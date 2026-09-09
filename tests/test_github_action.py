#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTION_YML = ROOT / "action.yml"
ENTRYPOINT = ROOT / "scripts/action_entrypoint.py"

VALID_BRANDING_COLORS = {
    "white", "yellow", "blue", "green", "orange", "red", "purple", "gray-dark"
}


class GitHubActionTests(unittest.TestCase):
    def test_action_yml_exists_and_conforms_to_marketplace_contract(self):
        self.assertTrue(ACTION_YML.is_file(), "action.yml must exist at repository root")
        text = ACTION_YML.read_text(encoding="utf-8")
        
        # Parse basic YAML structure
        self.assertIn("name:", text)
        self.assertIn("description:", text)
        self.assertIn("author:", text)
        self.assertIn("branding:", text)
        self.assertIn("icon:", text)
        self.assertIn("color:", text)
        self.assertIn("runs:", text)
        self.assertIn("using: 'composite'", text)
        self.assertIn("scripts/action_entrypoint.py", text)

        # Check required inputs
        for input_name in ("path:", "action:", "output-dir:", "fail-on-error:", "summary:"):
            self.assertIn(input_name, text)

        # Check required outputs
        for output_name in ("ok:", "architecture:", "skills-count:", "plugin-path:", "sha256:"):
            self.assertIn(output_name, text)

    def test_entrypoint_renders_markdown_summary_and_outputs(self):
        with tempfile.TemporaryDirectory(prefix="action-test-") as temp_dir:
            temp_path = Path(temp_dir)
            gh_output = temp_path / "github_output.txt"
            gh_summary = temp_path / "github_summary.md"

            # Create a mock agentic repository with a skill and AGENTS.md
            mock_repo = temp_path / "mock-repo"
            mock_repo.mkdir()
            (mock_repo / "AGENTS.md").write_text("# Test Agents\nInstructions here", encoding="utf-8")
            mock_skill = mock_repo / "skills/test-skill"
            mock_skill.mkdir(parents=True)
            (mock_skill / "SKILL.md").write_text("---\nname: test-skill\ndescription: A test skill\n---\nBody", encoding="utf-8")

            env = {
                **os.environ,
                "ACTION_PATH": str(ROOT),
                "GITHUB_OUTPUT": str(gh_output),
                "GITHUB_STEP_SUMMARY": str(gh_summary),
            }

            # Run action in analyze mode
            cmd = [
                "python3",
                str(ENTRYPOINT),
                "--path", str(mock_repo),
                "--action", "analyze",
                "--output-dir", str(temp_path / "dist"),
                "--fail-on-error", "true",
                "--summary", "true",
            ]
            proc = subprocess.run(cmd, env=env, text=True, capture_output=True, cwd=str(ROOT))
            self.assertEqual(proc.returncode, 0, f"STDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")

            # Verify GITHUB_OUTPUT was written
            self.assertTrue(gh_output.is_file(), "GITHUB_OUTPUT file must exist")
            output_content = gh_output.read_text(encoding="utf-8")
            self.assertIn("ok=true", output_content)
            self.assertIn("architecture=skills-only", output_content)
            self.assertIn("skills_count=", output_content)

            # Verify GITHUB_STEP_SUMMARY was written
            self.assertTrue(gh_summary.is_file(), "GITHUB_STEP_SUMMARY file must exist")
            summary_content = gh_summary.read_text(encoding="utf-8")
            self.assertIn("## ✅ ChatGPT / Codex Plugin Autopilot Summary", summary_content)
            self.assertIn("Discovered Workflow Candidates", summary_content)
            self.assertIn("skills-only", summary_content)

    def test_entrypoint_handles_missing_directory_gracefully(self):
        with tempfile.TemporaryDirectory(prefix="action-missing-") as temp_dir:
            temp_path = Path(temp_dir)
            gh_output = temp_path / "github_output.txt"
            non_existent = temp_path / "non_existent_folder"

            env = {
                **os.environ,
                "ACTION_PATH": str(ROOT),
                "GITHUB_OUTPUT": str(gh_output),
            }

            # With fail-on-error=false, should return 0
            cmd = [
                "python3",
                str(ENTRYPOINT),
                "--path", str(non_existent),
                "--fail-on-error", "false",
            ]
            proc = subprocess.run(cmd, env=env, text=True, capture_output=True, cwd=str(ROOT))
            self.assertEqual(proc.returncode, 0)
            self.assertIn("ok=false", gh_output.read_text(encoding="utf-8"))

            # With fail-on-error=true, should return 1
            cmd_fail = [
                "python3",
                str(ENTRYPOINT),
                "--path", str(non_existent),
                "--fail-on-error", "true",
            ]
            proc_fail = subprocess.run(cmd_fail, env=env, text=True, capture_output=True, cwd=str(ROOT))
            self.assertEqual(proc_fail.returncode, 1)

    def test_entrypoint_package_mode_creates_artifact_and_checksum(self):
        with tempfile.TemporaryDirectory(prefix="action-package-") as temp_dir:
            temp_path = Path(temp_dir)
            out_dir = temp_path / "dist"
            gh_output = temp_path / "github_output.txt"

            env = {
                **os.environ,
                "ACTION_PATH": str(ROOT),
                "GITHUB_OUTPUT": str(gh_output),
            }

            cmd = [
                "python3",
                str(ENTRYPOINT),
                "--path", str(ROOT),
                "--action", "package",
                "--output-dir", str(out_dir),
                "--fail-on-error", "true",
            ]
            proc = subprocess.run(cmd, env=env, text=True, capture_output=True, cwd=str(ROOT))
            self.assertEqual(proc.returncode, 0, f"STDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")

            # Verify packaged ZIP exists
            zips = list(out_dir.glob("*.zip"))
            self.assertEqual(len(zips), 1, f"Expected 1 zip, found {zips}")
            self.assertGreater(zips[0].stat().st_size, 1000)

            # Verify output variables
            output_content = gh_output.read_text(encoding="utf-8")
            self.assertIn("ok=true", output_content)
            self.assertIn("plugin_path=", output_content)
            self.assertIn("sha256=", output_content)


if __name__ == "__main__":
    unittest.main()

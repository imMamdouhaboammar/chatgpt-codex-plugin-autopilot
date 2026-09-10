#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
ACTION_YML = ROOT / "action.yml"
ENTRYPOINT = ROOT / "scripts/action_entrypoint.py"

VALID_BRANDING_COLORS = {
    "white", "yellow", "blue", "green", "orange", "red", "purple", "gray-dark"
}

# ---------------------------------------------------------------------------
# Import the module so we can unit-test helpers directly
# ---------------------------------------------------------------------------
sys.path.insert(0, str(ROOT / "scripts"))
import action_entrypoint as _ae  # noqa: E402


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
        for input_name in (
            "path:", "action:", "output-dir:", "fail-on-error:", "summary:",
            "create-pr:", "pr-title:", "pr-branch:"
        ):
            self.assertIn(input_name, text, f"Missing input: {input_name}")

        # Check required outputs
        for output_name in (
            "ok:", "architecture:", "skills-count:", "plugin-path:", "sha256:",
            "pr-url:", "pr-number:"
        ):
            self.assertIn(output_name, text, f"Missing output: {output_name}")

        # Verify GH_TOKEN is passed through
        self.assertIn("GH_TOKEN:", text)

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

            # Run action in analyze mode (without create-pr, so no git calls)
            cmd = [
                "python3",
                str(ENTRYPOINT),
                "--path", str(mock_repo),
                "--action", "analyze",
                "--output-dir", str(temp_path / "dist"),
                "--fail-on-error", "true",
                "--summary", "true",
                "--create-pr", "false",
            ]
            proc = subprocess.run(cmd, env=env, text=True, capture_output=True, cwd=str(ROOT))
            self.assertEqual(proc.returncode, 0, f"STDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")

            # Verify GITHUB_OUTPUT was written
            self.assertTrue(gh_output.is_file(), "GITHUB_OUTPUT file must exist")
            output_content = gh_output.read_text(encoding="utf-8")
            self.assertIn("ok=true", output_content)
            self.assertIn("architecture=skills-only", output_content)
            self.assertIn("skills_count=", output_content)
            # pr_url must NOT appear when create-pr is false
            self.assertNotIn("pr_url=", output_content)

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

    # -----------------------------------------------------------------------
    # Auto-PR unit tests
    # -----------------------------------------------------------------------

    def test_build_plugin_json_scaffold_from_analysis(self):
        """_build_plugin_json produces a valid schema-1.0 structure from analysis data."""
        with tempfile.TemporaryDirectory(prefix="build-pj-") as tmp:
            target = Path(tmp) / "my-cool-repo"
            target.mkdir()
            analysis = {
                "architecture": {"recommended": "mcp-backed", "reason": "has mcp config"},
                "candidates": [
                    {"slug": "analyze-skill", "kind": "skill"},
                    {"slug": "search-skill", "kind": "skill"},
                    {"slug": "analyze-skill", "kind": "skill"},  # duplicate — should be deduplicated
                ],
            }
            with patch.dict(os.environ, {"GITHUB_REPOSITORY": "testorg/my-cool-repo"}):
                result = _ae._build_plugin_json(target, analysis)

            self.assertEqual(result["schemaVersion"], "1.0")
            self.assertEqual(result["architecture"], "mcp-backed")
            self.assertIn("analyze-skill", result["skills"])
            self.assertIn("search-skill", result["skills"])
            self.assertEqual(len(result["skills"]), 2, "Duplicates must be removed")
            self.assertEqual(result["repository"], "https://github.com/testorg/my-cool-repo")
            self.assertEqual(result["_generatedBy"], "chatgpt-codex-plugin-autopilot")
            self.assertIn("assets", result)
            self.assertIn("logoLight", result["assets"])

    def test_scaffold_files_written_to_correct_paths(self):
        """create_pr_with_scaffold writes .codex-plugin/plugin.json and assets/ before git ops."""
        with tempfile.TemporaryDirectory(prefix="scaffold-files-") as tmp:
            target = Path(tmp) / "user-repo"
            target.mkdir()

            # Minimal git repo so git checkout works
            subprocess.run(["git", "init", "--initial-branch=main"], cwd=str(target),
                           capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(target),
                           capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=str(target),
                           capture_output=True)
            # Make an initial commit so HEAD exists
            (target / "README.md").write_text("# Test", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=str(target), capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=str(target), capture_output=True)

            analysis = {
                "architecture": {"recommended": "skills-only"},
                "candidates": [
                    {"slug": "my-skill", "kind": "skill", "recommendedTarget": "compile_skill", "path": "AGENTS.md", "reasons": ["agent instructions"]}
                ],
                "nextActions": [{"title": "Add plugin.json", "description": "Create the manifest"}],
            }

            # Patch git push and gh pr create to avoid real network calls
            def fake_push(*args, **kwargs):
                m = MagicMock()
                m.returncode = 0
                m.stdout = ""
                m.stderr = ""
                return m

            def fake_gh(*args, **kwargs):
                m = MagicMock()
                m.returncode = 0
                m.stdout = "https://github.com/testorg/user-repo/pull/42"
                m.stderr = ""
                return m

            original_run = subprocess.run

            def selective_mock(cmd_args, **kwargs):
                if isinstance(cmd_args, list) and cmd_args[0] == "git" and cmd_args[1] == "push":
                    return fake_push()
                if isinstance(cmd_args, list) and cmd_args[0] == "gh":
                    return fake_gh()
                return original_run(cmd_args, **kwargs)

            with patch("subprocess.run", side_effect=selective_mock):
                with patch.dict(os.environ, {"GITHUB_REPOSITORY": "testorg/user-repo"}):
                    pr_url, pr_number, scaffolded = _ae.create_pr_with_scaffold(
                        target, analysis, "skills-only", "🤖 Test PR Title"
                    )

            self.assertEqual(pr_url, "https://github.com/testorg/user-repo/pull/42")
            self.assertEqual(pr_number, "42")
            self.assertTrue((target / ".codex-plugin/plugin.json").is_file(),
                            "plugin.json must be scaffolded")
            self.assertTrue((target / "assets/logo-light.svg").is_file(),
                            "logo-light.svg must be scaffolded")
            self.assertTrue((target / "assets/logo-dark.svg").is_file())
            self.assertTrue((target / "assets/mark.svg").is_file())
            self.assertTrue((target / "submission/listing.json").is_file(),
                            "submission/listing.json must be scaffolded")
            self.assertTrue((target / ".github/workflows/codex-plugin.yml").is_file(),
                            "codex-plugin.yml CI workflow must be scaffolded")
            self.assertTrue((target / "skills/my-skill/SKILL.md").is_file(),
                            "candidate workflow skill must be scaffolded")

            plugin_json = json.loads((target / ".codex-plugin/plugin.json").read_text())
            self.assertEqual(plugin_json["schemaVersion"], "1.0")
            self.assertIn("my-skill", plugin_json["skills"])
            self.assertIn(".codex-plugin/plugin.json", scaffolded)
            self.assertIn("submission/listing.json", scaffolded)

    def test_create_pr_skipped_when_flag_is_false(self):
        """When create-pr=false, no git/gh subprocess is invoked."""
        with tempfile.TemporaryDirectory(prefix="no-pr-") as tmp:
            target = Path(tmp) / "repo"
            target.mkdir()
            gh_output = Path(tmp) / "out.txt"

            # Minimal git repo
            subprocess.run(["git", "init", "--initial-branch=main"], cwd=str(target),
                           capture_output=True)
            subprocess.run(["git", "config", "user.email", "x@x.com"], cwd=str(target),
                           capture_output=True)
            subprocess.run(["git", "config", "user.name", "X"], cwd=str(target),
                           capture_output=True)
            (target / "AGENTS.md").write_text("# Skills", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=str(target), capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=str(target), capture_output=True)

            env = {
                **os.environ,
                "ACTION_PATH": str(ROOT),
                "GITHUB_OUTPUT": str(gh_output),
                "INPUT_CREATE_PR": "false",
            }

            # Count gh/git invocations
            original_run = subprocess.run
            calls = []

            def tracking_run(cmd_args, **kwargs):
                if isinstance(cmd_args, list) and cmd_args[0] in ("gh",):
                    calls.append(cmd_args)
                return original_run(cmd_args, **kwargs)

            with patch("subprocess.run", side_effect=tracking_run):
                cmd = [
                    "python3", str(ENTRYPOINT),
                    "--path", str(target),
                    "--action", "analyze",
                    "--create-pr", "false",
                    "--summary", "false",
                ]
                proc = subprocess.run(cmd, env=env, text=True, capture_output=True, cwd=str(ROOT))

            # The outer subprocess.run is the entrypoint — gh must not be in its subprocesses
            self.assertEqual(proc.returncode, 0, proc.stderr)
            output_text = gh_output.read_text(encoding="utf-8") if gh_output.is_file() else ""
            self.assertNotIn("pr_url=", output_text)


if __name__ == "__main__":
    unittest.main()

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "skills" / "chatgpt-codex-plugin-autopilot" / "scripts" / "analyze_repo.py"


class RepoAnalyzerTests(unittest.TestCase):
    def run_analyzer(self, repo: Path) -> dict:
        proc = subprocess.run(
            ["python3", str(ANALYZER), str(repo), "--json"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        return json.loads(proc.stdout)

    def test_discovers_agentic_workflows_and_existing_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "README.md").write_text("# Example\n", encoding="utf-8")
            (repo / "AGENTS.md").write_text("Run the release review before shipping.\n", encoding="utf-8")
            (repo / "workflows").mkdir()
            (repo / "workflows/release-review.md").write_text(
                "# Release review\nVerify tests, inspect the diff, and publish only when green.\n",
                encoding="utf-8",
            )
            skill = repo / "skills/existing-review"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: existing-review\ndescription: Use when reviewing a release.\n---\n\nReview the release.\n",
                encoding="utf-8",
            )

            report = self.run_analyzer(repo)

            paths = {candidate["path"] for candidate in report["candidates"]}
            self.assertIn("skills/existing-review/SKILL.md", paths)
            self.assertIn("AGENTS.md", paths)
            self.assertIn("workflows/release-review.md", paths)
            self.assertEqual(report["architecture"]["recommended"], "skills-only")
            self.assertGreaterEqual(report["summary"]["candidateCount"], 3)
            self.assertIn("compile_workflows", report["nextActions"])
            self.assertIn("plan_host_workspace_capabilities", report["nextActions"])
            self.assertIn("install_host_workspace_skill", report["nextActions"])
            self.assertTrue(report["hostWorkspace"]["installRecommended"])
            self.assertEqual(report["hostWorkspace"]["skill"], "host-workspace-operator")
            self.assertEqual(
                report["hostWorkspace"]["capabilities"],
                ["read", "list", "search", "grep", "write", "patch", "shell", "python"],
            )

    def test_recommends_hybrid_when_skills_and_explicit_mcp_are_present(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            skill = repo / "skills/research"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: research\ndescription: Use when researching.\n---\n\nResearch.\n",
                encoding="utf-8",
            )
            (repo / ".mcp.json").write_text(
                json.dumps({"mcp_servers": {"search": {"command": "python3", "args": ["server.py"]}}}),
                encoding="utf-8",
            )
            (repo / "server.py").write_text("print('server')\n", encoding="utf-8")

            report = self.run_analyzer(repo)

            self.assertEqual(report["architecture"]["recommended"], "hybrid")
            self.assertIn("mcp", report["signals"])
            self.assertTrue(report["architecture"]["requiresHumanReview"])

    def test_existing_manifest_ignores_undeclared_root_mcp_for_active_architecture(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            skill = repo / "skills/research"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: research\ndescription: Use when researching.\n---\n\nResearch.\n",
                encoding="utf-8",
            )
            manifest_dir = repo / ".codex-plugin"
            manifest_dir.mkdir()
            (manifest_dir / "plugin.json").write_text(
                json.dumps({"name": "example", "version": "1.0.0", "skills": "./skills/"}),
                encoding="utf-8",
            )
            (repo / ".mcp.json").write_text(
                json.dumps({"mcp_servers": {"legacy": {"command": "python3", "args": ["server.py"]}}}),
                encoding="utf-8",
            )

            report = self.run_analyzer(repo)

            self.assertEqual(report["architecture"]["recommended"], "skills-only")
            self.assertNotIn("mcp", report["signals"])
            self.assertTrue(any("does not declare mcpServers" in item for item in report["warnings"]))

    def test_declared_apps_plus_skills_recommends_hybrid(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            skill = repo / "skills/research"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: research\ndescription: Use when researching.\n---\n\nResearch.\n",
                encoding="utf-8",
            )
            manifest_dir = repo / ".codex-plugin"
            manifest_dir.mkdir()
            (manifest_dir / "plugin.json").write_text(
                json.dumps({
                    "name": "example",
                    "version": "1.0.0",
                    "skills": "./skills/",
                    "apps": "./.app.json",
                }),
                encoding="utf-8",
            )
            (repo / ".app.json").write_text(
                json.dumps({"apps": {"work": {"id": "plugin_asdk_app_example"}}}),
                encoding="utf-8",
            )

            report = self.run_analyzer(repo)

            self.assertEqual(report["architecture"]["recommended"], "hybrid")
            self.assertIn("apps", report["signals"])
            self.assertTrue(report["architecture"]["requiresHumanReview"])

    def test_ignored_dependency_trees_do_not_enter_inventory_or_candidates(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "AGENTS.md").write_text("Review releases.\n", encoding="utf-8")
            ignored = repo / "node_modules" / "package" / "workflows"
            ignored.mkdir(parents=True)
            for index in range(30):
                (ignored / f"workflow-{index}.md").write_text("Ignore me.\n", encoding="utf-8")

            report = self.run_analyzer(repo)

            self.assertEqual(report["summary"]["fileCount"], 1)
            self.assertEqual({item["path"] for item in report["candidates"]}, {"AGENTS.md"})

    def test_output_is_deterministic_for_same_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "README.md").write_text("# Deterministic\n", encoding="utf-8")
            (repo / "commands").mkdir()
            (repo / "commands/audit.md").write_text("Audit the repository.\n", encoding="utf-8")

            first = self.run_analyzer(repo)
            second = self.run_analyzer(repo)

            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

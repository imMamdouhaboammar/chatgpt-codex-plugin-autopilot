import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "host-workspace-operator"
INSTALLER = ROOT / "skills" / "chatgpt-codex-plugin-autopilot" / "scripts" / "install_host_workspace_skill.py"


class HostWorkspaceSkillTests(unittest.TestCase):
    def test_host_workspace_skill_covers_read_search_and_mutation_tools(self):
        skill_file = SKILL / "SKILL.md"
        agent_file = SKILL / "agents" / "openai.yaml"
        self.assertTrue(skill_file.is_file())
        self.assertTrue(agent_file.is_file())
        text = skill_file.read_text(encoding="utf-8").lower()
        for phrase in (
            "read",
            "list",
            "search",
            "grep",
            "write",
            "patch",
            "shell",
            "python",
            "read-only",
            "mutation",
            "tool is unavailable",
        ):
            self.assertIn(phrase, text)

    def test_installer_adds_workspace_skill_to_target_plugin(self):
        with tempfile.TemporaryDirectory() as temp:
            plugin = Path(temp) / "plugin"
            (plugin / "skills").mkdir(parents=True)

            proc = subprocess.run(
                ["python3", str(INSTALLER), str(plugin)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
            installed = plugin / "skills" / "host-workspace-operator"
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "agents" / "openai.yaml").is_file())

    def test_installer_is_idempotent_and_refuses_custom_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            plugin = Path(temp) / "plugin"
            (plugin / "skills").mkdir(parents=True)

            first = subprocess.run(
                ["python3", str(INSTALLER), str(plugin)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(first.returncode, 0, first.stderr or first.stdout)

            second = subprocess.run(
                ["python3", str(INSTALLER), str(plugin)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            self.assertIn("already current", second.stdout.lower())

            skill_file = plugin / "skills" / "host-workspace-operator" / "SKILL.md"
            skill_file.write_text("custom local skill\n", encoding="utf-8")
            third = subprocess.run(
                ["python3", str(INSTALLER), str(plugin)],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(third.returncode, 0)
            self.assertIn("refusing to overwrite", (third.stderr + third.stdout).lower())


if __name__ == "__main__":
    unittest.main()

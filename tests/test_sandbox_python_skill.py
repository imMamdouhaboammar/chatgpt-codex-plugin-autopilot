import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "sandbox-python-executor"
MAIN_SKILL = ROOT / "skills" / "chatgpt-codex-plugin-autopilot" / "SKILL.md"
MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
REVIEWER_PACKET = ROOT / "submission" / "reviewer-packet.json"


class SandboxPythonSkillTests(unittest.TestCase):
    def test_plugin_version_and_capability_include_sandbox_python(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "0.5.0")
        self.assertIn("Sandbox Python execution", manifest["interface"]["capabilities"])

    def test_sandbox_python_skill_is_packaged_and_discoverable(self):
        skill_file = SKILL / "SKILL.md"
        agent_file = SKILL / "agents" / "openai.yaml"
        self.assertTrue(skill_file.is_file())
        self.assertTrue(agent_file.is_file())

        text = skill_file.read_text(encoding="utf-8")
        normalized = text.lower()
        self.assertRegex(text, r"(?m)^name:\s*sandbox-python-executor$")
        description = re.search(r"(?m)^description:\s*(.+)$", text)
        self.assertIsNotNone(description)
        self.assertTrue(description.group(1).startswith("Use when "))

        for phrase in (
            "python tool",
            "sandbox",
            "execution evidence",
            "do not claim",
            "tool is unavailable",
        ):
            self.assertIn(phrase, normalized)

    def test_skill_metadata_targets_chat_and_codex_without_fake_tool_dependency(self):
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("products:", text)
        self.assertIn("CHAT", text)
        self.assertIn("CODEX", text)
        self.assertIn("allow_implicit_invocation: true", text)
        self.assertNotIn("dependencies:", text)
        self.assertNotRegex(text, r"(?i)code[_ -]?interpreter.*type:")

    def test_main_autopilot_routes_real_execution_to_sandbox_skill(self):
        text = MAIN_SKILL.read_text(encoding="utf-8").lower()
        for phrase in (
            "sandbox-python-executor",
            "host-native python",
            "execute the checks",
            "do not merely print commands",
        ):
            self.assertIn(phrase, text)

    def test_reviewer_packet_covers_success_and_unavailable_tool_behavior(self):
        packet = json.loads(REVIEWER_PACKET.read_text(encoding="utf-8"))
        skill_names = {item["name"] for item in packet["skills"]}
        self.assertIn("sandbox-python-executor", skill_names)

        positive = "\n".join(case["expectedBehavior"] for case in packet["positiveTests"])
        negative = "\n".join(case["expectedBehavior"] for case in packet["negativeTests"])
        self.assertIn("python tool", positive.lower())
        self.assertIn("unavailable", negative.lower())
        self.assertIn("do not claim", negative.lower())


if __name__ == "__main__":
    unittest.main()

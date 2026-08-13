import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".codex-plugin" / "plugin.json"


class PluginContractTests(unittest.TestCase):
    def test_manifest_declares_standalone_skill_only_plugin(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "chatgpt-codex-plugin-autopilot")
        self.assertEqual(data["version"], "0.2.0")
        self.assertEqual(data["skills"], "./skills/")
        self.assertNotIn("mcpServers", data)
        self.assertNotIn("apps", data)
        self.assertNotIn("hooks", data)

    def test_manifest_uses_final_directory_safe_identity(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        interface = data["interface"]
        self.assertLessEqual(len(interface["displayName"]), 30)
        self.assertLessEqual(len(interface["shortDescription"]), 30)
        self.assertLessEqual(len(interface["developerName"]), 80)
        self.assertEqual(interface["category"], "Developer Tools")
        self.assertIn("Submission preflight", interface["capabilities"])
        for key in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL", "supportURL"):
            self.assertTrue(interface[key].startswith("https://"), key)

    def test_manifest_declares_required_square_branding_assets(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        interface = data["interface"]
        for key in ("logo", "composerIcon"):
            value = interface[key]
            self.assertTrue(value.startswith("./"), key)
            self.assertTrue((ROOT / value[2:]).is_file(), value)

    def test_codex_plugin_directory_contains_manifest_only(self):
        entries = sorted(path.name for path in (ROOT / ".codex-plugin").iterdir())
        self.assertEqual(entries, ["plugin.json"])

    def test_skills_root_contains_directories_only(self):
        entries = list((ROOT / "skills").iterdir())
        self.assertTrue(entries)
        for entry in entries:
            self.assertTrue(entry.is_dir(), entry.name)
            self.assertTrue((entry / "SKILL.md").is_file(), entry.name)

    def test_required_public_files_exist(self):
        for rel in ("README.md", "PRIVACY.md", "TERMS.md", "SUPPORT.md", "LICENSE", "assets/mark.svg"):
            self.assertTrue((ROOT / rel).is_file(), rel)


if __name__ == "__main__":
    unittest.main()

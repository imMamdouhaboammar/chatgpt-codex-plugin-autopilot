import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
REVIEWER_PACKET = ROOT / "submission" / "reviewer-packet.json"


class PluginContractTests(unittest.TestCase):
    def test_manifest_declares_standalone_skill_only_plugin(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "chatgpt-codex-plugin-autopilot")
        self.assertEqual(data["version"], "0.3.0")
        self.assertEqual(data["skills"], "./skills/")
        self.assertNotIn("mcpServers", data)
        self.assertNotIn("apps", data)
        self.assertNotIn("hooks", data)

    def test_manifest_uses_documented_install_surface_fields(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        interface = data["interface"]
        self.assertLessEqual(len(interface["displayName"]), 30)
        self.assertLessEqual(len(interface["shortDescription"]), 30)
        self.assertLessEqual(len(interface["developerName"]), 80)
        self.assertEqual(interface["category"], "Developer Tools")
        self.assertIn("Submission preflight", interface["capabilities"])
        for key in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
            self.assertTrue(interface[key].startswith("https://"), key)
        self.assertNotIn("supportURL", interface)

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

    def test_repo_marketplace_points_to_plugin_root(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        self.assertEqual(marketplace["interface"]["displayName"], "Plugin Autopilot")
        self.assertEqual(len(marketplace["plugins"]), 1)
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], manifest["name"])
        self.assertEqual(entry["source"], {"source": "local", "path": "./"})
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")
        self.assertEqual(entry["category"], manifest["interface"]["category"])

    def test_reviewer_packet_matches_manifest_and_required_test_counts(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        packet = json.loads(REVIEWER_PACKET.read_text(encoding="utf-8"))
        plugin = packet["plugin"]
        self.assertEqual(plugin["name"], manifest["name"])
        self.assertEqual(plugin["version"], manifest["version"])
        self.assertEqual(plugin["architecture"], "skills-only")
        self.assertEqual(plugin["displayName"], manifest["interface"]["displayName"])
        self.assertEqual(plugin["developerName"], manifest["interface"]["developerName"])
        self.assertEqual(plugin["category"], manifest["interface"]["category"])
        self.assertEqual(plugin["shortDescription"], manifest["interface"]["shortDescription"])
        self.assertEqual(plugin["longDescription"], manifest["interface"]["longDescription"])
        self.assertEqual(packet["starterPrompts"], manifest["interface"]["defaultPrompt"])
        self.assertTrue(plugin["supportURL"].startswith("https://"))
        self.assertEqual(len(packet["positiveTests"]), 5)
        self.assertEqual(len(packet["negativeTests"]), 3)
        for case in packet["positiveTests"]:
            self.assertTrue(case["userPrompt"])
            self.assertTrue(case["expectedBehavior"])
            self.assertTrue(case["expectedResultShape"])
            self.assertTrue(case["fixtureData"])
        for case in packet["negativeTests"]:
            self.assertTrue(case["userPrompt"])
            self.assertTrue(case["expectedBehavior"])
            self.assertTrue(case["reason"])

    def test_required_public_and_distribution_files_exist(self):
        for rel in (
            "README.md",
            "PRIVACY.md",
            "TERMS.md",
            "SUPPORT.md",
            "LICENSE",
            "assets/mark.svg",
            ".agents/plugins/marketplace.json",
            "submission/reviewer-packet.json",
        ):
            self.assertTrue((ROOT / rel).is_file(), rel)


if __name__ == "__main__":
    unittest.main()

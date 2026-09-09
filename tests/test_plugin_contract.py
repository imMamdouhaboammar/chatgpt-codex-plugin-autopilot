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
        # Version is managed in plugin.json and validated by tag-parity in CI.
        # Do not hardcode version strings in tests.
        self.assertRegex(data["version"], r"^\d+\.\d+\.\d+$")
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
        for capability in (
            "Workflow-to-Skill conversion",
            "Host workspace read/search/edit",
            "Sandbox Python execution",
            "SVG brand identity pack",
            "Plugin Directory listing pack",
            "Submission preflight",
        ):
            self.assertIn(capability, interface["capabilities"])
        for key in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
            self.assertTrue(interface[key].startswith("https://"), key)
        self.assertNotIn("supportURL", interface)
        for forbidden in ("grep", "write", "shell", "code_interpreter"):
            self.assertNotIn(forbidden, data)

    def test_manifest_declares_required_square_branding_assets(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        interface = data["interface"]
        for key in ("logo", "composerIcon"):
            value = interface[key]
            self.assertTrue(value.startswith("./"), key)
            self.assertTrue((ROOT / value[2:]).is_file(), value)
        self.assertEqual(interface["logo"], "./assets/logo-light.svg")
        self.assertTrue((ROOT / "assets/logo-dark.svg").is_file())

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
        self.assertGreaterEqual(len(packet["positiveTests"]), 5)
        self.assertGreaterEqual(len(packet["negativeTests"]), 3)
        self.assertEqual(
            packet["hostCapabilities"]["workspace"],
            ["read", "list", "search", "grep", "write", "patch", "shell", "python"],
        )
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
            "SECURITY.md",
            "LICENSE",
            "assets/mark.svg",
            "assets/logo-light.svg",
            "assets/logo-dark.svg",
            ".agents/plugins/marketplace.json",
            "submission/reviewer-packet.json",
            "submission/listing.json",
            "skills/host-workspace-operator/SKILL.md",
            "skills/sandbox-python-executor/SKILL.md",
        ):
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_security_policy_contract_and_support_routing(self):
        security_text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        support_text = (ROOT / "SUPPORT.md").read_text(encoding="utf-8")
        self.assertIn("security/advisories/new", security_text)
        self.assertIn("Do not disclose suspected security vulnerabilities or sensitive evidence in public", security_text)
        self.assertIn("Fail-Closed Fallback Route", security_text)
        self.assertIn("Trust Boundaries", security_text)
        self.assertIn("SECURITY.md", support_text)
        self.assertIn("Security Vulnerabilities", support_text)

    def test_conformance_matrix_and_drift_control_reference(self):
        matrix_path = (
            ROOT
            / "skills"
            / "chatgpt-codex-plugin-autopilot"
            / "references"
            / "conformance-matrix.md"
        )
        self.assertTrue(matrix_path.is_file())
        text = matrix_path.read_text(encoding="utf-8")
        self.assertIn("Authoritative Review Date", text)
        self.assertIn("archive_member_path_too_long", text)
        self.assertIn("dependencies.tools", text)
        self.assertIn("duplicate_app_reference", text)
        self.assertIn("mcpServers", text)
        self.assertIn("Local Proof", text)
        self.assertIn("Strategy A", text)

    def test_contributing_and_product_boundaries(self):
        contrib_path = ROOT / "CONTRIBUTING.md"
        self.assertTrue(contrib_path.is_file())
        text = contrib_path.read_text(encoding="utf-8")
        self.assertIn("Primary Product", text)
        self.assertIn("Secondary Subtrees", text)
        self.assertIn("plugins/no-ai-slop", text)
        self.assertIn("Local Verification Commands", text)
        self.assertIn(".github/workflows/release.yml", text)

        slop_readme = (ROOT / "plugins/no-ai-slop/README.md").read_text(encoding="utf-8")
        self.assertIn("Canonical ID & Marketplace Namespace Advisory", slop_readme)


if __name__ == "__main__":
    unittest.main()

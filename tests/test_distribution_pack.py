import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
AUTOPILOT = SKILLS / "chatgpt-codex-plugin-autopilot"
PACKER = AUTOPILOT / "scripts" / "build_directory_pack.py"


class DistributionPackTests(unittest.TestCase):
    def test_branding_and_listing_skills_exist(self):
        for slug in ("plugin-brand-identity-designer", "plugin-directory-listing-writer"):
            path = SKILLS / slug / "SKILL.md"
            self.assertTrue(path.is_file(), slug)
            text = path.read_text(encoding="utf-8")
            self.assertIn(f"name: {slug}", text)
            self.assertIn("Use when ", text)

    def test_autopilot_ships_light_and_dark_svg_logo_variants(self):
        for rel in ("assets/logo-light.svg", "assets/logo-dark.svg"):
            path = ROOT / rel
            self.assertTrue(path.is_file(), rel)
            text = path.read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            self.assertRegex(text, r'viewBox="0 0 [0-9]+ [0-9]+"')

    def test_directory_pack_extracts_portal_facing_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".codex-plugin").mkdir()
            (root / "assets").mkdir()
            (root / "assets/logo-light.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/logo-dark.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/icon.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            manifest = {
                "name": "example-plugin",
                "version": "1.2.3",
                "description": "Example package",
                "repository": "https://github.com/example/example-plugin",
                "interface": {
                    "displayName": "Example Plugin",
                    "shortDescription": "Review releases faster",
                    "longDescription": "Review release evidence and prepare a clear decision.",
                    "developerName": "Example Studio",
                    "category": "Developer Tools",
                    "capabilities": ["Release review", "Evidence checks"],
                    "websiteURL": "https://example.com",
                    "supportURL": "https://example.com/support",
                    "privacyPolicyURL": "https://example.com/privacy",
                    "termsOfServiceURL": "https://example.com/terms",
                    "defaultPrompt": ["Review this release before I publish it."],
                    "logo": "./assets/logo-light.svg",
                    "composerIcon": "./assets/icon.svg",
                },
            }
            (root / ".codex-plugin/plugin.json").write_text(json.dumps(manifest), encoding="utf-8")

            proc = subprocess.run(
                ["python3", str(PACKER), str(root), "--json"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
            report = json.loads(proc.stdout)

            self.assertTrue(report["ok"])
            self.assertEqual(report["listing"]["name"], "Example Plugin")
            self.assertEqual(report["listing"]["subtitle"], "Review releases faster")
            self.assertEqual(report["listing"]["packageName"], "example-plugin")
            self.assertEqual(report["listing"]["version"], "1.2.3")
            self.assertEqual(report["listing"]["customerSupportURL"], "https://example.com/support")
            self.assertEqual(report["branding"]["lightLogo"], "./assets/logo-light.svg")
            self.assertEqual(report["branding"]["darkLogo"], "./assets/logo-dark.svg")
            self.assertEqual(report["readiness"]["missing"], [])


if __name__ == "__main__":
    unittest.main()

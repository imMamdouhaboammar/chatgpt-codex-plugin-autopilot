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
            self.assertEqual(report["readiness"]["status"], "listing_ready")

    def test_skills_only_omitted_urls_passes_listing_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".codex-plugin").mkdir()
            (root / "assets").mkdir()
            (root / "assets/logo-light.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/logo-dark.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/icon.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            manifest = {
                "name": "skills-plugin",
                "version": "1.0.0",
                "description": "Skills-only package without URLs",
                "interface": {
                    "displayName": "Skills Plugin",
                    "shortDescription": "Quick skills workflow",
                    "longDescription": "A pure skills plugin with no remote apps or MCP servers.",
                    "developerName": "Studio",
                    "category": "Productivity",
                    "capabilities": ["Automation"],
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
            self.assertEqual(report["targetArchitecture"], "skills")
            self.assertEqual(report["readiness"]["missing"], [])
            self.assertEqual(report["readiness"]["errors"], [])
            self.assertEqual(report["readiness"]["status"], "listing_ready")

    def test_mcp_backed_requires_mandatory_urls(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".codex-plugin").mkdir()
            (root / "assets").mkdir()
            (root / "assets/logo-light.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/logo-dark.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/icon.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            manifest = {
                "name": "mcp-plugin",
                "version": "1.0.0",
                "description": "MCP package missing required URLs",
                "mcpServers": "./.mcp.json",
                "interface": {
                    "displayName": "MCP Plugin",
                    "shortDescription": "MCP workflow",
                    "longDescription": "An MCP plugin requiring public URLs for directory submission.",
                    "developerName": "Studio",
                    "category": "Developer Tools",
                    "capabilities": ["Tools"],
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
            self.assertNotEqual(proc.returncode, 0)
            report = json.loads(proc.stdout)
            self.assertFalse(report["ok"])
            self.assertEqual(report["targetArchitecture"], "mcp")
            self.assertEqual(report["readiness"]["status"], "not_ready")
            missing = report["readiness"]["missing"]
            for url_field in ("websiteURL", "customerSupportURL", "privacyPolicyURL", "termsOfServiceURL"):
                self.assertIn(url_field, missing)

    def test_starter_prompt_constraints_and_overrides(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".codex-plugin").mkdir()
            (root / "assets").mkdir()
            (root / "assets/logo-light.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/logo-dark.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/icon.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            manifest = {
                "name": "prompt-plugin",
                "version": "1.0.0",
                "description": "Testing prompt constraints",
                "interface": {
                    "displayName": "Prompt Plugin",
                    "shortDescription": "Prompts",
                    "longDescription": "Testing starter prompts constraints in directory listing pack.",
                    "developerName": "Studio",
                    "category": "Productivity",
                    "capabilities": ["Prompts"],
                    "logo": "./assets/logo-light.svg",
                    "composerIcon": "./assets/icon.svg",
                },
            }
            (root / ".codex-plugin/plugin.json").write_text(json.dumps(manifest), encoding="utf-8")

            # 1. >3 starter prompts fails
            override_path = root / "listing_override.json"
            override_path.write_text(
                json.dumps({"starterPrompts": ["P1", "P2", "P3", "P4"]}),
                encoding="utf-8",
            )
            proc = subprocess.run(["python3", str(PACKER), str(root), "--listing", str(override_path), "--json"], text=True, capture_output=True)
            report = json.loads(proc.stdout)
            self.assertFalse(report["ok"])
            self.assertTrue(any("at most 3 prompts" in err for err in report["readiness"]["errors"]))

            # 2. Overlong prompt (>128 chars) fails
            override_path.write_text(
                json.dumps({"starterPrompts": ["A" * 129]}),
                encoding="utf-8",
            )
            proc = subprocess.run(["python3", str(PACKER), str(root), "--listing", str(override_path), "--json"], text=True, capture_output=True)
            report = json.loads(proc.stdout)
            self.assertFalse(report["ok"])
            self.assertTrue(any("exceeds 128 characters" in err for err in report["readiness"]["errors"]))

            # 3. Newline in prompt fails
            override_path.write_text(
                json.dumps({"starterPrompts": ["Line 1\nLine 2"]}),
                encoding="utf-8",
            )
            proc = subprocess.run(["python3", str(PACKER), str(root), "--listing", str(override_path), "--json"], text=True, capture_output=True)
            report = json.loads(proc.stdout)
            self.assertFalse(report["ok"])
            self.assertTrue(any("must fit on one line" in err for err in report["readiness"]["errors"]))

            # 4. App @mention fails
            override_path.write_text(
                json.dumps({"starterPrompts": ["Ask @my_app to do something"]}),
                encoding="utf-8",
            )
            proc = subprocess.run(["python3", str(PACKER), str(root), "--listing", str(override_path), "--json"], text=True, capture_output=True)
            report = json.loads(proc.stdout)
            self.assertFalse(report["ok"])
            self.assertTrue(any("app @mention" in err for err in report["readiness"]["errors"]))

            # 5. Normalized duplicate prompts fail
            override_path.write_text(
                json.dumps({"starterPrompts": ["Test Prompt", "test   prompt"]}),
                encoding="utf-8",
            )
            proc = subprocess.run(["python3", str(PACKER), str(root), "--listing", str(override_path), "--json"], text=True, capture_output=True)
            report = json.loads(proc.stdout)
            self.assertFalse(report["ok"])
            self.assertTrue(any("unique after normalization" in err for err in report["readiness"]["errors"]))

    def test_invalid_credential_bearing_and_unsupported_urls(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".codex-plugin").mkdir()
            (root / "assets").mkdir()
            (root / "assets/logo-light.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/logo-dark.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/icon.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            manifest = {
                "name": "url-plugin",
                "version": "1.0.0",
                "description": "Testing URL validation",
                "interface": {
                    "displayName": "URL Plugin",
                    "shortDescription": "URLs",
                    "longDescription": "Testing URL validation rules in build_directory_pack.",
                    "developerName": "Studio",
                    "category": "Productivity",
                    "capabilities": ["Web"],
                    "logo": "./assets/logo-light.svg",
                    "composerIcon": "./assets/icon.svg",
                },
            }
            (root / ".codex-plugin/plugin.json").write_text(json.dumps(manifest), encoding="utf-8")

            # 1. Credential-bearing URL
            override_path = root / "listing_override.json"
            override_path.write_text(
                json.dumps({"websiteURL": "https://admin:secret@example.com"}),
                encoding="utf-8",
            )
            proc = subprocess.run(["python3", str(PACKER), str(root), "--listing", str(override_path), "--json"], text=True, capture_output=True)
            report = json.loads(proc.stdout)
            self.assertFalse(report["ok"])
            self.assertTrue(any("embedded credentials" in err for err in report["readiness"]["errors"]))

            # 2. Non-HTTPS URL
            override_path.write_text(
                json.dumps({"websiteURL": "http://example.com"}),
                encoding="utf-8",
            )
            proc = subprocess.run(["python3", str(PACKER), str(root), "--listing", str(override_path), "--json"], text=True, capture_output=True)
            report = json.loads(proc.stdout)
            self.assertFalse(report["ok"])
            self.assertTrue(any("public HTTPS URL" in err for err in report["readiness"]["errors"]))

            # 3. Overlong URL (>1024 chars)
            override_path.write_text(
                json.dumps({"websiteURL": "https://example.com/" + ("x" * 1020)}),
                encoding="utf-8",
            )
            proc = subprocess.run(["python3", str(PACKER), str(root), "--listing", str(override_path), "--json"], text=True, capture_output=True)
            report = json.loads(proc.stdout)
            self.assertFalse(report["ok"])
            self.assertTrue(any("exceeds final directory limit of 1024 characters" in err for err in report["readiness"]["errors"]))

    def test_metadata_limits_and_overrides(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".codex-plugin").mkdir()
            (root / "assets").mkdir()
            (root / "assets/logo-light.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/logo-dark.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            (root / "assets/icon.svg").write_text('<svg viewBox="0 0 64 64"></svg>', encoding="utf-8")
            manifest = {
                "name": "meta-plugin",
                "version": "1.0.0",
                "description": "Testing metadata limits",
                "interface": {
                    "displayName": "Meta Plugin",
                    "shortDescription": "Meta",
                    "longDescription": "Testing metadata limits and override validation.",
                    "developerName": "Studio",
                    "category": "Productivity",
                    "capabilities": ["Automation"],
                    "logo": "./assets/logo-light.svg",
                    "composerIcon": "./assets/icon.svg",
                },
            }
            (root / ".codex-plugin/plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
            override_path = root / "listing_override.json"

            cases = [
                ({"name": "A" * 31}, "name exceeds 30 characters"),
                ({"name": "Line 1\nLine 2"}, "name must fit on one line"),
                ({"subtitle": "S" * 31}, "subtitle exceeds 30 characters"),
                ({"subtitle": "Sub\nTitle"}, "subtitle must fit on one line"),
                ({"developerName": "D" * 81}, "developerName exceeds 80 characters"),
                ({"developerName": "Dev\nName"}, "developerName must fit on one line"),
                ({"category": "UnsupportedCategory"}, "category is unsupported"),
                ({"packageName": "invalid package name!"}, "packageName must be"),
                ({"version": "v1.0"}, "version must be strict semver"),
                ({"capabilities": ["Cap"] * 21}, "capabilities exceeds 20 items"),
                ({"capabilities": ["C" * 121]}, "exceeds 120 characters"),
                ({"capabilities": ["Multi\nLine"]}, "must fit on one line"),
            ]

            for override_data, expected_err in cases:
                override_path.write_text(json.dumps(override_data), encoding="utf-8")
                proc = subprocess.run(
                    ["python3", str(PACKER), str(root), "--listing", str(override_path), "--json"],
                    text=True,
                    capture_output=True,
                )
                report = json.loads(proc.stdout)
                self.assertFalse(report["ok"], f"Expected failure for {override_data}")
                self.assertTrue(
                    any(expected_err in err for err in report["readiness"]["errors"]),
                    f"Expected '{expected_err}' in errors for {override_data}, got {report['readiness']['errors']}",
                )


if __name__ == "__main__":
    unittest.main()


import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "skills/chatgpt-codex-plugin-autopilot/scripts/validate_plugin.py"


def square_svg() -> str:
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64"/></svg>\n'


def base_manifest() -> dict:
    return {
        "name": "fixture-plugin",
        "version": "1.0.0",
        "description": "Fixture plugin for Skill frontmatter tests.",
        "author": {"name": "Test Publisher", "url": "https://example.com"},
        "skills": "./skills/",
        "interface": {
            "displayName": "Fixture",
            "shortDescription": "Fixture plugin",
            "longDescription": "Fixture used by Plugin Autopilot regression tests.",
            "developerName": "Test Publisher",
            "category": "Developer Tools",
            "logo": "./assets/icon.svg",
            "composerIcon": "./assets/icon.svg",
            "websiteURL": "https://example.com",
            "privacyPolicyURL": "https://example.com/privacy",
            "termsOfServiceURL": "https://example.com/terms",
            "supportURL": "https://example.com/support",
        },
    }


def write_fixture(root: Path, frontmatter: str) -> None:
    (root / ".codex-plugin").mkdir(parents=True)
    (root / "assets").mkdir()
    (root / "skills" / "worker").mkdir(parents=True)
    (root / ".codex-plugin" / "plugin.json").write_text(json.dumps(base_manifest()), encoding="utf-8")
    (root / "assets" / "icon.svg").write_text(square_svg(), encoding="utf-8")
    (root / "skills" / "worker" / "SKILL.md").write_text(
        f"---\n{frontmatter}\n---\n\nValidate the fixture.\n",
        encoding="utf-8",
    )


def validate(root: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    proc = subprocess.run(
        ["python3", str(VALIDATOR), str(root), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return proc, json.loads(proc.stdout)


class SkillFrontmatterYamlTests(unittest.TestCase):
    def test_rejects_malformed_yaml_that_regex_metadata_would_accept(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(
                root,
                "name: worker\n"
                "description: Use when validating malformed frontmatter.\n"
                "metadata: [unterminated",
            )

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            self.assertFalse(report["ok"], report)
            self.assertTrue(
                any("frontmatter" in error.lower() and "malformed" in error.lower() for error in report["errors"]),
                report,
            )

    def test_rejects_non_mapping_top_level_frontmatter(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root, "- worker\n- metadata")

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(
                any("frontmatter" in error.lower() and "mapping" in error.lower() for error in report["errors"]),
                report,
            )

    def test_rejects_non_string_name_and_description(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root, "name: [worker]\ndescription: 123")

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            joined = "\n".join(report["errors"]).lower()
            self.assertIn("skill name", joined)
            self.assertIn("string", joined)
            self.assertIn("skill description", joined)
            self.assertIn("string", joined)

    def test_accepts_quoted_scalars_with_colons_hashes_and_unicode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(
                root,
                'name: "quoted-worker"\n'
                'description: "Use when metadata includes: colons, # marks, and Unicode ✓."',
            )

            proc, report = validate(root)

            self.assertEqual(proc.returncode, 0, report)
            self.assertEqual(report["skills"], ["quoted-worker"])

    def test_accepts_block_scalar_description(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(
                root,
                "name: multiline-worker\n"
                "description: >-\n"
                "  Use when validating multiline\n"
                "  Skill metadata safely.",
            )

            proc, report = validate(root)

            self.assertEqual(proc.returncode, 0, report)
            self.assertEqual(report["skills"], ["multiline-worker"])

    def test_rejects_leading_comma_in_flow_collections(self):
        cases = (
            "metadata: [ , extra]",
            "metadata: {, extra: 1}",
        )
        for extra in cases:
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "plugin"
                write_fixture(
                    root,
                    "name: worker\n"
                    "description: Use when validating malformed flow collections.\n"
                    f"{extra}",
                )

                proc, report = validate(root)

                self.assertNotEqual(proc.returncode, 0, report)
                self.assertTrue(
                    any("frontmatter" in error.lower() and "malformed" in error.lower() for error in report["errors"]),
                    report,
                )

    def test_rejects_explicit_yaml_tags(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(
                root,
                "name: worker\n"
                "description: !!python/object/apply:os.system ['echo unsafe']",
            )

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(any("frontmatter" in error.lower() for error in report["errors"]), report)
            self.assertNotIn("unsafe", json.dumps(report))

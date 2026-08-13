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
        "description": "Fixture plugin for validator tests.",
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


def write_fixture(root: Path, *, skill_dir: str = "worker", skill_name: str = "worker") -> None:
    (root / ".codex-plugin").mkdir(parents=True)
    (root / "assets").mkdir()
    (root / "skills" / skill_dir).mkdir(parents=True)
    (root / ".codex-plugin" / "plugin.json").write_text(json.dumps(base_manifest()), encoding="utf-8")
    (root / "assets" / "icon.svg").write_text(square_svg(), encoding="utf-8")
    (root / "skills" / skill_dir / "SKILL.md").write_text(
        f"---\nname: {skill_name}\ndescription: Use when validating fixture behavior.\n---\n\nValidate the fixture.\n",
        encoding="utf-8",
    )


def validate(root: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    proc = subprocess.run(
        ["python3", str(VALIDATOR), str(root), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    report = json.loads(proc.stdout)
    return proc, report


class ValidatorRegressionTests(unittest.TestCase):
    def test_rejects_files_directly_under_skills_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            (root / "skills" / "registry.json").write_text("{}\n", encoding="utf-8")
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(any("direct" in error.lower() and "skills" in error.lower() for error in report["errors"]), report)

    def test_rejects_extra_content_inside_codex_plugin_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            (root / ".codex-plugin" / "notes.txt").write_text("not part of the manifest directory\n", encoding="utf-8")
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(any(".codex-plugin" in error and "plugin.json" in error for error in report["errors"]), report)

    def test_undeclared_mcp_file_is_ignored_for_architecture(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            (root / ".mcp.json").write_text(
                json.dumps({"mcp_servers": {"demo": {"url": "https://example.com/mcp"}}}), encoding="utf-8"
            )
            proc, report = validate(root)
            self.assertEqual(proc.returncode, 0, report)
            self.assertEqual(report["architecture"], "skills-only")
            self.assertTrue(any(".mcp.json" in warning and "ignored" in warning.lower() for warning in report["warnings"]), report)

    def test_skill_metadata_name_does_not_have_to_match_directory_name(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root, skill_dir="worker", skill_name="focused-review")
            proc, report = validate(root)
            self.assertEqual(proc.returncode, 0, report)
            self.assertEqual(report["skills"], ["focused-review"])

    def test_rejects_asset_path_with_parent_traversal_segment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["interface"]["logo"] = "./assets/../assets/icon.svg"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(any("traversal" in error.lower() or ".." in error for error in report["errors"]), report)

    def test_rejects_invalid_openai_agent_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            agents = root / "skills" / "worker" / "agents"
            agents.mkdir()
            (agents / "openai.yaml").write_text("policy:\n  allow_implicit_invocation: sometimes\n", encoding="utf-8")
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(any("agents/openai.yaml" in error for error in report["errors"]), report)

    def test_rejects_invalid_declared_app_mapping(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["apps"] = "./.app.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / ".app.json").write_text(json.dumps({"apps": {"demo": "not-an-object"}}), encoding="utf-8")
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(any(".app.json" in error for error in report["errors"]), report)

    def test_rejects_invalid_declared_mcp_mapping(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["mcpServers"] = "./.mcp.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / ".mcp.json").write_text(json.dumps({"mcp_servers": []}), encoding="utf-8")
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(any(".mcp.json" in error for error in report["errors"]), report)


if __name__ == "__main__":
    unittest.main()

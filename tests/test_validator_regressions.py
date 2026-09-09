import importlib.util
import json
import os
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "skills/chatgpt-codex-plugin-autopilot/scripts/validate_plugin.py"
PACKAGER = ROOT / "skills/chatgpt-codex-plugin-autopilot/scripts/package_plugin.py"


def square_svg() -> str:
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64"/></svg>\n'


def rgb_png(width: int, height: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + (b"\xff\x00\x00" * width) for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


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


def load_validator_module():
    spec = importlib.util.spec_from_file_location("plugin_autopilot_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("validator module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_regular_file_error(test: unittest.TestCase, report: dict, declared_path: str) -> None:
    test.assertTrue(
        any(declared_path in error and "regular file" in error.lower() for error in report["errors"]),
        report,
    )


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

    def test_undeclared_mcp_file_fails_skills_only_preflight_without_changing_architecture(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            (root / ".mcp.json").write_text(
                json.dumps({"mcp_servers": {"demo": {"url": "https://example.com/mcp"}}}), encoding="utf-8"
            )
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertEqual(report["architecture"], "skills-only")
            self.assertTrue(
                any("mcp_configuration_excluded" in error and ".mcp.json" in error for error in report["errors"]),
                report,
            )

    def test_undeclared_app_file_fails_skills_only_preflight_without_changing_architecture(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            (root / ".app.json").write_text(
                json.dumps({"apps": {"demo": {"id": "connector_demo"}}}), encoding="utf-8"
            )
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertEqual(report["architecture"], "skills-only")
            self.assertTrue(
                any("app_configuration_excluded" in error and ".app.json" in error for error in report["errors"]),
                report,
            )

    def test_packager_blocks_skills_only_zip_with_undeclared_mcp_or_app(self):
        for filename, code in ((".mcp.json", "mcp_configuration_excluded"), (".app.json", "app_configuration_excluded")):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "plugin"
                write_fixture(root)
                (root / filename).write_text("{}\n", encoding="utf-8")
                output = Path(temp) / "plugin.zip"
                proc = subprocess.run(
                    ["python3", str(PACKAGER), str(root), str(output), "--json"],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                )
                combined = f"{proc.stdout}\n{proc.stderr}"
                self.assertNotEqual(proc.returncode, 0, combined)
                self.assertFalse(output.exists(), combined)
                self.assertIn(code, combined)
                self.assertIn(filename, combined)

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

    def test_rejects_backslash_in_archive_member_name(self):
        if "\\" in os.sep:
            self.skipTest("host filesystem uses backslash separators")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            (root / "assets" / "bad\\shot.txt").write_text("not a portable archive name\n", encoding="utf-8")
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(
                any("backslash" in error.lower() for error in report["errors"]),
                report,
            )

    def test_archive_member_path_within_limit_exact_boundaries(self):
        validator = load_validator_module()
        self.assertEqual(validator.MAX_MEMBER_PATH, 1024)
        self.assertTrue(validator.archive_member_path_within_limit("a" * 1023))
        self.assertTrue(validator.archive_member_path_within_limit("a" * 1024))
        self.assertFalse(validator.archive_member_path_within_limit("a" * 1025))
        # Multibyte UTF-8 path where code point count <= 1024 but byte length exceeds 1024
        multibyte_overlong = "é" * 513  # 513 characters, 1026 UTF-8 bytes
        self.assertFalse(validator.archive_member_path_within_limit(multibyte_overlong))

    def test_boundary_valid_archive_member_path_passes_preflight(self):
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            # Add a nested file with a valid multi-segment path on disk
            nested_dir = root / "assets" / ("sub_" + "x" * 40)
            nested_dir.mkdir(parents=True, exist_ok=True)
            (nested_dir / ("data_" + "y" * 40 + ".txt")).write_text("ok\n", encoding="utf-8")
            proc, report = validate(root)
            self.assertEqual(proc.returncode, 0, report)
            self.assertTrue(report.get("ok"), report)

            # Test exact 1,024-character boundary file path passes validator helper and _walk
            # 5 segments of 200 chars (1000) + 4 slashes + "file_" (5) + 10 chars + ".txt" (4) = 1024 chars
            exact_1024 = "/".join(["d" * 200 for _ in range(5)]) + "/file_" + ("a" * 10) + ".txt"
            self.assertEqual(len(exact_1024), 1024)
            self.assertTrue(validator.archive_member_path_within_limit(exact_1024))

    def test_directory_trailing_slash_counted_in_archive_member_path_limit(self):
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            # A 1,024-character directory without slash becomes 1,025 with trailing slash and must be rejected
            dir_1024 = "/".join(["d" * 200 for _ in range(5)]) + "/dir_" + ("b" * 15)
            self.assertEqual(len(dir_1024), 1024)
            self.assertFalse(validator.archive_member_path_within_limit(dir_1024 + "/"))

            errors: list[str] = []
            def mocked_walk_dir(top, *args, **kwargs):
                yield str(root), [dir_1024], []

            with mock.patch.object(validator.os, "walk", side_effect=mocked_walk_dir):
                validator._walk(root, errors, [])
            self.assertTrue(
                any("archive_member_path_too_long" in err and dir_1024 + "/" in err for err in errors),
                errors,
            )

    def test_rejects_archive_member_path_exceeding_limit(self):
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            # Try creating an on-disk member path of 1025 chars if host filesystem permits
            long_subdirs = ["d" * 200 for _ in range(5)]
            target_dir = root.joinpath(*long_subdirs)
            target_file = target_dir / ("f" * 25 + ".txt")
            created_on_disk = False
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                target_file.write_text("overlong path\n", encoding="utf-8")
                created_on_disk = True
            except OSError:
                # Host filesystem (e.g. macOS APFS with 1024 PATH_MAX or Windows MAX_PATH) does not permit
                pass

            if created_on_disk:
                proc, report = validate(root)
                self.assertNotEqual(proc.returncode, 0, report)
                self.assertTrue(
                    any("archive_member_path_too_long" in error for error in report["errors"]),
                    report,
                )
            else:
                # Alternate assertion when host OS path limit is smaller than contract
                overlong_rel = "/".join(["d" * 100 for _ in range(10)]) + "/file_" + ("z" * 20) + ".txt"  # 1039 chars (> 1024)
                self.assertFalse(validator.archive_member_path_within_limit(overlong_rel))
                errors: list[str] = []
                # Test _walk directly with mocked os.walk
                mock_file = root / "assets" / "icon.svg"
                def mocked_walk(top, *args, **kwargs):
                    yield str(root), [], [overlong_rel]

                with mock.patch.object(validator.os, "walk", side_effect=mocked_walk):
                    validator._walk(root, errors, [])
                self.assertTrue(
                    any("archive_member_path_too_long" in err and "exceeds 1024 characters" in err for err in errors),
                    errors,
                )

    def test_packager_rejects_archive_member_path_exceeding_limit(self):
        packager_spec = importlib.util.spec_from_file_location("package_plugin", PACKAGER)
        self.assertIsNotNone(packager_spec and packager_spec.loader)
        packager = importlib.util.module_from_spec(packager_spec)
        packager_spec.loader.exec_module(packager)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            overlong_name = "x" * 1025
            def mocked_walk(top, *args, **kwargs):
                yield str(root), [], [overlong_name]

            with mock.patch.object(packager.os, "walk", side_effect=mocked_walk):
                with self.assertRaises(ValueError) as ctx:
                    packager._collect(root)
                self.assertIn("archive_member_path_too_long", str(ctx.exception))

    def test_rejects_screenshots_on_skills_only_packages(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["interface"]["screenshots"] = ["./assets/icon.svg"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertEqual(report["architecture"], "skills-only")
            self.assertTrue(
                any("screenshot_configuration_excluded" in error for error in report["errors"]),
                report,
            )

    def test_rejects_mcp_screenshots_with_wrong_count_format_or_dimensions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["mcpServers"] = "./.mcp.json"
            manifest["interface"]["defaultPrompt"] = ["Use the fixture.", "Use it again."]
            manifest["interface"]["screenshots"] = ["./assets/shot.png"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / ".mcp.json").write_text(
                json.dumps({"mcp_servers": {"demo": {"url": "https://example.com/mcp"}}}),
                encoding="utf-8",
            )
            (root / "assets" / "shot.png").write_bytes(rgb_png(64, 64))
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            joined = "\n".join(report["errors"]).lower()
            self.assertIn("screenshot", joined)
            self.assertIn("starter prompt", joined)

    def test_accepts_mcp_screenshots_matching_prompt_count_and_dimensions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["mcpServers"] = "./.mcp.json"
            manifest["interface"]["defaultPrompt"] = ["Use the fixture."]
            manifest["interface"]["screenshots"] = ["./assets/shot.png"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / ".mcp.json").write_text(
                json.dumps({"mcp_servers": {"demo": {"url": "https://example.com/mcp"}}}),
                encoding="utf-8",
            )
            (root / "assets" / "shot.png").write_bytes(rgb_png(706, 400))
            proc, report = validate(root)
            self.assertEqual(proc.returncode, 0, report)
            self.assertEqual(report["architecture"], "hybrid")
            self.assertTrue(any("custom UI" in warning for warning in report["warnings"]), report)

    def test_validates_bundled_mcp_configuration_positive_and_negative(self):
        # Positive case with stdio and remote servers, camelCase mcpServers, and forward-compatibility warning
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["mcpServers"] = "./.mcp.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / ".mcp.json").write_text(
                json.dumps({
                    "mcpServers": {
                        "local-tool": {
                            "command": "python3",
                            "args": ["tool.py"],
                            "env": {"DEBUG": "1"},
                            "experimental_option": True,
                        },
                        "remote-service": {
                            "url": "https://mcp.example.com/sse",
                            "transport": "sse",
                            "headers": {"Authorization": "Bearer fake"},
                        },
                    }
                }),
                encoding="utf-8",
            )
            proc, report = validate(root)
            self.assertEqual(proc.returncode, 0, report)
            self.assertEqual(report["architecture"], "hybrid")
            self.assertTrue(any("experimental_option" in w for w in report["warnings"]), report)

        # Negative cases
        negative_cases = (
            (
                {"mcpServers": {"demo": {}}},
                "mcp_server_target_missing",
            ),
            (
                {"mcpServers": {"demo": {"command": ""}}},
                "mcp_server_command_invalid",
            ),
            (
                {"mcpServers": {"demo": {"command": "tool", "args": "not-a-list"}}},
                "mcp_server_args_invalid",
            ),
            (
                {"mcpServers": {"demo": {"command": "tool", "env": {"NUM": 123}}}},
                "mcp_server_env_invalid",
            ),
            (
                {"mcpServers": {"demo": {"url": "http://remote-server.com/mcp"}}},
                "mcp_server_url_insecure",
            ),
            (
                {"mcpServers": {"demo": "not-a-dict"}},
                ".mcp.json server config must be an object",
            ),
        )
        for payload, expected_error in negative_cases:
            with self.subTest(expected=expected_error), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "plugin"
                write_fixture(root)
                manifest_path = root / ".codex-plugin" / "plugin.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["mcpServers"] = "./.mcp.json"
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                (root / ".mcp.json").write_text(json.dumps(payload), encoding="utf-8")
                proc, report = validate(root)
                self.assertNotEqual(proc.returncode, 0, report)
                self.assertTrue(any(expected_error in err for err in report["errors"]), report)

    def test_rejects_malformed_openai_agent_yaml(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            agents = root / "skills" / "worker" / "agents"
            agents.mkdir()
            (agents / "openai.yaml").write_text(
                "interface:\n"
                "  display_name: Fixture\n"
                "  short_description: Fixture plugin\n"
                "policy:\n"
                "  products: [CHAT\n",
                encoding="utf-8",
            )
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(
                any("agents/openai.yaml" in error and "malformed" in error.lower() for error in report["errors"]),
                report,
            )

    def test_rejects_wrong_typed_openai_agent_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            agents = root / "skills" / "worker" / "agents"
            agents.mkdir()
            (agents / "openai.yaml").write_text(
                "interface:\n"
                "  display_name: 123\n"
                "  short_description: Fixture plugin\n"
                "policy:\n"
                "  products: 1\n"
                "  allow_implicit_invocation: yes-please\n",
                encoding="utf-8",
            )
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            joined = "\n".join(report["errors"]).lower()
            self.assertIn("agents/openai.yaml", joined)
            self.assertIn("string", joined)
            self.assertIn("products", joined)

    def test_accepts_quoted_and_list_openai_agent_metadata(self):
        cases = (
            "interface:\n"
            "  display_name: \"Quoted Fixture\"\n"
            "  short_description: \"Fixture plugin\"\n"
            "policy:\n"
            "  products: [CHAT, CODEX]\n"
            "  allow_implicit_invocation: false\n",
            "interface:\n"
            "  display_name: Quoted Fixture\n"
            "  short_description: Fixture plugin\n"
            "policy:\n"
            "  products:\n"
            "    - CHAT\n"
            "    - CODEX\n"
            "  allow_implicit_invocation: true\n",
        )
        for document in cases:
            with self.subTest(document=document), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "plugin"
                write_fixture(root)
                agents = root / "skills" / "worker" / "agents"
                agents.mkdir()
                (agents / "openai.yaml").write_text(document, encoding="utf-8")
                proc, report = validate(root)
                self.assertEqual(proc.returncode, 0, report)

    def test_validates_skill_agent_dependencies_tools_positive_and_negative(self):
        # Positive case with valid MCP tool dependency and forward-compatibility warning
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            agents = root / "skills" / "worker" / "agents"
            agents.mkdir()
            (agents / "openai.yaml").write_text(
                "interface:\n"
                "  display_name: Valid Tool Dependency\n"
                "  short_description: Validates tool dependencies\n"
                "dependencies:\n"
                "  tools:\n"
                "    - type: mcp\n"
                "      value: demoMcpServer\n"
                "      description: Documentation MCP server\n"
                "      transport: streamable_http\n"
                "      url: https://example.com/mcp\n"
                "      experimental_flag: true\n",
                encoding="utf-8",
            )
            proc, report = validate(root)
            self.assertEqual(proc.returncode, 0, report)
            self.assertTrue(any("experimental_flag" in warning for warning in report["warnings"]), report)

        # Negative cases
        negative_cases = (
            (
                "interface:\n  display_name: Neg\n  short_description: Neg\ndependencies:\n  tools: not-a-list\n",
                "skill_agent_tools_wrong_type",
            ),
            (
                "interface:\n  display_name: Neg\n  short_description: Neg\ndependencies:\n  tools:\n    - not-a-mapping\n",
                "skill_agent_tool_entry_wrong_type",
            ),
            (
                "interface:\n  display_name: Neg\n  short_description: Neg\ndependencies:\n  tools:\n    - value: server\n",
                "skill_agent_tool_type_missing",
            ),
            (
                "interface:\n  display_name: Neg\n  short_description: Neg\ndependencies:\n  tools:\n    - type: mcp\n",
                "skill_agent_tool_value_missing",
            ),
            (
                "interface:\n  display_name: Neg\n  short_description: Neg\ndependencies:\n  unsupported_key: true\n",
                "skill_agent_dependency_unsupported",
            ),
            (
                "interface:\n  display_name: Neg\n  short_description: Neg\ndependencies:\n  tools:\n    - type: mcp\n      value: srv\n      url: http://insecure.example.com/mcp\n",
                "skill_agent_tool_url_insecure",
            ),
        )
        for document, expected_error in negative_cases:
            with self.subTest(expected=expected_error), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "plugin"
                write_fixture(root)
                agents = root / "skills" / "worker" / "agents"
                agents.mkdir()
                (agents / "openai.yaml").write_text(document, encoding="utf-8")
                proc, report = validate(root)
                self.assertNotEqual(proc.returncode, 0, report)
                self.assertTrue(any(expected_error in error for error in report["errors"]), report)

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


    def test_declared_app_duplicate_id_warns_and_passes_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["apps"] = "./.app.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / ".app.json").write_text(
                json.dumps({
                    "apps": {
                        "primary": {"id": "connector_sample_app"},
                        "secondary": {"id": "connector_sample_app"},
                    }
                }),
                encoding="utf-8",
            )
            proc, report = validate(root)
            self.assertEqual(proc.returncode, 0, report)
            self.assertTrue(report.get("ok"), report)
            self.assertEqual(report.get("errors"), [])
            warnings = report.get("warnings", [])
            self.assertTrue(
                any(
                    "duplicate_app_reference" in w
                    and "connector_sample_app" in w
                    and "secondary" in w
                    and "primary" in w
                    for w in warnings
                ),
                warnings,
            )

            # Confirm packaging succeeds with warning
            zip_path = Path(temp) / "plugin.zip"
            pack_proc = subprocess.run(
                ["python3", str(PACKAGER), str(root), str(zip_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(pack_proc.returncode, 0, pack_proc.stderr)
            self.assertTrue(zip_path.exists())

    def test_declared_app_duplicate_id_preserves_field_validation_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["apps"] = "./.app.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / ".app.json").write_text(
                json.dumps({
                    "apps": {
                        "primary": {"id": "connector_sample_app"},
                        "secondary": {"id": "connector_sample_app", "required": "not-a-bool"},
                    }
                }),
                encoding="utf-8",
            )
            proc, report = validate(root)
            self.assertNotEqual(proc.returncode, 0, report)
            self.assertFalse(report.get("ok"), report)
            errors = report.get("errors", [])
            warnings = report.get("warnings", [])
            self.assertTrue(any(".app.json secondary.required must be true or false" in err for err in errors), errors)
            self.assertTrue(any("duplicate_app_reference" in w for w in warnings), warnings)

    def test_unit_validate_app_manifest_duplicate_warning(self):
        validator = load_validator_module()
        data = {
            "apps": {
                "alias1": {"id": "connector_service"},
                "alias2": {"id": "connector_service"},
                "alias3": {"id": "connector_service"},
            }
        }
        errors: list[str] = []
        warnings: list[str] = []
        validator._validate_app_manifest(data, errors, warnings)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 2)
        self.assertTrue(all("duplicate_app_reference" in w and "connector_service" in w for w in warnings))

        # Backward compatibility when warnings is omitted or None
        errors_legacy: list[str] = []
        validator._validate_app_manifest(data, errors_legacy)
        self.assertEqual(errors_legacy, [])

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

    def test_unit_validate_mcp_manifest_shapes(self):
        validator = load_validator_module()
        # 1. Valid local command stdio shape under mcpServers
        data_stdio = {
            "mcpServers": {
                "sqlite": {
                    "command": "uvx",
                    "args": ["mcp-server-sqlite", "--db-path", "/tmp/test.db"],
                    "env": {"DEBUG": "1"},
                    "unrecognized_future_field": True,
                }
            }
        }
        errors: list[str] = []
        warnings: list[str] = []
        validator._validate_mcp_manifest(data_stdio, errors, warnings)
        self.assertEqual(errors, [])
        self.assertTrue(any("unrecognized_future_field" in w for w in warnings))

        # 2. Valid remote HTTPS shape under direct map
        data_remote = {
            "fetch": {
                "url": "https://api.example.com/mcp",
                "transport": "streamable_http",
                "headers": {"Authorization": "Bearer token"},
            }
        }
        errors.clear()
        warnings.clear()
        validator._validate_mcp_manifest(data_remote, errors, warnings)
        self.assertEqual(errors, [])

        # 3. Valid legacy mcp_servers with recommendation warning
        data_legacy = {
            "mcp_servers": {
                "demo": {"command": "python3", "args": ["server.py"]}
            }
        }
        errors.clear()
        warnings.clear()
        validator._validate_mcp_manifest(data_legacy, errors, warnings)
        self.assertEqual(errors, [])
        self.assertTrue(any("mcpServers" in w and "camelCase" in w for w in warnings))

        # 4. Negative cases
        negative_cases = (
            ({}, "mcp_servers_missing"),
            ({"mcpServers": "not-a-dict"}, "mcp_servers_wrong_type"),
            ({"mcpServers": {}}, "mcp_servers_missing"),
            ({"mcpServers": {"": {"command": "node"}}}, "mcp_server_name_empty"),
            ({"mcpServers": {"server1": "not-an-object"}}, "mcp_server_wrong_type"),
            ({"mcpServers": {"server1": {"description": "no command or url"}}}, "mcp_server_target_missing"),
            ({"mcpServers": {"server1": {"command": ""}}}, "mcp_server_command_invalid"),
            ({"mcpServers": {"server1": {"command": "node", "args": "not-a-list"}}}, "mcp_server_args_invalid"),
            ({"mcpServers": {"server1": {"command": "node", "env": ["not", "dict"]}}}, "mcp_server_env_invalid"),
            ({"mcpServers": {"server1": {"url": "http://insecure.remote.com/mcp"}}}, "mcp_server_url_insecure"),
        )
        for val_data, expected_err in negative_cases:
            errors.clear()
            warnings.clear()
            validator._validate_mcp_manifest(val_data, errors, warnings)
            self.assertTrue(any(expected_err in e for e in errors), f"Expected {expected_err} in {errors} for {val_data}")

    def test_rejects_symlinked_manifest_before_parsing_external_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            target = Path(temp) / "outside-manifest.json"
            target.write_text('{"external-secret-marker":', encoding="utf-8")
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest_path.unlink()
            manifest_path.symlink_to(target)

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            assert_regular_file_error(self, report, ".codex-plugin/plugin.json")
            self.assertFalse(any("malformed" in error.lower() for error in report["errors"]), report)
            self.assertNotIn("external-secret-marker", json.dumps(report))
            self.assertNotIn(str(target), json.dumps(report))

    def test_rejects_internal_symlinked_skill_before_parsing_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            skill_dir = root / "skills" / "worker"
            target = skill_dir / "REAL-SKILL.md"
            target.write_text(
                "---\nname: leaked-symlink-target\ndescription: Must never be parsed through SKILL.md.\n---\n\nDo not parse.\n",
                encoding="utf-8",
            )
            definition = skill_dir / "SKILL.md"
            definition.unlink()
            definition.symlink_to(target.name)

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            assert_regular_file_error(self, report, "skills/worker/SKILL.md")
            self.assertNotIn("leaked-symlink-target", report["skills"])

    def test_rejects_symlinked_agent_metadata_before_yaml_inspection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            agents = root / "skills" / "worker" / "agents"
            agents.mkdir()
            target = agents / "target.yaml"
            target.write_text(
                "interface:\n"
                "  display_name: Fixture\n"
                "  short_description: Fixture\n"
                "policy:\n"
                "  allow_implicit_invocation: sometimes\n",
                encoding="utf-8",
            )
            metadata = agents / "openai.yaml"
            metadata.symlink_to(target.name)

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            assert_regular_file_error(self, report, "skills/worker/agents/openai.yaml")
            self.assertFalse(any("interface mapping is required" in error for error in report["errors"]), report)
            self.assertFalse(any("allow_implicit_invocation must be" in error for error in report["errors"]), report)

    def test_rejects_symlinked_declared_app_manifest_before_json_parsing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["apps"] = "./.app.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            target = Path(temp) / "outside-app.json"
            target.write_text('{"external-app-marker":', encoding="utf-8")
            (root / ".app.json").symlink_to(target)

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            assert_regular_file_error(self, report, ".app.json")
            self.assertFalse(any("unreadable or malformed" in error for error in report["errors"]), report)
            self.assertNotIn("external-app-marker", json.dumps(report))
            self.assertNotIn(str(target), json.dumps(report))

    def test_rejects_symlinked_declared_mcp_manifest_before_json_parsing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["mcpServers"] = "./.mcp.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            target = Path(temp) / "outside-mcp.json"
            target.write_text('{"external-mcp-marker":', encoding="utf-8")
            (root / ".mcp.json").symlink_to(target)

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            assert_regular_file_error(self, report, ".mcp.json")
            self.assertFalse(any("unreadable or malformed" in error for error in report["errors"]), report)
            self.assertNotIn("external-mcp-marker", json.dumps(report))
            self.assertNotIn(str(target), json.dumps(report))

    def test_rejects_symlinked_brand_asset_before_image_inspection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            target = root / "assets" / "target.svg"
            target.write_text("<svg", encoding="utf-8")
            icon = root / "assets" / "icon.svg"
            icon.unlink()
            icon.symlink_to(target.name)

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            assert_regular_file_error(self, report, "assets/icon.svg")
            self.assertFalse(any("image unreadable" in error.lower() for error in report["errors"]), report)

    def test_rejects_symlinked_hook_path_after_lexical_path_hardening(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["hooks"] = "./hooks.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            target = Path(temp) / "outside-hooks.json"
            target.write_text("{}\n", encoding="utf-8")
            (root / "hooks.json").symlink_to(target)

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            assert_regular_file_error(self, report, "hooks.json")
            self.assertNotIn(str(target), json.dumps(report))

    def test_control_character_asset_path_returns_json_error_instead_of_crashing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["interface"]["logo"] = "./assets/icon\u0000.svg"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(any("control character" in error for error in report["errors"]), report)

    def test_rejects_skills_path_traversal_before_outside_directory_inspection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            write_fixture(root)
            outside = Path(temp) / "outside"
            outside.mkdir()
            (outside / "escape").mkdir()
            (outside / "escape" / "SKILL.md").write_text(
                "---\nname: outside-skill-marker\ndescription: Must not be inspected.\n---\n\nOutside.\n",
                encoding="utf-8",
            )
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["skills"] = "./skills/../../outside"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            proc, report = validate(root)

            self.assertNotEqual(proc.returncode, 0, report)
            self.assertTrue(any("manifest skills path" in error for error in report["errors"]), report)
            self.assertNotIn("outside-skill-marker", report["skills"])

    def test_verified_reader_rejects_file_replaced_by_regular_file_before_open(self):
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            root.mkdir()
            candidate = root / "metadata.json"
            candidate.write_text('{"safe": true}\n', encoding="utf-8")
            outside = Path(temp) / "outside.json"
            outside.write_text('{"external-race-marker": true}\n', encoding="utf-8")
            replacement = root / "replacement.json"
            replacement.write_bytes(outside.read_bytes())
            errors: list[str] = []
            real_open = validator.os.open
            swapped = False

            def swap_then_open(path, flags, *args, **kwargs):
                nonlocal swapped
                if not swapped and Path(path) == candidate:
                    validator.os.replace(replacement, candidate)
                    swapped = True
                return real_open(path, flags, *args, **kwargs)

            with mock.patch.object(validator.os, "open", side_effect=swap_then_open):
                result = validator._read_regular_package_bytes(root, candidate, "metadata", errors)

            self.assertIsNone(result)
            self.assertTrue(any("changed during validation" in error for error in errors), errors)
            self.assertNotIn("external-race-marker", "\n".join(errors))
            self.assertNotIn(str(outside), "\n".join(errors))


if __name__ == "__main__":
    unittest.main()

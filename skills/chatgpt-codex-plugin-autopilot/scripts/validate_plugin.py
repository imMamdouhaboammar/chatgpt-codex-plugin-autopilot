#!/usr/bin/env python3
"""Dependency-free ChatGPT/Codex public plugin preflight validator."""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import struct
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

MAX_ENTRIES = 5000
MAX_TOTAL = 512 * 1024 * 1024
MAX_MEMBER = 100 * 1024 * 1024
MAX_IMAGE = 5 * 1024 * 1024
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
PLUGIN_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
APP_ID = re.compile(
    r"^(?:(?:plugin_)?asdk_app_|connector_|templated_apps_)[A-Za-z0-9][A-Za-z0-9_-]*$"
)
CATEGORIES = {
    "Productivity", "Creativity", "Developer Tools", "Business & Operations",
    "Data & Analytics", "Communication", "Education & Research", "Security",
    "Finance", "Healthcare", "Travel", "Entertainment", "Other",
}
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".xml",
    ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".py", ".sh", ".zsh",
    ".html", ".css", ".svg",
}
SECRET_BASENAME = re.compile(
    r"^(?:\.env(?:\..*)?|auth\.json|credentials?(?:\..*)?|secrets?(?:\..*)?|\.npmrc|\.pypirc)$",
    re.I,
)


def _error(errors: list[str], message: str) -> None:
    errors.append(message)


def _warning(warnings: list[str], message: str) -> None:
    warnings.append(message)


def _load_json(path: Path, errors: list[str], label: str = "manifest") -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _error(errors, f"{label} unreadable or malformed: {exc}")
        return {}
    if not isinstance(value, dict):
        _error(errors, f"{label} must be a JSON object")
        return {}
    return value


def _https(value: object, field: str, errors: list[str], required: bool = False) -> None:
    if value is None:
        if required:
            _error(errors, f"interface.{field} is required for MCP-backed public submission")
        return
    if not isinstance(value, str) or not value:
        _error(errors, f"interface.{field} must be a non-empty HTTPS URL")
        return
    if len(value) > 1024:
        _error(errors, f"interface.{field} exceeds final directory limit of 1024 characters")
    parsed = urlparse(value)
    if parsed.scheme.lower() != "https" or not parsed.netloc or parsed.username or parsed.password:
        _error(errors, f"interface.{field} must be an HTTPS URL without embedded credentials")


def _public_https(value: object, field: str, errors: list[str], limit: int = 2048) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not value:
        _error(errors, f"{field} must be a non-empty HTTPS URL")
        return
    if len(value) > limit:
        _error(errors, f"{field} must be <={limit} characters")
    parsed = urlparse(value)
    if parsed.scheme.lower() != "https" or not parsed.netloc or parsed.username or parsed.password:
        _error(errors, f"{field} must be an HTTPS URL without embedded credentials")


def _has_control(value: str) -> bool:
    return any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)


def _relative_file_path(
    root: Path,
    field: str,
    value: object,
    errors: list[str],
    *,
    required: bool = False,
    require_dot_prefix: bool = True,
) -> Path | None:
    if value is None:
        if required:
            _error(errors, f"{field} is required")
        return None
    if not isinstance(value, str) or not value:
        _error(errors, f"{field} must be a non-empty relative file path")
        return None
    if value != value.strip():
        _error(errors, f"{field} path must not contain outer whitespace: {value!r}")
    if _has_control(value):
        _error(errors, f"{field} path contains a control character")
    if require_dot_prefix and not value.startswith("./"):
        _error(errors, f"{field} path must start with ./: {value}")
    if value.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", value):
        _error(errors, f"{field} path is unsafe and must be relative: {value}")
        return None

    relative = value[2:] if value.startswith("./") else value
    normalized = relative.replace("\\", "/")
    segments = normalized.split("/")
    if ".." in segments:
        _error(errors, f"{field} path contains unsafe .. traversal: {value}")
        return None
    if not relative or any(segment == "" for segment in segments):
        _error(errors, f"{field} path must identify a file inside the plugin: {value}")
        return None

    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        _error(errors, f"{field} path escapes plugin root: {value}")
        return None
    return candidate


def _component_path(
    root: Path,
    manifest: dict,
    field: str,
    expected: str,
    errors: list[str],
    required: bool = False,
) -> bool:
    value = manifest.get(field)
    if value is None:
        if required:
            _error(errors, f"manifest {field} path is required")
        return False
    if not isinstance(value, str) or not value:
        _error(errors, f"manifest {field} path must be a non-empty string")
        return False
    if value != value.strip() or _has_control(value):
        _error(errors, f"manifest {field} path contains unsupported whitespace or control characters")
    if not value.startswith("./"):
        _error(errors, f"manifest {field} path must start with ./: {value}")
    normalized = value[2:] if value.startswith("./") else value
    if ".." in normalized.replace("\\", "/").split("/"):
        _error(errors, f"manifest {field} path contains unsafe .. traversal: {value}")
        return False
    if normalized.rstrip("/") != expected.rstrip("/"):
        _error(errors, f"manifest {field} path must resolve to ./{expected}: {value}")
        return False
    candidate = root / expected
    if expected.endswith("/"):
        if not candidate.is_dir():
            _error(errors, f"manifest {field} directory is missing: ./{expected}")
            return False
    elif not candidate.is_file():
        _error(errors, f"manifest {field} file is missing: ./{expected}")
        return False
    return True


def _validate_codex_plugin_directory(root: Path, errors: list[str]) -> None:
    directory = root / ".codex-plugin"
    if not directory.is_dir():
        return
    for item in sorted(directory.iterdir(), key=lambda path: path.name):
        if item.name != "plugin.json":
            _error(
                errors,
                f".codex-plugin may contain plugin.json only; move or remove: .codex-plugin/{item.name}",
            )


def _luminance(hex_color: str) -> float:
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _validate_brand_color(interface: dict, field: str, background: str, errors: list[str]) -> None:
    value = interface.get(field)
    if value is None:
        return
    if not isinstance(value, str) or not HEX_COLOR.fullmatch(value):
        _error(errors, f"interface.{field} must be a six-digit hex color")
        return
    if _contrast(value, background) < 2.0:
        _error(errors, f"interface.{field} must have at least 2:1 contrast against {background}")


def _numeric_dimension(value: str | None) -> float | None:
    if value is None or not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", value.strip()):
        return None
    try:
        result = float(value)
        return result if result > 0 else None
    except ValueError:
        return None


def _svg_size(path: Path) -> tuple[float, float]:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    if root.tag.split("}")[-1].lower() != "svg":
        raise ValueError("SVG root element must be <svg>")
    view_box = root.attrib.get("viewBox") or root.attrib.get("viewbox")
    if view_box:
        values = [float(item) for item in re.split(r"[\s,]+", view_box.strip()) if item]
        if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
            raise ValueError("SVG viewBox must contain four positive dimensions")
        return values[2], values[3]
    width = _numeric_dimension(root.attrib.get("width"))
    height = _numeric_dimension(root.attrib.get("height"))
    if width is None or height is None:
        raise ValueError("SVG must declare numeric viewBox or width/height")
    return width, height


def _png_size(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("invalid PNG")
    return struct.unpack(">II", data[16:24])


def _jpeg_size(data: bytes) -> tuple[int, int]:
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError("invalid JPEG")
    index = 2
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while index + 4 <= len(data):
        while index < len(data) and data[index] != 0xFF:
            index += 1
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            break
        marker = data[index]
        index += 1
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            break
        length = struct.unpack(">H", data[index:index + 2])[0]
        if length < 2 or index + length > len(data):
            break
        if marker in sof and length >= 7:
            height, width = struct.unpack(">HH", data[index + 3:index + 7])
            return width, height
        index += length
    raise ValueError("JPEG dimensions not found")


def _webp_size(data: bytes) -> tuple[int, int]:
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("invalid WebP")
    kind = data[12:16]
    if kind == b"VP8X":
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return width, height
    if kind == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if kind == b"VP8 " and len(data) >= 30:
        frame = data.find(b"\x9d\x01\x2a", 20)
        if frame >= 0 and frame + 7 <= len(data):
            width, height = struct.unpack("<HH", data[frame + 3:frame + 7])
            return width & 0x3FFF, height & 0x3FFF
    raise ValueError("WebP dimensions not found")


def _image_size(path: Path) -> tuple[float, float]:
    suffix = path.suffix.lower()
    if suffix == ".svg":
        return _svg_size(path)
    data = path.read_bytes()
    if suffix == ".png":
        return _png_size(data)
    if suffix in {".jpg", ".jpeg"}:
        return _jpeg_size(data)
    if suffix == ".webp":
        return _webp_size(data)
    raise ValueError("unsupported image format")


def _validate_image(root: Path, field: str, value: object, errors: list[str]) -> None:
    if not isinstance(value, str) or not value:
        _error(errors, f"interface.{field} is required and must reference a square image")
        return
    candidate = _relative_file_path(root, f"interface.{field}", value, errors, required=True)
    if candidate is None:
        return
    if not candidate.is_file():
        _error(errors, f"interface.{field} asset is missing: {value}")
        return
    if candidate.stat().st_size > MAX_IMAGE:
        _error(errors, f"interface.{field} image exceeds 5 MiB: {value}")
    if candidate.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
        _error(errors, f"interface.{field} image format is unsupported: {value}")
        return
    try:
        width, height = _image_size(candidate)
    except Exception as exc:
        _error(errors, f"interface.{field} image unreadable: {value}: {exc}")
        return
    if width != height:
        _error(errors, f"interface.{field} image must be square: {value}")
    if width < 48 or height < 48:
        _error(errors, f"interface.{field} image dimensions must be at least 48x48: {value}")
    if candidate.suffix.lower() != ".svg" and (width > 4096 or height > 4096):
        _error(errors, f"interface.{field} raster dimensions exceed 4096x4096: {value}")


def _skill_metadata(path: Path) -> tuple[str | None, str | None]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, None
    end = text.find("\n---", 4)
    if end < 0:
        return None, None
    frontmatter = text[4:end]
    name = re.search(r"(?m)^name:\s*[\"']?([^\n\"']+)", frontmatter)
    description = re.search(r"(?m)^description:\s*(.+)$", frontmatter)
    return (
        " ".join(name.group(1).split()) if name else None,
        " ".join(description.group(1).strip("\"'").split()) if description else None,
    )


def _yaml_unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _yaml_top_level_blocks(text: str, label: str, errors: list[str]) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    if "\t" in text:
        _error(errors, f"{label} must use spaces for indentation")
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw.startswith((" ", "\t")):
            match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):\s*(?:#.*)?", raw)
            if not match:
                _error(errors, f"{label} must use mapping entries at the top level")
                current = None
                continue
            current = match.group(1)
            blocks.setdefault(current, [])
        elif current is not None:
            blocks[current].append(raw)
    return blocks


def _yaml_block_fields(lines: list[str], label: str, errors: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    base_indent: int | None = None
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if base_indent is None:
            base_indent = indent
        if indent != base_indent:
            continue
        match = re.fullmatch(r"\s*([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*", raw)
        if not match:
            _error(errors, f"{label} contains unsupported mapping syntax: {raw.strip()}")
            continue
        fields[match.group(1)] = match.group(2)
    return fields


def _validate_skill_agent_metadata(skill_dir: Path, errors: list[str], warnings: list[str]) -> None:
    path = skill_dir / "agents" / "openai.yaml"
    if not path.exists():
        return
    rel = f"skills/{skill_dir.name}/agents/openai.yaml"
    if not path.is_file():
        _error(errors, f"{rel} must be a regular file")
        return
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _error(errors, f"{rel} unreadable: {exc}")
        return

    blocks = _yaml_top_level_blocks(text, rel, errors)
    interface_lines = blocks.get("interface")
    if interface_lines is None:
        _error(errors, f"{rel}: interface mapping is required")
        return
    interface = _yaml_block_fields(interface_lines, f"{rel} interface", errors)
    for field in ("display_name", "short_description"):
        value = interface.get(field)
        if value is None or not _yaml_unquote(value).strip():
            _error(errors, f"{rel}: interface.{field} is required and must be non-empty")

    for field in ("icon_small", "icon_large"):
        if field in interface:
            value = _yaml_unquote(interface[field])
            candidate = _relative_file_path(
                skill_dir,
                f"{rel} interface.{field}",
                value,
                errors,
                required=True,
                require_dot_prefix=False,
            )
            if candidate is not None and not candidate.is_file():
                _error(errors, f"{rel}: interface.{field} asset is missing: {value}")

    brand = interface.get("brand_color")
    if brand is not None and not HEX_COLOR.fullmatch(_yaml_unquote(brand)):
        _error(errors, f"{rel}: interface.brand_color must be a six-digit hex color")
    prompt = interface.get("default_prompt")
    if prompt is not None and not _yaml_unquote(prompt).strip():
        _error(errors, f"{rel}: interface.default_prompt must be non-empty when provided")

    if "policy" in blocks:
        policy = _yaml_block_fields(blocks["policy"], f"{rel} policy", errors)
        unsupported = sorted(set(policy) - {"products", "allow_implicit_invocation"})
        for key in unsupported:
            _error(errors, f"{rel}: unsupported policy field: {key}")
        implicit = policy.get("allow_implicit_invocation")
        if implicit is not None and _yaml_unquote(implicit).lower() not in {"true", "false"}:
            _error(errors, f"{rel}: policy.allow_implicit_invocation must be true or false")
        products = policy.get("products")
        if products is not None:
            raw = _yaml_unquote(products).strip()
            if raw.startswith("[") and raw.endswith("]"):
                values = [item.strip().strip("\"'") for item in raw[1:-1].split(",") if item.strip()]
                if not values or any(item not in {"CHAT", "CODEX"} for item in values):
                    _error(errors, f"{rel}: policy.products may contain CHAT, CODEX, or both")
            else:
                _warning(
                    warnings,
                    f"{rel}: policy.products uses YAML syntax outside the dependency-free inline-list checker; official uploader remains authoritative",
                )

    if "dependencies" in blocks:
        dependencies = _yaml_block_fields(blocks["dependencies"], f"{rel} dependencies", errors)
        unsupported = sorted(set(dependencies) - {"tools"})
        for key in unsupported:
            _error(errors, f"{rel}: only dependencies.tools is supported; found {key}")

    known = {"interface", "policy", "dependencies"}
    unknown = sorted(set(blocks) - known)
    if unknown:
        _warning(
            warnings,
            f"{rel}: unrecognized top-level metadata retained for forward compatibility: {', '.join(unknown)}",
        )


def _validate_app_manifest(path: Path, errors: list[str]) -> None:
    data = _load_json(path, errors, ".app.json")
    if not data:
        return
    apps = data.get("apps")
    if not isinstance(apps, dict):
        _error(errors, ".app.json apps is required and must be an object")
        return
    seen_ids: set[str] = set()
    for alias, entry in apps.items():
        if not isinstance(entry, dict):
            _error(errors, f".app.json app entry must be an object: {alias}")
            continue
        app_id = entry.get("id")
        if not isinstance(app_id, str) or not app_id:
            _error(errors, f".app.json app entry id is required and must be a string: {alias}")
        elif not APP_ID.fullmatch(app_id):
            _error(errors, f".app.json app id has unsupported format: {alias}: {app_id}")
        elif app_id in seen_ids:
            _error(errors, f".app.json duplicate app id: {app_id}")
        else:
            seen_ids.add(app_id)
        for field in ("optional", "required"):
            if field in entry and not isinstance(entry[field], bool):
                _error(errors, f".app.json {alias}.{field} must be true or false")


def _validate_mcp_manifest(path: Path, errors: list[str]) -> None:
    data = _load_json(path, errors, ".mcp.json")
    if not data:
        return
    servers = data.get("mcp_servers") if "mcp_servers" in data else data
    if not isinstance(servers, dict) or not servers:
        _error(errors, ".mcp.json must contain a non-empty direct server map or mcp_servers object")
        return
    for name, config in servers.items():
        if not isinstance(name, str) or not name:
            _error(errors, ".mcp.json server names must be non-empty strings")
        if not isinstance(config, dict):
            _error(errors, f".mcp.json server config must be an object: {name}")


def _walk(root: Path, errors: list[str], exclusions: list[str]) -> tuple[list[Path], int, int]:
    files: list[Path] = []
    directories: set[Path] = set()
    total = 0
    normalized: dict[str, str] = {}
    absolute_user_path = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/")
    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in list(dirs):
            path = current_path / name
            if name == "__pycache__":
                _error(errors, f"transient Python bytecode cache is not allowed in public plugin: {path.relative_to(root)}")
                dirs.remove(name)
                continue
            if path.is_symlink():
                _error(errors, f"symlink is not allowed in public plugin: {path.relative_to(root)}")
                dirs.remove(name)
                continue
            directories.add(path)
        for name in names:
            path = current_path / name
            rel = path.relative_to(root).as_posix()
            if rel != rel.strip():
                _error(errors, f"archive member path has outer whitespace: {rel!r}")
            segments = rel.split("/")
            if any(segment != segment.strip() for segment in segments):
                _error(errors, f"archive member path segment has outer whitespace: {rel!r}")
            if len(segments) > 20:
                _error(errors, f"archive member path must contain at most 20 segments: {rel}")
            try:
                mode = path.lstat().st_mode
            except OSError as exc:
                _error(errors, f"unreadable plugin member {rel}: {exc}")
                continue
            if stat.S_ISLNK(mode):
                _error(errors, f"symlink is not allowed in public plugin: {rel}")
                continue
            if not stat.S_ISREG(mode):
                _error(errors, f"unsupported plugin member type: {rel}")
                continue
            size = path.stat().st_size
            files.append(path)
            total += size
            if size > MAX_MEMBER:
                _error(errors, f"plugin member exceeds 100 MiB: {rel}")
            base = path.name
            if base in {".DS_Store", "Thumbs.db"} or base.startswith("._"):
                _error(errors, f"operating-system metadata is not allowed: {rel}")
            if base.endswith((".pyc", ".pyo")):
                _error(errors, f"transient Python bytecode is not allowed in public plugin: {rel}")
            if SECRET_BASENAME.match(base):
                _error(errors, f"secret-shaped file is not allowed in public plugin: {rel}")
            normalized_key = unicodedata.normalize("NFC", rel).casefold()
            previous = normalized.get(normalized_key)
            if previous is not None and previous != rel:
                _error(errors, f"path normalization collision: {previous} vs {rel}")
            normalized[normalized_key] = rel
            for slug in exclusions:
                if slug and (slug in Path(rel).parts or slug in rel):
                    _error(errors, f"public exclusion remains in plugin path: {slug}: {rel}")
            if size <= 1024 * 1024 and path.suffix.lower() in TEXT_SUFFIXES:
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    text = ""
                if absolute_user_path.search(text):
                    _error(errors, f"absolute user path found in public text file: {rel}")
                for slug in exclusions:
                    if slug and slug in text:
                        _error(errors, f"public exclusion remains in plugin text: {slug}: {rel}")
    entry_count = len(files) + len(directories)
    if entry_count > MAX_ENTRIES:
        _error(errors, f"plugin would exceed 5000 archive entries: {entry_count}")
    if total > MAX_TOTAL:
        _error(errors, f"plugin extracted size exceeds 512 MiB: {total}")
    return sorted(files), entry_count, total


def validate_plugin(plugin_root: str, exclusions: list[str] | None = None) -> dict:
    root = Path(plugin_root).expanduser().resolve()
    exclusions = sorted({item for item in (exclusions or []) if item})
    errors: list[str] = []
    warnings: list[str] = []
    if not root.is_dir():
        return {
            "ok": False,
            "architecture": "unknown",
            "skills": [],
            "errors": [f"plugin root is not a directory: {root}"],
            "warnings": [],
        }

    _validate_codex_plugin_directory(root, errors)
    manifest_path = root / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        _error(errors, "missing .codex-plugin/plugin.json")
        manifest: dict = {}
    else:
        manifest = _load_json(manifest_path, errors)

    name = manifest.get("name")
    if not isinstance(name, str) or not PLUGIN_NAME.fullmatch(name):
        _error(errors, "plugin name must be 1..64 characters using supported ASCII letters, digits, _ or -")
    version = manifest.get("version")
    if not isinstance(version, str) or len(version) > 64 or not SEMVER.fullmatch(version):
        _error(errors, "plugin version must be strict semver and <=64 characters")
    description = manifest.get("description")
    if not isinstance(description, str) or not description or len(description) > 1024:
        _error(errors, "plugin description is required and must be <=1024 characters")
    author = manifest.get("author")
    author_name = author.get("name") if isinstance(author, dict) else None
    if not isinstance(author_name, str) or not author_name or len(author_name) > 120:
        _error(errors, "author.name is required and must be <=120 characters")
    if isinstance(author, dict):
        _public_https(author.get("url"), "author.url", errors, 2048)
    _public_https(manifest.get("homepage"), "homepage", errors, 2048)
    _public_https(manifest.get("repository"), "repository", errors, 2048)

    mcp_declared = _component_path(root, manifest, "mcpServers", ".mcp.json", errors) if "mcpServers" in manifest else False
    apps_declared = _component_path(root, manifest, "apps", ".app.json", errors) if "apps" in manifest else False
    if mcp_declared:
        _validate_mcp_manifest(root / ".mcp.json", errors)
    elif (root / ".mcp.json").exists():
        _warning(warnings, "root .mcp.json is ignored because manifest mcpServers is not set to ./.mcp.json")
    if apps_declared:
        _validate_app_manifest(root / ".app.json", errors)
    elif (root / ".app.json").exists():
        _warning(warnings, "root .app.json is ignored because manifest apps is not set to ./.app.json")

    if "hooks" in manifest:
        hook_value = manifest.get("hooks")
        if isinstance(hook_value, str):
            hook_path = _relative_file_path(root, "manifest hooks", hook_value, errors)
            if hook_path is not None and not hook_path.is_file():
                _error(errors, f"manifest hooks file is missing: {hook_value}")
        elif isinstance(hook_value, list):
            for index, item in enumerate(hook_value):
                if isinstance(item, str):
                    hook_path = _relative_file_path(root, f"manifest hooks[{index}]", item, errors)
                    if hook_path is not None and not hook_path.is_file():
                        _error(errors, f"manifest hooks file is missing: {item}")
                elif not isinstance(item, dict):
                    _error(errors, f"manifest hooks[{index}] must be a path or inline hooks object")
        elif not isinstance(hook_value, dict):
            _error(errors, "manifest hooks must be a path, list, or inline hooks object")

    has_mcp = mcp_declared or apps_declared
    skill_path_value = manifest.get("skills", "./skills/")
    has_skills = False
    skills: list[str] = []
    skill_names: set[str] = set()
    if isinstance(skill_path_value, str):
        if not skill_path_value:
            _error(errors, "manifest skills must be a non-empty relative path string")
            skill_root = root / "__invalid__"
        else:
            if not skill_path_value.startswith("./"):
                _error(errors, f"manifest skills path must start with ./: {skill_path_value}")
            relative = skill_path_value[2:] if skill_path_value.startswith("./") else skill_path_value
            if relative.rstrip("/") != "skills":
                _error(errors, f"manifest skills path must resolve to ./skills/: {skill_path_value}")
            skill_root = (root / relative).resolve()
            try:
                skill_root.relative_to(root)
            except ValueError:
                _error(errors, f"manifest skills path escapes plugin root: {skill_path_value}")
                skill_root = root / "__invalid__"

        if skill_root.is_dir():
            for item in sorted(skill_root.iterdir(), key=lambda child: child.name):
                if item.is_symlink() or not item.is_dir():
                    _error(errors, f"skills direct child must be a real directory containing SKILL.md; found: skills/{item.name}")
                    continue
                directory = item
                if directory.name.startswith("."):
                    _error(errors, f"skill directory must not be hidden: {directory.name}")
                    continue
                definition = directory / "SKILL.md"
                if not definition.is_file():
                    _error(errors, f"skill directory is missing SKILL.md: {directory.name}")
                    continue
                try:
                    skill_name, skill_description = _skill_metadata(definition)
                except Exception as exc:
                    _error(errors, f"skill definition unreadable: {directory.name}: {exc}")
                    continue
                if not skill_name:
                    _error(errors, f"skill name is required: {directory.name}")
                elif skill_name in skill_names:
                    _error(errors, f"skill name must be unique within plugin: {skill_name}")
                else:
                    skill_names.add(skill_name)
                    skills.append(skill_name)
                if not skill_description:
                    _error(errors, f"skill description is required: {directory.name}")
                elif len(skill_description) > 1024:
                    _error(errors, f"skill description exceeds 1024 characters: {directory.name}")
                try:
                    skill_text = definition.read_text(encoding="utf-8")
                    front_end = skill_text.find("\n---", 4)
                    body = skill_text[front_end + 4:].strip() if front_end >= 0 else ""
                    if not body:
                        _error(errors, f"skill body must not be empty: {directory.name}")
                except Exception as exc:
                    _error(errors, f"skill body unreadable: {directory.name}: {exc}")
                if isinstance(name, str) and skill_name and len(f"{name}:{skill_name}") > 64:
                    _error(errors, f"combined plugin and skill identity exceeds 64 characters: {skill_name}")
                _validate_skill_agent_metadata(directory, errors, warnings)
            has_skills = bool(skills)
        elif "skills" in manifest:
            _error(errors, f"manifest skills path is missing: {skill_path_value}")
    else:
        _error(errors, "manifest skills must be a relative path string")

    architecture = "hybrid" if has_mcp and has_skills else "MCP-backed" if has_mcp else "skills-only"
    if not has_skills and not has_mcp:
        _error(errors, "plugin must contain at least one Skill or an MCP-backed capability")

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        _error(errors, "manifest interface is required and must be an object")
        interface = {}
    for field, limit in (("displayName", 30), ("shortDescription", 30), ("longDescription", 4000), ("developerName", 80)):
        value = interface.get(field)
        if not isinstance(value, str) or not value:
            _error(errors, f"interface.{field} is required")
        elif len(value) > limit:
            _error(errors, f"interface.{field} exceeds final directory limit of {limit} characters")
        if field in {"displayName", "shortDescription", "developerName"} and isinstance(value, str):
            if "\n" in value or "\r" in value:
                _error(errors, f"interface.{field} must fit on one line")

    category = interface.get("category")
    if not isinstance(category, str) or not category:
        _error(errors, "interface.category is required for final directory submission")
    elif category not in CATEGORIES:
        _error(errors, f"interface.category is unsupported: {category}")

    capabilities = interface.get("capabilities")
    if capabilities is not None:
        if not isinstance(capabilities, list) or len(capabilities) > 20:
            _error(errors, "interface.capabilities must be an array with at most 20 items")
        elif any(not isinstance(item, str) or not item or len(item) > 120 or "\n" in item or "\r" in item for item in capabilities):
            _error(errors, "each interface.capabilities item must be a non-empty one-line string <=120 characters")

    prompts = interface.get("defaultPrompt")
    if prompts is not None:
        prompt_list = [prompts] if isinstance(prompts, str) else prompts if isinstance(prompts, list) else None
        if prompt_list is None:
            _error(errors, "interface.defaultPrompt must be a string or list of strings")
        else:
            if len(prompt_list) > 3:
                _error(errors, "interface.defaultPrompt must contain at most 3 prompts")
            normalized_prompts: set[str] = set()
            for prompt in prompt_list:
                if not isinstance(prompt, str) or not prompt.strip():
                    _error(errors, "each interface.defaultPrompt must be a non-empty string")
                    continue
                if len(prompt) > 128 or "\n" in prompt or "\r" in prompt:
                    _error(errors, "each interface.defaultPrompt must be one line and <=128 characters")
                if re.search(r"(?<![A-Za-z0-9._%+-])@[A-Za-z0-9_-]+", prompt):
                    _error(errors, "interface.defaultPrompt must not contain an app @mention")
                normalized_prompt = " ".join(unicodedata.normalize("NFKC", prompt).split()).casefold()
                if normalized_prompt in normalized_prompts:
                    _error(errors, "interface.defaultPrompt entries must be unique after normalization")
                normalized_prompts.add(normalized_prompt)

    _validate_brand_color(interface, "brandColor", "#FFFFFF", errors)
    _validate_brand_color(interface, "brandColorDark", "#212121", errors)

    for field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL", "supportURL"):
        _https(interface.get(field), field, errors, required=has_mcp)
    _validate_image(root, "logo", interface.get("logo"), errors)
    _validate_image(root, "composerIcon", interface.get("composerIcon"), errors)

    screenshots = interface.get("screenshots")
    if screenshots is not None:
        if not isinstance(screenshots, list):
            _error(errors, "interface.screenshots must be a list of relative asset paths")
        else:
            for index, screenshot in enumerate(screenshots):
                candidate = _relative_file_path(root, f"interface.screenshots[{index}]", screenshot, errors, require_dot_prefix=True)
                if candidate is not None and not candidate.is_file():
                    _error(errors, f"interface.screenshots[{index}] asset is missing: {screenshot}")

    files, entry_count, total_bytes = _walk(root, errors, exclusions)
    if not exclusions:
        warnings.append("no explicit public exclusions supplied; confirm the repository has no internal-only capabilities")

    return {
        "ok": not errors,
        "pluginRoot": str(root),
        "name": name if isinstance(name, str) else "",
        "version": version if isinstance(version, str) else "",
        "architecture": architecture,
        "skills": skills,
        "exclusions": exclusions,
        "entries": entry_count,
        "uncompressedBytes": total_bytes,
        "files": len(files),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--exclude", action="append", default=[], help="public capability slug that must not occur in paths or text")
    args = parser.parse_args(argv)
    report = validate_plugin(args.plugin_root, args.exclude)
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("plugin preflight: " + ("PASS" if report["ok"] else "FAIL"))
        print(f"architecture: {report['architecture']}; skills: {len(report['skills'])}; entries: {report['entries']}")
        for warning in report["warnings"]:
            print(f"warning: {warning}")
        for error in report["errors"]:
            print(f"error: {error}", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

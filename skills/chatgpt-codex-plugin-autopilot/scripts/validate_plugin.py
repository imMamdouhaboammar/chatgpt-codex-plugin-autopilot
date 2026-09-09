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


def _load_json_bytes(data: bytes, errors: list[str], label: str = "manifest") -> dict:
    try:
        value = json.loads(data.decode("utf-8"))
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


def _package_member_stat(
    root: Path,
    path: Path,
    label: str,
    errors: list[str],
    *,
    required: bool = True,
    missing_message: str | None = None,
) -> os.stat_result | None:
    try:
        relative = path.relative_to(root)
    except ValueError:
        _error(errors, f"{label} path escapes plugin root")
        return None
    rel = relative.as_posix()
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        try:
            member = current.lstat()
        except FileNotFoundError:
            if required:
                _error(errors, missing_message or f"{label} parent is missing: {rel}")
            return None
        except (OSError, ValueError):
            _error(errors, f"{label} parent is unreadable: {rel}")
            return None
        if stat.S_ISLNK(member.st_mode):
            _error(errors, f"{label} parent must not be a symlink: {rel}")
            return None
        if not stat.S_ISDIR(member.st_mode):
            _error(errors, f"{label} parent must be a directory: {rel}")
            return None
    try:
        return path.lstat()
    except FileNotFoundError:
        if required:
            _error(errors, missing_message or f"{label} is missing: {rel}")
        return None
    except (OSError, ValueError):
        _error(errors, f"{label} is unreadable: {rel}")
        return None


def _regular_package_file(
    root: Path,
    path: Path,
    label: str,
    errors: list[str],
    *,
    required: bool = True,
    missing_message: str | None = None,
) -> bool:
    member = _package_member_stat(
        root,
        path,
        label,
        errors,
        required=required,
        missing_message=missing_message,
    )
    if member is None:
        return False
    if not stat.S_ISREG(member.st_mode):
        rel = path.relative_to(root).as_posix()
        _error(errors, f"{label} must be a regular file: {rel}")
        return False
    return True


def _real_package_directory(
    root: Path,
    path: Path,
    label: str,
    errors: list[str],
    *,
    required: bool = True,
    missing_message: str | None = None,
) -> bool:
    member = _package_member_stat(
        root,
        path,
        label,
        errors,
        required=required,
        missing_message=missing_message,
    )
    if member is None:
        return False
    if not stat.S_ISDIR(member.st_mode):
        rel = path.relative_to(root).as_posix()
        _error(errors, f"{label} must be a real directory: {rel}")
        return False
    return True


def _same_member(before: os.stat_result, after: os.stat_result) -> bool:
    if before.st_ino and after.st_ino:
        return before.st_dev == after.st_dev and before.st_ino == after.st_ino
    return (
        stat.S_IFMT(before.st_mode) == stat.S_IFMT(after.st_mode)
        and before.st_size == after.st_size
        and getattr(before, "st_mtime_ns", None) == getattr(after, "st_mtime_ns", None)
        and getattr(before, "st_ctime_ns", None) == getattr(after, "st_ctime_ns", None)
    )


def _open_regular_package_file(
    root: Path,
    path: Path,
    label: str,
    errors: list[str],
    *,
    required: bool = True,
    missing_message: str | None = None,
) -> tuple[int, os.stat_result] | None:
    before = _package_member_stat(
        root,
        path,
        label,
        errors,
        required=required,
        missing_message=missing_message,
    )
    if before is None:
        return None
    rel = path.relative_to(root).as_posix()
    if not stat.S_ISREG(before.st_mode):
        _error(errors, f"{label} must be a regular file: {rel}")
        return None
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except (OSError, ValueError):
        _error(errors, f"{label} must remain a regular file while opening: {rel}")
        return None
    try:
        after = os.fstat(descriptor)
        if not stat.S_ISREG(after.st_mode) or not _same_member(before, after):
            _error(errors, f"{label} changed during validation: {rel}")
            os.close(descriptor)
            return None
        return descriptor, after
    except OSError:
        os.close(descriptor)
        _error(errors, f"{label} could not be verified after opening: {rel}")
        return None


def _read_regular_package_bytes(
    root: Path,
    path: Path,
    label: str,
    errors: list[str],
    *,
    required: bool = True,
    missing_message: str | None = None,
    max_bytes: int = MAX_MEMBER,
) -> tuple[bytes, os.stat_result] | None:
    opened = _open_regular_package_file(
        root,
        path,
        label,
        errors,
        required=required,
        missing_message=missing_message,
    )
    if opened is None:
        return None
    descriptor, member = opened
    rel = path.relative_to(root).as_posix()
    if member.st_size > max_bytes:
        os.close(descriptor)
        _error(errors, f"{label} exceeds safe read limit: {rel}")
        return None
    try:
        handle = os.fdopen(descriptor, "rb", closefd=True)
    except (OSError, ValueError):
        os.close(descriptor)
        _error(errors, f"{label} could not be read after verification: {rel}")
        return None
    try:
        with handle:
            data = handle.read(max_bytes + 1)
    except OSError:
        _error(errors, f"{label} could not be read after verification: {rel}")
        return None
    if len(data) > max_bytes:
        _error(errors, f"{label} changed size during validation: {rel}")
        return None
    return data, member


def _read_regular_package_text(
    root: Path,
    path: Path,
    label: str,
    errors: list[str],
    *,
    required: bool = True,
    missing_message: str | None = None,
    max_bytes: int = MAX_MEMBER,
) -> str | None:
    result = _read_regular_package_bytes(
        root,
        path,
        label,
        errors,
        required=required,
        missing_message=missing_message,
        max_bytes=max_bytes,
    )
    if result is None:
        return None
    data, _ = result
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        rel = path.relative_to(root).as_posix()
        _error(errors, f"{label} must be UTF-8 text: {rel}")
        return None


def _verify_regular_package_file(
    root: Path,
    path: Path,
    label: str,
    errors: list[str],
    *,
    required: bool = True,
    missing_message: str | None = None,
) -> bool:
    opened = _open_regular_package_file(
        root,
        path,
        label,
        errors,
        required=required,
        missing_message=missing_message,
    )
    if opened is None:
        return False
    descriptor, _ = opened
    os.close(descriptor)
    return True


def _list_real_package_directory(
    root: Path,
    path: Path,
    label: str,
    errors: list[str],
    *,
    required: bool = True,
    missing_message: str | None = None,
) -> list[str] | None:
    before = _package_member_stat(
        root,
        path,
        label,
        errors,
        required=required,
        missing_message=missing_message,
    )
    if before is None:
        return None
    rel = path.relative_to(root).as_posix()
    if not stat.S_ISDIR(before.st_mode):
        _error(errors, f"{label} must be a real directory: {rel}")
        return None
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
    except (OSError, ValueError):
        _error(errors, f"{label} must remain a real directory while opening: {rel}")
        return None
    try:
        try:
            after = os.fstat(descriptor)
        except OSError:
            _error(errors, f"{label} could not be verified after opening: {rel}")
            return None
        if not stat.S_ISDIR(after.st_mode) or not _same_member(before, after):
            _error(errors, f"{label} changed during validation: {rel}")
            return None
        if os.listdir not in os.supports_fd:
            _error(errors, f"platform cannot safely enumerate package directory: {rel}")
            return None
        try:
            return sorted(os.listdir(descriptor))
        except OSError:
            _error(errors, f"{label} is unreadable: {rel}")
            return None
    finally:
        os.close(descriptor)


def _load_json_package_file(
    root: Path,
    path: Path,
    errors: list[str],
    label: str = "manifest",
    *,
    required: bool = True,
    missing_message: str | None = None,
) -> dict:
    result = _read_regular_package_bytes(
        root,
        path,
        label,
        errors,
        required=required,
        missing_message=missing_message,
    )
    if result is None:
        return {}
    data, _ = result
    return _load_json_bytes(data, errors, label)


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
        return None
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

    candidate = root / relative
    try:
        candidate.relative_to(root)
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
        return _real_package_directory(
            root,
            candidate,
            f"manifest {field} directory",
            errors,
            missing_message=f"manifest {field} directory is missing: ./{expected}",
        )
    return _regular_package_file(
        root,
        candidate,
        f"manifest {field} file",
        errors,
        missing_message=f"manifest {field} file is missing: ./{expected}",
    )


def _validate_codex_plugin_directory(root: Path, errors: list[str]) -> None:
    directory = root / ".codex-plugin"
    entries = _list_real_package_directory(root, directory, ".codex-plugin directory", errors, required=False)
    if entries is None:
        return
    for name in entries:
        if name != "plugin.json":
            _error(
                errors,
                f".codex-plugin may contain plugin.json only; move or remove: .codex-plugin/{name}",
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


def _svg_size(data: bytes) -> tuple[float, float]:
    root = ET.fromstring(data.decode("utf-8"))
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


def _image_size(suffix: str, data: bytes) -> tuple[float, float]:
    if suffix == ".svg":
        return _svg_size(data)
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
    suffix = candidate.suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
        _error(errors, f"interface.{field} image format is unsupported: {value}")
        return
    result = _read_regular_package_bytes(root, candidate, f"interface.{field} asset", errors, max_bytes=MAX_IMAGE)
    if result is None:
        return
    data, _ = result
    try:
        width, height = _image_size(suffix, data)
    except Exception as exc:
        _error(errors, f"interface.{field} image unreadable: {value}: {exc}")
        return
    if width != height:
        _error(errors, f"interface.{field} image must be square: {value}")
    if width < 48 or height < 48:
        _error(errors, f"interface.{field} image dimensions must be at least 48x48: {value}")
    if suffix != ".svg" and (width > 4096 or height > 4096):
        _error(errors, f"interface.{field} raster dimensions exceed 4096x4096: {value}")


class _YamlError(ValueError):
    def __init__(self, kind: str, message: str = "") -> None:
        self.kind = kind
        super().__init__(message or kind)


_YAML_NULL = {"~", "null", "Null", "NULL"}
_YAML_TRUE = {"true", "True", "TRUE"}
_YAML_FALSE = {"false", "False", "FALSE"}
_PLAIN_INT = re.compile(r"-?(?:0|[1-9]\d*)")
_PLAIN_FLOAT = re.compile(r"-?(?:0|[1-9]\d*)\.\d+(?:[eE][-+]?\d+)?")
_MISSING = object()
_BLOCK_INDICATOR = re.compile(r"^([|>][+-]?)(?:\s+#.*)?\s*$")


def _strip_plain_comment(text: str) -> str:
    if text.startswith("#"):
        return ""
    idx = text.find(" #")
    return text[:idx].rstrip() if idx >= 0 else text.rstrip()


def _parse_quoted(text: str) -> tuple[str, str]:
    if not text or text[0] not in {"'", '"'}:
        raise _YamlError("malformed", "quoted scalar required")
    quote = text[0]
    i = 1
    out: list[str] = []
    if quote == "'":
        while i < len(text):
            char = text[i]
            if char == "'":
                if i + 1 < len(text) and text[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                return "".join(out), text[i + 1:]
            out.append(char)
            i += 1
        raise _YamlError("malformed", "unclosed single quote")
    while i < len(text):
        char = text[i]
        if char == '"':
            return "".join(out), text[i + 1:]
        if char == "\\":
            if i + 1 >= len(text):
                raise _YamlError("malformed", "truncated escape")
            nxt = text[i + 1]
            escapes = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"'}
            if nxt not in escapes:
                raise _YamlError("malformed", "unsupported escape")
            out.append(escapes[nxt])
            i += 2
            continue
        out.append(char)
        i += 1
    raise _YamlError("malformed", "unclosed double quote")


def _skip_flow_ws(text: str, index: int) -> int:
    while index < len(text) and text[index] in " ":
        index += 1
    return index


def _reject_yaml_prefix(text: str, index: int) -> None:
    if index < len(text) and text[index] in "!&*":
        if text[index] == "!":
            raise _YamlError("tag")
        raise _YamlError("malformed", "anchors and aliases are not allowed")


def _parse_flow_value(text: str, index: int) -> tuple[object, int]:
    index = _skip_flow_ws(text, index)
    if index >= len(text):
        raise _YamlError("malformed", "missing flow value")
    _reject_yaml_prefix(text, index)
    char = text[index]
    if char == "[":
        return _parse_flow_seq(text, index)
    if char == "{":
        return _parse_flow_map(text, index)
    if char in {"'", '"'}:
        value, rest = _parse_quoted(text[index:])
        return value, index + len(text[index:]) - len(rest)
    start = index
    while index < len(text) and text[index] not in ",]}#":
        index += 1
    return _interpret_plain(text[start:index].strip()), index


def _parse_flow_seq(text: str, index: int) -> tuple[list[object], int]:
    if index >= len(text) or text[index] != "[":
        raise _YamlError("malformed", "sequence must start with [")
    index += 1
    items: list[object] = []
    expect_value = True
    while True:
        index = _skip_flow_ws(text, index)
        if index >= len(text) or text[index] == "#":
            raise _YamlError("malformed", "unterminated sequence")
        if text[index] == "]":
            return items, index + 1
        if text[index] == ",":
            if expect_value and items:
                raise _YamlError("malformed", "empty sequence item")
            expect_value = True
            index += 1
            continue
        if not expect_value:
            raise _YamlError("malformed", "missing comma in sequence")
        value, index = _parse_flow_value(text, index)
        items.append(value)
        expect_value = False


def _parse_flow_map(text: str, index: int) -> tuple[dict[str, object], int]:
    if index >= len(text) or text[index] != "{":
        raise _YamlError("malformed", "mapping must start with {")
    index += 1
    result: dict[str, object] = {}
    expect_pair = True
    while True:
        index = _skip_flow_ws(text, index)
        if index >= len(text) or text[index] == "#":
            raise _YamlError("malformed", "unterminated mapping")
        if text[index] == "}":
            return result, index + 1
        if text[index] == ",":
            expect_pair = True
            index += 1
            continue
        if not expect_pair:
            raise _YamlError("malformed", "missing comma in mapping")
        key, index = _parse_flow_key(text, index)
        index = _skip_flow_ws(text, index)
        if index >= len(text) or text[index] != ":":
            raise _YamlError("malformed", "mapping pair requires a colon")
        value, index = _parse_flow_value(text, index + 1)
        if key in result:
            raise _YamlError("malformed", "duplicate key")
        result[key] = value
        expect_pair = False


def _parse_flow_key(text: str, index: int) -> tuple[str, int]:
    index = _skip_flow_ws(text, index)
    _reject_yaml_prefix(text, index)
    if index < len(text) and text[index] in {"'", '"'}:
        key, rest = _parse_quoted(text[index:])
        return key, index + len(text[index:]) - len(rest)
    start = index
    while index < len(text) and text[index] not in ":,}#":
        index += 1
    key = text[start:index].strip()
    if not key:
        raise _YamlError("malformed", "empty mapping key")
    return key, index


def _interpret_plain(value: str) -> object:
    if value in _YAML_NULL or value == "":
        return None
    if value in _YAML_TRUE:
        return True
    if value in _YAML_FALSE:
        return False
    if _PLAIN_INT.fullmatch(value):
        return int(value)
    if _PLAIN_FLOAT.fullmatch(value):
        return float(value)
    return value


def _parse_value_token(token: str) -> object:
    token = token.strip()
    if not token or token.startswith("#"):
        return None
    _reject_yaml_prefix(token, 0)
    if token[0] in {"'", '"'}:
        value, rest = _parse_quoted(token)
        leftover = _strip_plain_comment(rest).strip()
        if leftover:
            raise _YamlError("malformed", "unexpected content after quoted scalar")
        return value
    if token[0] == "[":
        value, index = _parse_flow_seq(token, 0)
        leftover = _strip_plain_comment(token[index:]).strip()
        if leftover:
            raise _YamlError("malformed", "unexpected content after sequence")
        return value
    if token[0] == "{":
        value, index = _parse_flow_map(token, 0)
        leftover = _strip_plain_comment(token[index:]).strip()
        if leftover:
            raise _YamlError("malformed", "unexpected content after mapping")
        return value
    return _interpret_plain(_strip_plain_comment(token).strip())


def _split_mapping_line(content: str) -> tuple[str, str] | None:
    if not content or content.startswith(("- ", "-", "#", "[", "{")):
        return None
    if content[0] in {"'", '"'}:
        key, rest = _parse_quoted(content)
        rest = rest.lstrip(" ")
        if not rest.startswith(":"):
            return None
        return key, rest[1:]
    for index, char in enumerate(content):
        if char == ":" and (index + 1 == len(content) or content[index + 1] in " #"):
            key = content[:index].rstrip()
            if not key:
                raise _YamlError("malformed", "empty mapping key")
            return key, content[index + 1:]
    return None


class _RestrictedYamlParser:
    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.i = 0

    def skip_blank_comments(self) -> None:
        while self.i < len(self.lines):
            stripped = self.lines[self.i].strip()
            if stripped == "" or stripped.startswith("#"):
                self.i += 1
                continue
            break

    def current_indent(self) -> int:
        raw = self.lines[self.i]
        return len(raw) - len(raw.lstrip(" "))

    def parse_node(self, min_indent: int, *, allow_empty: bool = False) -> object:
        self.skip_blank_comments()
        if self.i >= len(self.lines):
            if allow_empty:
                return None
            raise _YamlError("malformed", "missing YAML value")
        indent = self.current_indent()
        if indent < min_indent:
            if allow_empty:
                return None
            raise _YamlError("malformed", "missing YAML value")
        content = self.lines[self.i][indent:]
        if content == "-" or content.startswith("- "):
            return self.parse_block_seq(indent)
        if _split_mapping_line(content) is not None:
            return self.parse_block_map(indent)
        self.i += 1
        return _parse_value_token(content)

    def parse_block_map(self, indent: int) -> dict[str, object]:
        result: dict[str, object] = {}
        while self.i < len(self.lines):
            self.skip_blank_comments()
            if self.i >= len(self.lines):
                break
            line_indent = self.current_indent()
            if line_indent < indent:
                break
            if line_indent > indent:
                raise _YamlError("malformed", "unexpected indentation")
            content = self.lines[self.i][line_indent:]
            pair = _split_mapping_line(content)
            if pair is None:
                break
            key, rest = pair
            if key in result:
                raise _YamlError("malformed", "duplicate key")
            self.i += 1
            indicator = _BLOCK_INDICATOR.fullmatch(rest.strip())
            if indicator:
                result[key] = self.parse_block_scalar(indicator.group(1), indent)
            elif rest.strip() == "" or rest.strip().startswith("#"):
                self.skip_blank_comments()
                if self.i < len(self.lines) and self.current_indent() > indent:
                    result[key] = self.parse_node(indent + 1)
                else:
                    result[key] = None
            else:
                result[key] = _parse_value_token(rest)
        if not result:
            raise _YamlError("malformed", "empty mapping")
        return result

    def parse_block_seq(self, indent: int) -> list[object]:
        items: list[object] = []
        while self.i < len(self.lines):
            self.skip_blank_comments()
            if self.i >= len(self.lines):
                break
            line_indent = self.current_indent()
            if line_indent != indent:
                break
            content = self.lines[self.i][line_indent:]
            if content != "-" and not content.startswith("- "):
                break
            rest = "" if content == "-" else content[2:]
            self.i += 1
            indicator = _BLOCK_INDICATOR.fullmatch(rest.strip())
            if indicator:
                items.append(self.parse_block_scalar(indicator.group(1), indent))
            elif rest.strip() == "" or rest.strip().startswith("#"):
                self.skip_blank_comments()
                if self.i < len(self.lines) and self.current_indent() > indent:
                    items.append(self.parse_node(indent + 1))
                else:
                    items.append(None)
            else:
                items.append(_parse_value_token(rest))
        return items

    def parse_block_scalar(self, indicator: str, parent_indent: int) -> str:
        chunks: list[str] = []
        content_indent: int | None = None
        while self.i < len(self.lines):
            raw = self.lines[self.i]
            if raw.strip() == "":
                chunks.append("")
                self.i += 1
                continue
            line_indent = len(raw) - len(raw.lstrip(" "))
            if line_indent <= parent_indent:
                break
            if content_indent is None:
                content_indent = line_indent
            if line_indent < content_indent:
                break
            chunks.append(raw[content_indent:])
            self.i += 1
        while chunks and chunks[-1] == "":
            chunks.pop()
        if indicator.startswith(">"):
            return " ".join(chunk for chunk in chunks if chunk != "")
        return "\n".join(chunks)


def _parse_restricted_yaml(text: str) -> object:
    if "\t" in text:
        raise _YamlError("malformed", "tabs are not allowed")
    parser = _RestrictedYamlParser(text.splitlines())
    value = parser.parse_node(0, allow_empty=True)
    parser.skip_blank_comments()
    if parser.i < len(parser.lines):
        raise _YamlError("malformed", "unexpected trailing content")
    return value


def _normalize_skill_text(value: str) -> str:
    return " ".join(value.split())


def _parse_skill_frontmatter(text: str, skill_dir: str, errors: list[str]) -> tuple[str | None, str | None] | None:
    if not text.startswith("---\n"):
        _error(errors, f"skill_frontmatter_missing: SKILL.md must start with YAML front matter: {skill_dir}")
        return None
    end = text.find("\n---", 4)
    if end < 0:
        _error(errors, f"skill_frontmatter_unclosed: SKILL.md YAML front matter must end with ---: {skill_dir}")
        return None
    try:
        parsed = _parse_restricted_yaml(text[4:end])
    except _YamlError as exc:
        if exc.kind == "tag":
            _error(errors, f"skill_frontmatter_yaml_malformed: SKILL.md frontmatter rejects explicit YAML tags: {skill_dir}")
        else:
            _error(errors, f"skill_frontmatter_yaml_malformed: SKILL.md frontmatter is malformed YAML: {skill_dir}")
        return None
    if not isinstance(parsed, dict):
        _error(errors, f"skill_frontmatter_wrong_type: SKILL.md frontmatter must contain a YAML mapping: {skill_dir}")
        return None

    name = parsed.get("name", _MISSING)
    description = parsed.get("description", _MISSING)
    skill_name: str | None = None
    skill_description: str | None = None
    if name is _MISSING:
        _error(errors, f"skill name is required: {skill_dir}")
    elif not isinstance(name, str):
        _error(errors, f"skill name must be a string: {skill_dir}")
    else:
        skill_name = _normalize_skill_text(name)
        if not skill_name:
            _error(errors, f"skill name is required: {skill_dir}")
            skill_name = None
    if description is _MISSING:
        _error(errors, f"skill description is required: {skill_dir}")
    elif not isinstance(description, str):
        _error(errors, f"skill description must be a string: {skill_dir}")
    else:
        skill_description = _normalize_skill_text(description)
        if not skill_description:
            _error(errors, f"skill description is required: {skill_dir}")
            skill_description = None
    return skill_name, skill_description


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


def _validate_skill_agent_metadata(plugin_root: Path, skill_dir: Path, errors: list[str], warnings: list[str]) -> None:
    path = skill_dir / "agents" / "openai.yaml"
    rel = f"skills/{skill_dir.name}/agents/openai.yaml"
    text = _read_regular_package_text(plugin_root, path, rel, errors, required=False)
    if text is None:
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
            if candidate is not None:
                _verify_regular_package_file(plugin_root, candidate, f"{rel} interface.{field} asset", errors)

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


def _validate_app_manifest(data: dict, errors: list[str]) -> None:
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


def _validate_mcp_manifest(data: dict, errors: list[str]) -> None:
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
                member = path.lstat()
            except OSError as exc:
                _error(errors, f"unreadable plugin member {rel}: {exc}")
                continue
            if stat.S_ISLNK(member.st_mode):
                _error(errors, f"symlink is not allowed in public plugin: {rel}")
                continue
            if not stat.S_ISREG(member.st_mode):
                _error(errors, f"unsupported plugin member type: {rel}")
                continue
            size = member.st_size
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
                result = _read_regular_package_bytes(root, path, f"plugin text file {rel}", errors, max_bytes=1024 * 1024)
                if result is None:
                    continue
                data, _ = result
                try:
                    text = data.decode("utf-8")
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
    manifest = _load_json_package_file(
        root,
        manifest_path,
        errors,
        "manifest",
        missing_message="missing .codex-plugin/plugin.json",
    )

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
        mcp_data = _load_json_package_file(root, root / ".mcp.json", errors, ".mcp.json")
        _validate_mcp_manifest(mcp_data, errors)
    elif "mcpServers" not in manifest and (root / ".mcp.json").exists():
        _warning(warnings, "root .mcp.json is ignored because manifest mcpServers is not set to ./.mcp.json")
    if apps_declared:
        app_data = _load_json_package_file(root, root / ".app.json", errors, ".app.json")
        _validate_app_manifest(app_data, errors)
    elif "apps" not in manifest and (root / ".app.json").exists():
        _warning(warnings, "root .app.json is ignored because manifest apps is not set to ./.app.json")

    if "hooks" in manifest:
        hook_value = manifest.get("hooks")
        if isinstance(hook_value, str):
            hook_path = _relative_file_path(root, "manifest hooks", hook_value, errors)
            if hook_path is not None:
                _verify_regular_package_file(
                    root,
                    hook_path,
                    "manifest hooks file",
                    errors,
                    missing_message=f"manifest hooks file is missing: {hook_value}",
                )
        elif isinstance(hook_value, list):
            for index, item in enumerate(hook_value):
                if isinstance(item, str):
                    hook_path = _relative_file_path(root, f"manifest hooks[{index}]", item, errors)
                    if hook_path is not None:
                        _verify_regular_package_file(
                            root,
                            hook_path,
                            f"manifest hooks[{index}] file",
                            errors,
                            missing_message=f"manifest hooks file is missing: {item}",
                        )
                elif not isinstance(item, dict):
                    _error(errors, f"manifest hooks[{index}] must be a path or inline hooks object")
        elif not isinstance(hook_value, dict):
            _error(errors, "manifest hooks must be a path, list, or inline hooks object")

    has_mcp = mcp_declared or apps_declared
    skill_path_value = manifest.get("skills", "./skills/")
    has_skills = False
    skills: list[str] = []
    skill_names: set[str] = set()
    skill_root: Path | None = None
    if isinstance(skill_path_value, str):
        if not skill_path_value:
            _error(errors, "manifest skills must be a non-empty relative path string")
        else:
            invalid_skill_path = False
            if skill_path_value != skill_path_value.strip() or _has_control(skill_path_value):
                _error(errors, "manifest skills path contains unsupported whitespace or control characters")
                invalid_skill_path = True
            if not skill_path_value.startswith("./"):
                _error(errors, f"manifest skills path must start with ./: {skill_path_value}")
                invalid_skill_path = True
            relative = skill_path_value[2:] if skill_path_value.startswith("./") else skill_path_value
            normalized = relative.replace("\\", "/")
            if ".." in normalized.split("/"):
                _error(errors, f"manifest skills path contains unsafe .. traversal: {skill_path_value}")
                invalid_skill_path = True
            if relative.rstrip("/") != "skills":
                _error(errors, f"manifest skills path must resolve to ./skills/: {skill_path_value}")
                invalid_skill_path = True
            if not invalid_skill_path:
                skill_root = root / "skills"

        if skill_root is not None:
            entries = _list_real_package_directory(
                root,
                skill_root,
                "manifest skills directory",
                errors,
                required="skills" in manifest,
                missing_message=f"manifest skills path is missing: {skill_path_value}",
            )
            if entries is not None:
                for item_name in entries:
                    item = skill_root / item_name
                    member = _package_member_stat(root, item, f"skill entry skills/{item_name}", errors)
                    if member is None or not stat.S_ISDIR(member.st_mode):
                        _error(errors, f"skills direct child must be a real directory containing SKILL.md; found: skills/{item_name}")
                        continue
                    directory = item
                    if directory.name.startswith("."):
                        _error(errors, f"skill directory must not be hidden: {directory.name}")
                        continue
                    definition = directory / "SKILL.md"
                    skill_text = _read_regular_package_text(
                        root,
                        definition,
                        "skill definition",
                        errors,
                        missing_message=f"skill directory is missing SKILL.md: {directory.name}",
                    )
                    if skill_text is None:
                        continue
                    try:
                        parsed = _parse_skill_frontmatter(skill_text, directory.name, errors)
                    except Exception as exc:
                        _error(errors, f"skill definition unreadable: {directory.name}: {exc}")
                        continue
                    if parsed is None:
                        continue
                    skill_name, skill_description = parsed
                    if skill_name:
                        if skill_name in skill_names:
                            _error(errors, f"skill name must be unique within plugin: {skill_name}")
                        else:
                            skill_names.add(skill_name)
                            skills.append(skill_name)
                    if skill_description and len(skill_description) > 1024:
                        _error(errors, f"skill description exceeds 1024 characters: {directory.name}")
                    front_end = skill_text.find("\n---", 4)
                    body = skill_text[front_end + 4:].strip() if front_end >= 0 else ""
                    if not body:
                        _error(errors, f"skill body must not be empty: {directory.name}")
                    if isinstance(name, str) and skill_name and len(f"{name}:{skill_name}") > 64:
                        _error(errors, f"combined plugin and skill identity exceeds 64 characters: {skill_name}")
                    _validate_skill_agent_metadata(root, directory, errors, warnings)
                has_skills = bool(skills)
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
                if candidate is not None:
                    _verify_regular_package_file(root, candidate, f"interface.screenshots[{index}] asset", errors)

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

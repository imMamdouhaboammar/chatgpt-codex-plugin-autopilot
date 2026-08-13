#!/usr/bin/env python3
"""Build a deterministic archive-root ZIP after generic plugin validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import zipfile
from pathlib import Path

# Prevent transient bytecode inside the plugin root from entering deterministic archives.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_plugin import validate_plugin  # noqa: E402

FIXED_TIME = (1980, 1, 1, 0, 0, 0)
MAX_ARCHIVE = 100 * 1000 * 1000


def archive_size_within_limit(size: int) -> bool:
    return 0 <= size <= MAX_ARCHIVE


def _collect(root: Path) -> tuple[list[str], list[str]]:
    files: list[str] = []
    directories: set[str] = set()
    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in sorted(dirs):
            path = current_path / name
            if path.is_symlink():
                raise ValueError(f"symlink is not packageable: {path.relative_to(root)}")
        for name in sorted(names):
            path = current_path / name
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"unsupported package member: {path.relative_to(root)}")
            rel = path.relative_to(root).as_posix()
            files.append(rel)
            parts = rel.split("/")[:-1]
            for index in range(1, len(parts) + 1):
                directories.add("/".join(parts[:index]) + "/")
    return sorted(directories), sorted(files)


def build_archive(plugin_root: str, output_path: str, exclusions: list[str] | None = None) -> dict:
    root = Path(plugin_root).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("output ZIP must live outside the plugin root")

    report = validate_plugin(str(root), exclusions or [])
    if not report["ok"]:
        raise ValueError("plugin validation failed: " + "; ".join(report["errors"]))
    directories, files = _collect(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for rel in directories:
                info = zipfile.ZipInfo(rel, FIXED_TIME)
                info.create_system = 3
                info.external_attr = (stat.S_IFDIR | 0o755) << 16
                archive.writestr(info, b"")
            for rel in files:
                path = root.joinpath(*rel.split("/"))
                info = zipfile.ZipInfo(rel, FIXED_TIME)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                executable = bool(path.stat().st_mode & stat.S_IXUSR)
                mode = 0o755 if executable else 0o644
                info.external_attr = (stat.S_IFREG | mode) << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        if not archive_size_within_limit(temporary.stat().st_size):
            raise ValueError(f"compressed ZIP exceeds 100 MB: {temporary.stat().st_size}")
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return {
        "ok": True,
        "outputPath": str(output),
        "sha256": digest,
        "version": report["version"],
        "architecture": report["architecture"],
        "skills": len(report["skills"]),
        "entries": len(directories) + len(files),
        "bytes": output.stat().st_size,
        "exclusions": report["exclusions"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root")
    parser.add_argument("output_zip")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--exclude", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        result = build_archive(args.plugin_root, args.output_zip, args.exclude)
    except Exception as exc:
        if args.as_json:
            print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2, sort_keys=True))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"built {result['outputPath']} sha256={result['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

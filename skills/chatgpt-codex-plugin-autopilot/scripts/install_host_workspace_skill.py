#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL_NAME = "host-workspace-operator"


def source_skill() -> Path:
    return Path(__file__).resolve().parents[2] / SKILL_NAME


def files_under(root: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix().lower()):
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def install(plugin_root: Path) -> tuple[bool, str]:
    root = plugin_root.expanduser().resolve()
    if not root.is_dir():
        return False, f"target plugin root is not a directory: {root}"

    source = source_skill()
    if not (source / "SKILL.md").is_file():
        return False, f"bundled source Skill is missing: {source}"

    skills_root = root / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)
    target = skills_root / SKILL_NAME

    if target.exists():
        if not target.is_dir():
            return False, f"refusing to overwrite non-directory target: {target}"
        if files_under(target) == files_under(source):
            return True, f"{SKILL_NAME} already current"
        return False, f"refusing to overwrite customized Skill: {target}"

    target.mkdir(parents=True)
    for relative, data in files_under(source).items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)

    return True, f"installed {SKILL_NAME} into {target}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install Plugin Autopilot's host-native workspace operations Skill into a target Plugin."
    )
    parser.add_argument("plugin_root")
    args = parser.parse_args()

    ok, message = install(Path(args.plugin_root))
    stream = sys.stdout if ok else sys.stderr
    print(message, file=stream)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

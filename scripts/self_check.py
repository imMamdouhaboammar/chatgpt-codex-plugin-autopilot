#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_REL = Path("skills/chatgpt-codex-plugin-autopilot")
SURFACE = [
    Path(".codex-plugin"), Path("assets"), Path("skills"),
    Path("README.md"), Path("LICENSE"), Path("PRIVACY.md"),
    Path("TERMS.md"), Path("SUPPORT.md"), Path("SECURITY.md"),
]


def stage_plugin(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    for rel in SURFACE:
        source = ROOT / rel
        target = destination / rel
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        else:
            raise FileNotFoundError(f"missing release surface member: {rel}")
    return destination


def validate_stage(stage: Path) -> dict:
    validator = stage / SKILL_REL / "scripts/validate_plugin.py"
    proc = subprocess.run(
        ["python3", str(validator), str(stage), "--json"],
        text=True, capture_output=True,
    )
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(proc.stderr or proc.stdout or str(exc)) from exc
    if proc.returncode != 0 or not report.get("ok"):
        raise RuntimeError("plugin validation failed: " + "; ".join(report.get("errors", [])))
    return report


def run_check() -> dict:
    with tempfile.TemporaryDirectory(prefix="plugin-autopilot-check-") as temp:
        stage = stage_plugin(Path(temp) / "plugin")
        report = validate_stage(stage)
        return {
            "ok": True,
            "name": report["name"],
            "version": report["version"],
            "architecture": report["architecture"],
            "skills": len(report["skills"]),
            "entries": report["entries"],
            "uncompressedBytes": report["uncompressedBytes"],
            "warnings": report["warnings"],
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = run_check()
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2, sort_keys=True))
        else:
            print(f"self-check: FAIL: {exc}")
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"self-check: PASS {report['name']} {report['version']} skills={report['skills']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""GitHub Action entrypoint for ChatGPT & Codex Plugin Autopilot."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Prevent bytecode generation during action execution
sys.dont_write_bytecode = True

ROOT = Path(os.environ.get("ACTION_PATH") or Path(__file__).resolve().parents[1])
SCRIPTS_DIR = ROOT / "skills/chatgpt-codex-plugin-autopilot/scripts"


def write_output(name: str, value: str | int | bool) -> None:
    """Write an output key-value pair to GITHUB_OUTPUT."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if not output_file:
        return
    text = str(value)
    if "\n" in text:
        delimiter = "EOF_AUTOPILOT"
        line = f"{name}<<{delimiter}\n{text}\n{delimiter}\n"
    else:
        line = f"{name}={text}\n"
    with open(output_file, "a", encoding="utf-8") as fh:
        fh.write(line)


def write_summary(markdown_text: str) -> None:
    """Append formatted markdown text to GITHUB_STEP_SUMMARY."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return
    with open(summary_file, "a", encoding="utf-8") as fh:
        fh.write(markdown_text.rstrip() + "\n\n")


def run_analyzer(target_dir: Path) -> dict:
    """Run analyze_repo.py on the target directory."""
    analyzer = SCRIPTS_DIR / "analyze_repo.py"
    cmd = [sys.executable, str(analyzer), str(target_dir), "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    try:
        data = json.loads(proc.stdout)
        if "ok" not in data:
            data["ok"] = bool(proc.returncode == 0 and not data.get("errors"))
        return data
    except Exception as exc:
        return {
            "ok": False,
            "errors": [f"analyzer execution failed: {proc.stderr or proc.stdout or exc}"],
            "skills": [],
            "candidates": [],
        }


def run_validator(target_dir: Path) -> dict:
    """Run validation on the target directory, using self_check if available or validate_plugin."""
    self_check = target_dir / "scripts/self_check.py"
    if self_check.is_file():
        cmd = [sys.executable, str(self_check), "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(target_dir))
        try:
            return json.loads(proc.stdout)
        except Exception as exc:
            return {"ok": False, "errors": [f"self_check execution failed: {proc.stderr or proc.stdout or exc}"]}

    validator = SCRIPTS_DIR / "validate_plugin.py"
    cmd = [sys.executable, str(validator), str(target_dir), "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    try:
        data = json.loads(proc.stdout)
        if proc.returncode != 0 and "ok" not in data:
            data["ok"] = False
        return data
    except Exception as exc:
        return {
            "ok": False,
            "errors": [f"validator execution failed: {proc.stderr or proc.stdout or exc}"],
            "warnings": [],
            "skills": [],
        }


def run_packager(target_dir: Path, output_dir: Path) -> dict:
    """Package the target directory into a verified release ZIP."""
    output_dir.mkdir(parents=True, exist_ok=True)
    custom_build_script = target_dir / "scripts/build_release.py"
    if custom_build_script.is_file():
        cmd = [sys.executable, str(custom_build_script), "--out-dir", str(output_dir), "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(target_dir))
        try:
            return json.loads(proc.stdout)
        except Exception as exc:
            return {"ok": False, "errors": [f"build_release failed: {proc.stderr or proc.stdout or exc}"]}

    manifest_path = target_dir / ".codex-plugin/plugin.json"
    if not manifest_path.is_file():
        return {"ok": False, "errors": [f"missing manifest at {manifest_path}"]}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        name = manifest.get("name", "plugin")
        version = manifest.get("version", "0.1.0")
    except Exception as exc:
        return {"ok": False, "errors": [f"failed to read manifest: {exc}"]}

    archive_path = output_dir / f"{name}-{version}.zip"
    packager = SCRIPTS_DIR / "package_plugin.py"
    cmd = [sys.executable, str(packager), str(target_dir), str(archive_path), "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    try:
        result = json.loads(proc.stdout)
        if result.get("ok"):
            result["archive"] = result.get("outputPath", str(archive_path))
        return result
    except Exception as exc:
        return {"ok": False, "errors": [f"package_plugin failed: {proc.stderr or proc.stdout or exc}"]}


def format_summary_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format a GitHub Flavored Markdown table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))
    header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    sep_line = "| " + " | ".join("-" * col_widths[i] for i in range(len(headers))) + " |"
    data_lines = [
        "| " + " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"
        for row in rows
    ]
    return "\n".join([header_line, sep_line] + data_lines)


def render_markdown_summary(mode: str, report: dict, target_dir: Path, arch_str: str) -> str:
    """Generate a rich GitHub Step Summary."""
    ok = report.get("ok", False)
    status_emoji = "✅" if ok else "❌"
    status_text = "PASSED" if ok else "FAILED"

    lines = [
        f"## {status_emoji} ChatGPT / Codex Plugin Autopilot Summary",
        "",
        f"- **Mode:** `{mode}`",
        f"- **Target Directory:** `{target_dir}`",
        f"- **Status:** **{status_text}**",
        f"- **Architecture:** `{arch_str}`",
    ]

    skills = report.get("skills", [])
    if isinstance(skills, list):
        lines.append(f"- **Skills Count:** {len(skills)}")
    elif isinstance(skills, int):
        lines.append(f"- **Skills Count:** {skills}")

    if "archive" in report:
        lines.append(f"- **Release Archive:** `{report['archive']}`")
        if "sha256" in report:
            lines.append(f"- **SHA-256 Checksum:** `{report['sha256']}`")
        if "bytes" in report:
            kb = round(report["bytes"] / 1024, 2)
            lines.append(f"- **Archive Size:** {kb} KB ({report['bytes']} bytes)")

    lines.append("")

    # Errors section
    errors = report.get("errors", [])
    if errors:
        lines.extend([
            "### ❌ Errors Encountered",
            "",
        ])
        for err in errors:
            lines.append(f"- {err}")
        lines.append("")

    # Warnings section
    warnings = report.get("warnings", [])
    if warnings:
        lines.extend([
            "### ⚠️ Warnings",
            "",
        ])
        for warn in warnings:
            lines.append(f"- {warn}")
        lines.append("")

    # Candidates table (from analyzer)
    candidates = report.get("candidates", [])
    if candidates:
        lines.extend([
            "### 🔍 Discovered Workflow Candidates",
            "",
        ])
        headers = ["Kind", "Slug", "Path", "Target Action"]
        rows = [
            [str(c.get("kind", "")), str(c.get("slug", "")), str(c.get("path", "")), str(c.get("recommendedTarget", ""))]
            for c in candidates[:25]
        ]
        lines.append(format_summary_table(headers, rows))
        if len(candidates) > 25:
            lines.append(f"\n*(and {len(candidates) - 25} more candidates)*")
        lines.append("")

    # Skills table (from validator)
    if isinstance(skills, list) and skills and isinstance(skills[0], dict):
        lines.extend([
            "### 📦 Included Skills",
            "",
        ])
        headers = ["Skill Name", "Path", "Description"]
        rows = []
        for s in skills:
            name = s.get("name", "")
            path = s.get("path", "")
            desc = s.get("description", "")[:60] + "..." if len(s.get("description", "")) > 60 else s.get("description", "")
            rows.append([name, path, desc])
        lines.append(format_summary_table(headers, rows))
        lines.append("")

    lines.extend([
        "---",
        "*Powered by [ChatGPT & Codex Plugin Autopilot](https://github.com/imMamdouhaboammar/chatgpt-codex-plugin-autopilot)*",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GitHub Action Entrypoint for Plugin Autopilot")
    parser.add_argument("--path", default=os.environ.get("INPUT_PATH", "."))
    parser.add_argument("--action", default=os.environ.get("INPUT_ACTION", "auto"))
    parser.add_argument("--output-dir", default=os.environ.get("INPUT_OUTPUT_DIR", "dist"))
    parser.add_argument("--fail-on-error", default=os.environ.get("INPUT_FAIL_ON_ERROR", "true"))
    parser.add_argument("--summary", default=os.environ.get("INPUT_SUMMARY", "true"))
    args = parser.parse_args(argv)

    target_dir = Path(args.path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    fail_on_error = str(args.fail_on_error).lower() in ("true", "1", "yes")
    gen_summary = str(args.summary).lower() in ("true", "1", "yes")
    action_mode = args.action.lower().strip()

    if not target_dir.exists():
        err_msg = f"Target directory does not exist: {target_dir}"
        print(f"Error: {err_msg}", file=sys.stderr)
        write_output("ok", "false")
        if gen_summary:
            write_summary(render_markdown_summary(action_mode, {"ok": False, "errors": [err_msg]}, target_dir, "unknown"))
        return 1 if fail_on_error else 0

    has_plugin_manifest = (target_dir / ".codex-plugin/plugin.json").is_file()

    report: dict = {}
    actual_mode = action_mode

    if action_mode == "auto":
        if has_plugin_manifest:
            actual_mode = "package"
        else:
            actual_mode = "analyze"

    if actual_mode == "analyze":
        report = run_analyzer(target_dir)
    elif actual_mode == "validate":
        report = run_validator(target_dir)
    elif actual_mode == "package":
        # Validate first
        val_report = run_validator(target_dir)
        if not val_report.get("ok"):
            report = val_report
        else:
            pkg_report = run_packager(target_dir, output_dir)
            report = {**val_report, **pkg_report}
            if not pkg_report.get("ok"):
                report["ok"] = False
    elif actual_mode == "build-directory-pack":
        packer = SCRIPTS_DIR / "build_directory_pack.py"
        listing_path = target_dir / "submission/listing.json"
        cmd = [sys.executable, str(packer), str(target_dir), "--json"]
        if listing_path.is_file():
            cmd.extend(["--listing", str(listing_path)])
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
        try:
            report = json.loads(proc.stdout)
        except Exception as exc:
            report = {"ok": False, "errors": [f"build_directory_pack failed: {proc.stderr or proc.stdout or exc}"]}
    else:
        report = {"ok": False, "errors": [f"Unknown action: {action_mode}"]}

    ok = report.get("ok", False)
    arch_raw = report.get("architecture", "unknown")
    if isinstance(arch_raw, dict):
        architecture = arch_raw.get("recommended", "skills-only")
    elif isinstance(arch_raw, str):
        architecture = arch_raw
    else:
        architecture = "unknown"

    skills = report.get("skills", [])
    skills_count = len(skills) if isinstance(skills, list) else int(skills) if isinstance(skills, int) else 0

    write_output("ok", "true" if ok else "false")
    write_output("architecture", architecture)
    write_output("skills_count", skills_count)
    if "archive" in report:
        write_output("plugin_path", report["archive"])
    elif "outputPath" in report:
        write_output("plugin_path", report["outputPath"])
    if "sha256" in report:
        write_output("sha256", report["sha256"])

    summary_md = render_markdown_summary(actual_mode, report, target_dir, architecture)
    if gen_summary:
        write_summary(summary_md)

    print(json.dumps(report, indent=2, sort_keys=True))

    if not ok and fail_on_error:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

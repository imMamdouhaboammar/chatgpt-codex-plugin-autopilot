#!/usr/bin/env python3
"""GitHub Action entrypoint for ChatGPT & Codex Plugin Autopilot."""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
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


# ---------------------------------------------------------------------------
# Auto-PR scaffolding
# ---------------------------------------------------------------------------

_LOGO_SVG_LIGHT = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <rect width="100" height="100" rx="16" fill="#0d1117"/>
  <text x="50" y="68" font-size="58" text-anchor="middle" fill="#58a6ff">⚡</text>
</svg>
"""

_LOGO_SVG_DARK = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <rect width="100" height="100" rx="16" fill="#ffffff"/>
  <text x="50" y="68" font-size="58" text-anchor="middle" fill="#0d1117">⚡</text>
</svg>
"""

_MARK_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <rect width="32" height="32" rx="6" fill="#0d1117"/>
  <text x="16" y="24" font-size="20" text-anchor="middle" fill="#58a6ff">⚡</text>
</svg>
"""


def _repo_slug(target_dir: Path) -> str:
    """Return the detected repo name (last dir component, lowercased, hyphened)."""
    github_repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in github_repo:
        return github_repo.split("/")[-1]
    return target_dir.name.lower().replace(" ", "-") or "my-plugin"


def _build_plugin_json(target_dir: Path, analysis: dict) -> dict:
    """Build a minimal plugin.json scaffold from analysis results."""
    repo = _repo_slug(target_dir)
    arch_raw = analysis.get("architecture", {})
    if isinstance(arch_raw, dict):
        arch = arch_raw.get("recommended", "skills-only")
    elif isinstance(arch_raw, str):
        arch = arch_raw
    else:
        arch = "skills-only"

    skills: list[str] = []
    for c in analysis.get("candidates", []):
        slug = c.get("slug", "")
        if slug and slug not in skills:
            skills.append(slug)

    github_repo = os.environ.get("GITHUB_REPOSITORY", "")
    repo_url = f"https://github.com/{github_repo}" if github_repo else f"https://github.com/your-org/{repo}"

    return {
        "schemaVersion": "1.0",
        "name": repo,
        "version": "0.1.0",
        "description": f"Auto-scaffolded ChatGPT & Codex plugin for {repo}",
        "architecture": arch,
        "skills": skills[:20],
        "entrypoint": "skills/",
        "assets": {
            "logoLight": "assets/logo-light.svg",
            "logoDark": "assets/logo-dark.svg",
            "mark": "assets/mark.svg",
        },
        "repository": repo_url,
        "license": "MIT",
        "_generatedBy": "chatgpt-codex-plugin-autopilot",
    }


def _build_listing_json(target_dir: Path, analysis: dict) -> dict:
    """Build submission/listing.json metadata packet."""
    repo = _repo_slug(target_dir)
    github_repo = os.environ.get("GITHUB_REPOSITORY", "")
    repo_url = f"https://github.com/{github_repo}" if github_repo else f"https://github.com/your-org/{repo}"
    dev_name = github_repo.split("/")[0] if "/" in github_repo else "Developer"

    candidates = analysis.get("candidates", [])
    skill_names = [c.get("slug") for c in candidates if c.get("slug")]
    if not skill_names:
        skill_names = [repo]

    capabilities = [f"{s.replace('-', ' ').title()} capability" for s in skill_names[:6]]

    return {
        "name": repo.replace("-", " ").title(),
        "subtitle": f"ChatGPT & Codex plugin for {repo}",
        "description": f"Automate workflows and execute capabilities for {repo}.",
        "category": "Developer Tools",
        "developerName": dev_name,
        "websiteURL": repo_url,
        "customerSupportURL": f"{repo_url}/issues",
        "privacyPolicyURL": f"{repo_url}/blob/main/PRIVACY.md",
        "termsOfServiceURL": f"{repo_url}/blob/main/TERMS.md",
        "version": "0.1.0",
        "packageName": repo,
        "capabilities": capabilities or ["Automated agentic workflow"],
        "starterPrompts": [
            f"Show available capabilities for {repo}.",
            f"Run automated tasks using {repo} plugin.",
            f"Explain how to configure workflows for {repo}.",
        ],
        "brand": {
            "concept": f"Clean ChatGPT & Codex plugin integration for {repo}.",
            "lightLogo": "./assets/logo-light.svg",
            "darkLogo": "./assets/logo-dark.svg",
            "composerIcon": "./assets/mark.svg",
        },
        "publisherVerification": {
            "required": True,
            "status": "verify-in-openai-platform-before-submission",
        },
        "note": "Repository-maintained evidence format for submission preparation.",
    }


def _build_workflow_yaml() -> str:
    """Build a starter GitHub Actions workflow for validating and packaging the plugin."""
    return """name: ChatGPT & Codex Plugin CI

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  validate-and-package:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Validate and Package Plugin
        uses: imMamdouhaboammar/chatgpt-codex-plugin-autopilot@v0.8.0
        with:
          action: 'auto'
          output-dir: 'dist'
          fail-on-error: 'true'

      - name: Upload Plugin Release Artifact
        uses: actions/upload-artifact@v4
        with:
          name: codex-plugin-package
          path: dist/
"""


def _skill_md_template(slug: str, source_path: str = "", reason: str = "") -> str:
    source_clause = f"\n> 📌 Derived from `{source_path}` ({reason})\n" if source_path else ""
    title = slug.replace("-", " ").title()
    return f"""---
name: {slug}
description: Automated skill instructions for {slug}. Update this description.
version: 0.1.0
---

# {title}

> ✏️ This skill was auto-scaffolded by **ChatGPT & Codex Plugin Autopilot**.{source_clause}
## Purpose

Describe what this skill does and when an AI agent should invoke it.

## Instructions

1. Describe the primary objective and prerequisites.
2. Outline step-by-step procedures the AI model should follow.
3. Detail guidelines, boundaries, and formatting rules.

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query     | string | No     | The query, instruction, or payload for this skill |

## Outputs

Describe the expected response, artifact format, or structured data output.
"""


def _pr_body(analysis: dict, scaffolded_files: list[str], branch: str, arch: str) -> str:
    candidates = analysis.get("candidates", [])
    next_actions = analysis.get("nextActions", [])
    skills_detected = len(candidates)

    lines = [
        "## 🤖 ChatGPT & Codex Plugin Autopilot — Scaffolded Plugin PR",
        "",
        "This Pull Request was automatically generated by **[ChatGPT & Codex Plugin Autopilot](https://github.com/imMamdouhaboammar/chatgpt-codex-plugin-autopilot)**.",
        "It establishes the complete plugin architecture, manifest, branding assets, skill scaffolds, and CI pipeline for this repository.",
        "",
        "---",
        "",
        "### 📊 Repository Analysis",
        "",
        "| Metric | Result |",
        "|:-------|:-------|",
        f"| **Architecture** | `{arch}` |",
        f"| **Workflow Candidates Found** | `{skills_detected}` |",
        f"| **Branch** | `{branch}` |",
        "",
        "### 📦 Scaffolded Files & Artifacts",
        "",
        "| File Path | Description |",
        "|:----------|:------------|",
    ]
    file_descriptions = {
        ".codex-plugin/plugin.json": "Plugin manifest declaring skills, brand identity, and runtime requirements",
        "assets/logo-light.svg": "Plugin logo for light backgrounds (100x100 SVG)",
        "assets/logo-dark.svg": "Plugin logo for dark backgrounds (100x100 SVG)",
        "assets/mark.svg": "Composer icon mark (32x32 SVG)",
        "submission/listing.json": "Plugin Directory submission metadata and reviewer listing packet",
        ".github/workflows/codex-plugin.yml": "Automated GitHub Actions CI/CD to validate and package plugin releases",
    }
    for f in scaffolded_files:
        desc = file_descriptions.get(f)
        if not desc:
            if f.startswith("skills/"):
                desc = "Reusable Agent Skill definition with inputs/outputs contract"
            else:
                desc = "Scaffolded plugin component"
        lines.append(f"| `{f}` | {desc} |")

    if next_actions:
        lines.extend([
            "",
            "### 🎯 Recommended Next Steps",
            "",
        ])
        for action in next_actions[:8]:
            if isinstance(action, dict):
                lines.append(f"- [ ] **{action.get('title', '')}**: {action.get('description', '')}")
            else:
                lines.append(f"- [ ] `{action}`: Review and customize as needed.")

    lines.extend([
        "",
        "### 🚀 Verification Checklist",
        "",
        "- [ ] Review plugin metadata in `.codex-plugin/plugin.json`",
        "- [ ] Replace placeholder SVGs in `assets/` with brand logos",
        "- [ ] Polish instructions in `skills/*/SKILL.md`",
        "- [ ] Review submission metadata in `submission/listing.json`",
        "- [ ] Merge this PR to activate the ChatGPT / Codex Plugin!",
        "",
        "---",
        "",
        "*Generated with ❤️ by [ChatGPT & Codex Plugin Autopilot](https://github.com/imMamdouhaboammar/chatgpt-codex-plugin-autopilot)*",
    ])
    return "\n".join(lines)


def create_pr_with_scaffold(
    target_dir: Path,
    analysis: dict,
    arch: str,
    pr_title: str,
    custom_branch: str = "",
) -> tuple[str | None, str | None, list[str]]:
    """
    Scaffold plugin files onto a new branch and open a PR in the calling repo.

    Returns (pr_url, pr_number, scaffolded_files).
    """
    repo = _repo_slug(target_dir)
    if custom_branch.strip():
        branch_name = custom_branch.strip()
    else:
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
        branch_name = f"plugin-autopilot/scaffold-{date_str}"

    print(f"[autopilot] Creating scaffold branch: {branch_name}")

    def _git(*args: str, cwd: Path = target_dir) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], capture_output=True, text=True, cwd=str(cwd))

    _git("config", "user.email", "github-actions[bot]@users.noreply.github.com")
    _git("config", "user.name", "github-actions[bot]")

    # Fetch fresh branch from remote if available
    _git("fetch", "--depth=1", "origin")

    # Get default branch
    default_branch_proc = _git("rev-parse", "--abbrev-ref", "HEAD")
    default_branch = default_branch_proc.stdout.strip() or "main"

    checkout_proc = _git("checkout", "-b", branch_name)
    if checkout_proc.returncode != 0:
        print(f"[autopilot] git checkout failed: {checkout_proc.stderr}", file=sys.stderr)
        return None, None, []

    scaffolded: list[str] = []

    def _write_scaffold(rel_path: str, content: str) -> None:
        full = target_dir / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        scaffolded.append(rel_path)

    # 1. Manifest
    if not (target_dir / ".codex-plugin/plugin.json").is_file():
        plugin_json = _build_plugin_json(target_dir, analysis)
        _write_scaffold(".codex-plugin/plugin.json", json.dumps(plugin_json, indent=2) + "\n")

    # 2. Assets (logos & mark)
    if not (target_dir / "assets/logo-light.svg").is_file():
        _write_scaffold("assets/logo-light.svg", _LOGO_SVG_LIGHT)
    if not (target_dir / "assets/logo-dark.svg").is_file():
        _write_scaffold("assets/logo-dark.svg", _LOGO_SVG_DARK)
    if not (target_dir / "assets/mark.svg").is_file():
        _write_scaffold("assets/mark.svg", _MARK_SVG)

    # 3. Submission listing pack
    if not (target_dir / "submission/listing.json").is_file():
        listing_json = _build_listing_json(target_dir, analysis)
        _write_scaffold("submission/listing.json", json.dumps(listing_json, indent=2) + "\n")

    # 4. Skills: compile candidate workflows or create starter skill
    skills_dir = target_dir / "skills"
    candidates = [
        c for c in analysis.get("candidates", [])
        if c.get("recommendedTarget") == "compile_skill" and c.get("slug")
    ]
    if candidates:
        for c in candidates[:3]:
            slug = c["slug"]
            skill_file = f"skills/{slug}/SKILL.md"
            if not (target_dir / skill_file).is_file():
                reason = c.get("reasons", ["discovered workflow"])[0]
                _write_scaffold(skill_file, _skill_md_template(slug, c.get("path", ""), reason))
    elif not skills_dir.is_dir() or not any(skills_dir.glob("*/SKILL.md")):
        _write_scaffold(f"skills/{repo}/SKILL.md", _skill_md_template(repo))

    # 5. Continuous Integration workflow
    workflow_path = target_dir / ".github/workflows/codex-plugin.yml"
    if not workflow_path.is_file():
        _write_scaffold(".github/workflows/codex-plugin.yml", _build_workflow_yaml())

    if not scaffolded:
        print("[autopilot] Nothing to scaffold — all files already exist. Skipping PR.")
        _git("checkout", default_branch)
        _git("branch", "-D", branch_name)
        return None, None, []

    # Stage and commit
    add_proc = _git("add", "--", *[str(target_dir / f) for f in scaffolded])
    if add_proc.returncode != 0:
        print(f"[autopilot] git add failed: {add_proc.stderr}", file=sys.stderr)

    commit_msg = (
        f"feat: scaffold ChatGPT/Codex plugin structure and artifacts\n\n"
        f"Auto-generated by ChatGPT & Codex Plugin Autopilot.\n"
        f"Architecture: {arch}\n"
        f"Files added:\n" + "\n".join(f"  - {f}" for f in scaffolded)
    )
    commit_proc = _git("commit", "-m", commit_msg)
    if commit_proc.returncode != 0:
        print(f"[autopilot] git commit failed: {commit_proc.stderr}", file=sys.stderr)
        return None, None, []

    # Push the branch
    push_proc = _git("push", "origin", branch_name)
    if push_proc.returncode != 0:
        print(f"[autopilot] git push failed: {push_proc.stderr}", file=sys.stderr)
        return None, None, []

    # Open the PR using gh CLI
    body = _pr_body(analysis, scaffolded, branch_name, arch)
    gh_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
    gh_env = {**os.environ, "GH_TOKEN": gh_token}

    pr_proc = subprocess.run(
        [
            "gh", "pr", "create",
            "--title", pr_title,
            "--body", body,
            "--head", branch_name,
            "--base", default_branch,
            "--label", "plugin-autopilot",
        ],
        capture_output=True,
        text=True,
        cwd=str(target_dir),
        env=gh_env,
    )

    pr_url: str | None = None
    if pr_proc.returncode == 0:
        pr_url = pr_proc.stdout.strip()
    else:
        stdout = pr_proc.stdout.strip()
        stderr = pr_proc.stderr.strip()
        if stdout.startswith("http"):
            pr_url = stdout
        else:
            print(f"[autopilot] ⚠️ gh pr create failed.\nSTDOUT: {stdout}\nSTDERR: {stderr}", file=sys.stderr)
            return None, None, scaffolded

    pr_number: str | None = None
    if pr_url:
        print(f"[autopilot] ✅ PR opened: {pr_url}")
        match = re.search(r"/pull/(\d+)", pr_url)
        if match:
            pr_number = match.group(1)

    return pr_url, pr_number, scaffolded


# ---------------------------------------------------------------------------
# Summary / output helpers
# ---------------------------------------------------------------------------

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


def render_markdown_summary(
    mode: str,
    report: dict,
    target_dir: Path,
    arch_str: str,
    pr_url: str | None = None,
    scaffolded_files: list[str] | None = None,
) -> str:
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

    if pr_url:
        lines.extend([
            "",
            "> ### 🚀 Auto-Scaffold Pull Request Opened!",
            f"> **Pull Request:** [{pr_url}]({pr_url})",
        ])
        if scaffolded_files:
            lines.append(f"> **Files Added:** {', '.join(f'`{f}`' for f in scaffolded_files)}")
        lines.append("")

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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GitHub Action Entrypoint for Plugin Autopilot")
    parser.add_argument("--path", default=os.environ.get("INPUT_PATH", "."))
    parser.add_argument("--action", default=os.environ.get("INPUT_ACTION", "auto"))
    parser.add_argument("--output-dir", default=os.environ.get("INPUT_OUTPUT_DIR", "dist"))
    parser.add_argument("--fail-on-error", default=os.environ.get("INPUT_FAIL_ON_ERROR", "true"))
    parser.add_argument("--summary", default=os.environ.get("INPUT_SUMMARY", "true"))
    parser.add_argument("--create-pr", default=os.environ.get("INPUT_CREATE_PR", "false"))
    parser.add_argument("--pr-title", default=os.environ.get("INPUT_PR_TITLE", "🤖 [Plugin Autopilot] Scaffold ChatGPT/Codex plugin structure"))
    parser.add_argument("--pr-branch", default=os.environ.get("INPUT_PR_BRANCH", ""))
    args = parser.parse_args(argv)

    target_dir = Path(args.path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    fail_on_error = str(args.fail_on_error).lower() in ("true", "1", "yes")
    gen_summary = str(args.summary).lower() in ("true", "1", "yes")
    action_mode = args.action.lower().strip()
    create_pr = str(args.create_pr).lower() in ("true", "1", "yes")
    pr_title = args.pr_title
    pr_branch = args.pr_branch

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

    # ---------------------------------------------------------------------------
    # Auto-PR: open PR only when analysis succeeds and create-pr is enabled
    # ---------------------------------------------------------------------------
    pr_url: str | None = None
    pr_number: str | None = None
    scaffolded_files: list[str] = []

    if create_pr and actual_mode == "analyze" and ok:
        print("[autopilot] create-pr=true — scaffolding plugin files and opening PR …")
        try:
            pr_url, pr_number, scaffolded_files = create_pr_with_scaffold(
                target_dir, report, architecture, pr_title, pr_branch
            )
        except Exception as exc:
            print(f"[autopilot] Auto-PR failed with exception: {exc}", file=sys.stderr)
            pr_url, pr_number, scaffolded_files = None, None, []

        if pr_url:
            write_output("pr_url", pr_url)
            if pr_number:
                write_output("pr_number", pr_number)
        else:
            print("[autopilot] ⚠️  Auto-PR was requested but no PR URL was returned.", file=sys.stderr)

    summary_md = render_markdown_summary(
        actual_mode, report, target_dir, architecture, pr_url=pr_url, scaffolded_files=scaffolded_files
    )
    if gen_summary:
        write_summary(summary_md)

    print(json.dumps(report, indent=2, sort_keys=True))

    if not ok and fail_on_error:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

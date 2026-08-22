#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", "node_modules", "vendor",
    "dist", "build", "coverage", ".next", ".cache", ".pytest_cache",
    "__pycache__", ".venv", "venv", "target",
}
TEXT_SUFFIXES = {".md", ".mdx", ".txt", ".yaml", ".yml", ".json", ".toml"}
AGENT_FILES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "COPILOT.md"}
WORKFLOW_DIRS = {"workflow", "workflows", "playbook", "playbooks", "commands", "prompts", "recipes"}
AGENT_DIRS = {"agent", "agents", ".agents", ".claude"}
WORKSPACE_CAPABILITIES = ["read", "list", "search", "grep", "write", "patch", "shell", "python"]


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def safe_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def iter_files(root: Path, max_files: int) -> Iterable[Path]:
    """Yield eligible files deterministically while pruning ignored trees before descent."""
    count = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = sorted(
            (name for name in dirnames if name not in IGNORED_DIRS),
            key=str.lower,
        )
        for filename in sorted(filenames, key=str.lower):
            path = Path(dirpath) / filename
            if not path.is_file():
                continue
            yield path
            count += 1
            if count >= max_files:
                return


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:64] or "workflow"


def classify_candidate(path: Path, root: Path) -> dict | None:
    relative = rel(path, root)
    parts = {part.lower() for part in path.relative_to(root).parts[:-1]}
    suffix = path.suffix.lower()

    if path.name == "SKILL.md" and "skills" in parts:
        parent = path.parent.name
        return {
            "path": relative,
            "kind": "existing_skill",
            "slug": slugify(parent),
            "score": 100,
            "recommendedTarget": "preserve_skill",
            "reasons": ["existing Agent Skill package"],
            "publicReview": "required",
        }

    if path.name in AGENT_FILES or (parts & AGENT_DIRS and suffix in TEXT_SUFFIXES):
        return {
            "path": relative,
            "kind": "agent_definition",
            "slug": slugify(path.stem if path.name not in AGENT_FILES else path.stem + "-workflow"),
            "score": 85,
            "recommendedTarget": "compile_skill",
            "reasons": ["agent instructions can encode a repeatable workflow"],
            "publicReview": "required",
        }

    if parts & WORKFLOW_DIRS and suffix in TEXT_SUFFIXES:
        return {
            "path": relative,
            "kind": "workflow_document",
            "slug": slugify(path.stem),
            "score": 75,
            "recommendedTarget": "compile_skill",
            "reasons": ["workflow/playbook content is a reusable Skill candidate"],
            "publicReview": "required",
        }

    lowered = path.stem.lower()
    if suffix in {".md", ".mdx"} and any(token in lowered for token in ("workflow", "playbook", "runbook", "checklist")):
        return {
            "path": relative,
            "kind": "workflow_document",
            "slug": slugify(path.stem),
            "score": 65,
            "recommendedTarget": "compile_skill",
            "reasons": ["filename indicates a repeatable operating procedure"],
            "publicReview": "required",
        }

    return None


def inspect_manifest(root: Path) -> dict:
    manifest_path = root / ".codex-plugin" / "plugin.json"
    manifest = safe_json(manifest_path) if manifest_path.is_file() else {}
    return {
        "present": bool(manifest),
        "declaresSkills": bool(manifest.get("skills")),
        "declaresMcp": bool(manifest.get("mcpServers")),
        "declaresApps": bool(manifest.get("apps")),
        "declaresHooks": bool(manifest.get("hooks")),
    }


def analyze(root: Path, max_files: int = 5000) -> dict:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"repository root is not a directory: {root}")

    files = list(iter_files(root, max_files))
    candidates = [candidate for path in files if (candidate := classify_candidate(path, root))]
    candidates.sort(key=lambda item: (-item["score"], item["path"].lower(), item["kind"]))

    manifest = inspect_manifest(root)
    relative_files = {rel(path, root) for path in files}
    suffix_counts = Counter(path.suffix.lower() or "<none>" for path in files)

    has_existing_skills = any(candidate["kind"] == "existing_skill" for candidate in candidates)
    has_skill_candidates = any(candidate["recommendedTarget"] in {"preserve_skill", "compile_skill"} for candidate in candidates)

    root_mcp_present = ".mcp.json" in relative_files
    root_app_present = ".app.json" in relative_files

    if manifest["present"]:
        has_mcp = manifest["declaresMcp"]
        has_apps = manifest["declaresApps"]
    else:
        has_mcp = root_mcp_present
        has_apps = root_app_present

    has_hooks = "hooks/hooks.json" in relative_files or manifest["declaresHooks"] or any(
        item.startswith("hooks/") for item in relative_files
    )

    signals = []
    if has_existing_skills:
        signals.append("skills")
    if any(candidate["kind"] == "agent_definition" for candidate in candidates):
        signals.append("agents")
    if any(candidate["kind"] == "workflow_document" for candidate in candidates):
        signals.append("workflows")
    if has_mcp:
        signals.append("mcp")
    if has_apps:
        signals.append("apps")
    if has_hooks:
        signals.append("hooks")

    has_external_runtime = has_mcp or has_apps
    if has_external_runtime and has_skill_candidates:
        recommended = "hybrid"
        reason = "The repository contains reusable Skill candidates and an active app/MCP integration boundary."
    elif has_external_runtime:
        recommended = "MCP-backed"
        reason = "The repository contains an active external app/MCP integration boundary."
    else:
        recommended = "skills-only"
        reason = "The reusable workflows can be distributed without requiring an external runtime."

    # Repository conversion is inherently workspace-oriented. Install the shared
    # operator when a Plugin is being created from repository files, then let the
    # experience architect narrow which operations each domain Skill actually uses.
    workspace_profile = {
        "installRecommended": bool(files),
        "skill": "host-workspace-operator",
        "capabilities": WORKSPACE_CAPABILITIES,
        "readOnly": ["read", "list", "search", "grep"],
        "mutations": ["write", "patch", "mutating shell commands"],
        "hostControlled": True,
    }

    next_actions = ["review_candidates"]
    if has_skill_candidates:
        next_actions.append("compile_workflows")
    if has_external_runtime:
        next_actions.append("review_external_actions")
    next_actions.extend([
        "design_plugin_experience",
        "plan_host_workspace_capabilities",
        "install_host_workspace_skill",
        "validate_public_safety",
        "design_brand_identity",
        "build_directory_listing",
        "validate_plugin",
        "build_submission_pack",
    ])

    warnings = []
    if len(files) >= max_files:
        warnings.append(f"scan stopped at maxFiles={max_files}; increase the limit for a complete inventory")
    if root_mcp_present and manifest["present"] and not manifest["declaresMcp"]:
        warnings.append("root .mcp.json exists but the current plugin manifest does not declare mcpServers")
    if root_app_present and manifest["present"] and not manifest["declaresApps"]:
        warnings.append("root .app.json exists but the current plugin manifest does not declare apps")

    return {
        "schemaVersion": 1,
        "summary": {
            "fileCount": len(files),
            "candidateCount": len(candidates),
            "existingSkillCount": sum(1 for item in candidates if item["kind"] == "existing_skill"),
            "workflowCandidateCount": sum(1 for item in candidates if item["kind"] != "existing_skill"),
        },
        "signals": sorted(signals),
        "architecture": {
            "recommended": recommended,
            "reason": reason,
            "requiresHumanReview": bool(has_external_runtime),
        },
        "hostWorkspace": workspace_profile,
        "manifest": manifest,
        "inventory": {
            "topLevel": sorted({path.relative_to(root).parts[0] for path in files}),
            "suffixCounts": dict(sorted(suffix_counts.items())),
        },
        "candidates": candidates,
        "nextActions": next_actions,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover agentic workflows that can become ChatGPT/Codex Plugin Skills.")
    parser.add_argument("repository", nargs="?", default=".")
    parser.add_argument("--max-files", type=int, default=5000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.max_files < 1:
        parser.error("--max-files must be at least 1")

    try:
        report = analyze(Path(args.repository), max_files=args.max_files)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2, sort_keys=True))
        else:
            print(f"repo analysis: FAIL: {exc}")
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"architecture: {report['architecture']['recommended']}")
        print(f"candidates: {report['summary']['candidateCount']}")
        print(f"workspace skill: {report['hostWorkspace']['skill']} install={report['hostWorkspace']['installRecommended']}")
        for candidate in report["candidates"][:20]:
            print(f"- {candidate['kind']}: {candidate['path']} -> {candidate['recommendedTarget']}")
        for warning in report["warnings"]:
            print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

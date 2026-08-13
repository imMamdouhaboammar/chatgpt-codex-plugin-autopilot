# Plugin Contract Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Plugin Autopilot catch current ChatGPT/Codex plugin package and submission failures before upload.

**Architecture:** Extend the existing dependency-free Python validator rather than adding a second validator. Keep package validation, public-submission guidance, deterministic packaging, and self-hosting verification separate but connected through one fail-closed preflight.

**Tech Stack:** Python 3 standard library, unittest, GitHub Actions, Markdown/YAML/JSON plugin metadata.

## Global Constraints

- Current official OpenAI documentation is authoritative over remembered schema details.
- `.codex-plugin/` contains `plugin.json` only.
- Every immediate child under `skills/` must be a Skill directory containing `SKILL.md` for Autopilot's strict preflight.
- Final Plugin Directory submission requires a supported category.
- Do not add MCP/app dependencies to this skill-only plugin.
- Keep the validator dependency-free.
- A locally valid ZIP is not evidence of Plugin Directory approval.

---

### Task 1: Add regression tests for learned submission failures

**Files:**
- Create: `tests/test_validator_regressions.py`

**Interfaces:**
- Consumes: `skills/chatgpt-codex-plugin-autopilot/scripts/validate_plugin.py`
- Produces: executable contracts for package shape, declaration semantics, Skill identity, assets, and agent metadata.

- [ ] Write fixture helpers that create a minimal valid skills-only plugin with a square SVG.
- [ ] Add a test rejecting a direct file under `skills/`.
- [ ] Add a test rejecting extra content under `.codex-plugin/`.
- [ ] Add a test showing undeclared `.mcp.json` remains ignored for architecture classification.
- [ ] Add a test allowing Skill metadata name to differ from the directory.
- [ ] Add a test rejecting `..` traversal in asset references.
- [ ] Add a test rejecting invalid `agents/openai.yaml` metadata.
- [ ] Add tests rejecting malformed declared app and MCP mappings.
- [ ] Open a PR and verify the new tests fail for the intended missing behaviors.

### Task 2: Strengthen the dependency-free validator

**Files:**
- Modify: `skills/chatgpt-codex-plugin-autopilot/scripts/validate_plugin.py`

**Interfaces:**
- Consumes: plugin root path and optional public exclusions.
- Produces: JSON report with `ok`, architecture, skills, errors, warnings, size and file counts.

- [ ] Reject any `.codex-plugin/` child other than `plugin.json`.
- [ ] Reject files/symlinks directly under the configured `skills/` directory in strict Autopilot preflight so intended Skills cannot be silently ignored.
- [ ] Track unique Skill metadata names without requiring folder-name equality.
- [ ] Harden relative asset paths against whitespace, controls, absolute forms, drive prefixes, and `..` segments.
- [ ] Treat `.app.json`/`.mcp.json` as active only when declared by the manifest and warn when present but undeclared.
- [ ] Add conservative structural validation for declared app/MCP mappings.
- [ ] Add structural validation for `agents/openai.yaml` using the documented metadata subset without adding a package dependency.
- [ ] Keep supported category required because this validator targets final public-directory readiness, not only upload acceptance.
- [ ] Run the complete unit suite and self-check until green.

### Task 3: Refresh the official contract and failure playbook

**Files:**
- Modify: `skills/chatgpt-codex-plugin-autopilot/references/official-contract.md`
- Modify: `skills/chatgpt-codex-plugin-autopilot/references/submission-errors.md`
- Modify: `skills/chatgpt-codex-plugin-autopilot/references/architectures.md`
- Create: `skills/chatgpt-codex-plugin-autopilot/references/submission-checklist.md`

**Interfaces:**
- Consumes: official OpenAI plugin/Skill/submission documentation checked 2026-08-13.
- Produces: a dated snapshot and a practical pre-upload diagnosis guide.

- [ ] Record the 2026-08-13 verification date and current official URLs.
- [ ] Document `plugin.json`-only `.codex-plugin/` and Skill-direct-child behavior.
- [ ] Document `agents/openai.yaml`, ignored undeclared app/MCP files, and safe asset paths.
- [ ] Add a submission checklist separating package checks from portal materials such as publisher verification, listing copy, release notes, and positive/negative test cases.

### Task 4: Update the Autopilot Skill and public README

**Files:**
- Modify: `skills/chatgpt-codex-plugin-autopilot/SKILL.md`
- Modify: `README.md`
- Modify: `tests/test_skill_surface.py`
- Modify: `.codex-plugin/plugin.json`
- Modify: `tests/test_plugin_contract.py`

**Interfaces:**
- Produces: discoverable instructions that default to strict final-directory validation and version `0.2.0`.

- [ ] Update Skill instructions to run package preflight and submission-readiness checks as distinct gates.
- [ ] Add the new submission checklist to required Skill references.
- [ ] Expand README with the concrete failure classes Autopilot catches.
- [ ] Bump plugin version to `0.2.0` and update the version contract test.
- [ ] Run full unit tests, self-check, deterministic release build, extraction validation, and archive inspection.

### Task 5: PR and integration verification

**Files:**
- No new production files.

- [ ] Review the changed file list for unrelated artifacts, local paths, secrets, and stale contract claims.
- [ ] Require PR CI success.
- [ ] Merge only after CI is green and the PR remains mergeable.
- [ ] Verify post-merge CI on `main` before calling the repository update integrated.

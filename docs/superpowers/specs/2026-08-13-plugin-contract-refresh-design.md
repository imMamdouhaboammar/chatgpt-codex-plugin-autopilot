# 2026 ChatGPT/Codex Plugin Contract Refresh

## Goal

Update Plugin Autopilot so it catches the current public ChatGPT/Codex plugin packaging and submission failures before upload, using the official OpenAI plugin contract checked on 2026-08-13 and concrete failures observed while repairing real plugin packages.

## Scope

The refresh keeps the project dependency-free and skill-first. It does not add an MCP server, app runtime, remote service, telemetry, or publishing credentials.

The implementation will strengthen four boundaries:

1. package shape validation
2. Skill and optional `agents/openai.yaml` validation
3. app/MCP declaration semantics
4. submission-readiness guidance distinct from ZIP/package validation

## Package shape

`.codex-plugin/` contains `plugin.json` only. Files directly under `skills/` are invalid because each immediate child is an importable Skill directory containing `SKILL.md`.

Asset references must be package-relative, `./`-prefixed where the manifest expects a path, free of traversal segments and control characters, remain inside the package, and resolve to real files. `interface.logo` and `interface.composerIcon` remain required square image checks.

## Skill validation

Each immediate directory under `skills/` must contain a non-empty `SKILL.md` with YAML frontmatter containing `name` and `description`. Skill names must be unique and satisfy identity limits, but the Skill name is not required to equal its directory name unless the official OpenAI contract later requires it.

When `agents/openai.yaml` exists, Autopilot validates the documented OpenAI metadata surface conservatively: required `interface` metadata, supported policy keys and values, supported dependency shape, and relative asset references. The local validator must not pretend to replace the official uploader.

## App and MCP declarations

A root `.app.json` or `.mcp.json` file is active only when the manifest declares the corresponding component. Undeclared files produce an explicit warning because OpenAI ignores them; they must not change architecture classification.

Declared `.app.json` and `.mcp.json` files receive structural checks before packaging. The validator should report the producing source file and field so a user can repair the root cause rather than patching the ZIP.

## Submission readiness

Package validity and public submission readiness are separate states. Autopilot will document both.

For public submission it will prompt for the current listing metadata, publisher verification, release notes, positive and negative test cases, and any MCP-specific review material required by the current official submission flow. A locally valid ZIP must never be described as approved or published.

## Tests

Regression coverage must include:

- a direct `skills/registry.json` style file is rejected
- extra content inside `.codex-plugin/` is rejected
- undeclared `.mcp.json` does not turn a skills-only package into MCP-backed
- a valid Skill whose metadata name differs from the folder can pass
- unsafe asset traversal is rejected
- invalid `agents/openai.yaml` is rejected
- the repository still self-validates and produces byte-identical release archives

## Release boundary

This work updates and verifies the repository. It does not publish a GitHub Release or submit to the OpenAI Plugin Directory unless separately requested.

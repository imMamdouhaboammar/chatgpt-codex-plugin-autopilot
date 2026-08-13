# ChatGPT/Codex Plugin Autopilot

A standalone, self-hosting Skill Plugin for building, repairing, validating, packaging, and preparing ChatGPT/Codex Plugins for submission.

It is designed for the failures that usually appear late: a ZIP looks correct, the repository tests pass, then the plugin importer ignores a Skill, rejects branding, misreads an undeclared MCP file, or final-directory validation applies stricter rules than the local package check.

## What 0.2 catches before upload

Plugin Autopilot now checks the current package contract and several failure classes learned from real plugin repair work:

- `.codex-plugin/` contains `plugin.json` only
- `interface.logo` and `interface.composerIcon` exist and point to square supported images
- declared asset paths reject outer whitespace, control characters, absolute/drive paths, package escapes, and `..` traversal
- every intended direct child under `skills/` is a real Skill directory containing `SKILL.md`
- loose files such as `skills/registry.json` fail strict preflight instead of being silently ignored
- Skill metadata names are unique and satisfy identity limits without inventing a folder-name equality rule
- optional `agents/openai.yaml` receives structural checks for the documented Skill interface, policy, and dependency fields
- root `.app.json` / `.mcp.json` only activate when the manifest declares them
- declared app and MCP mappings receive structural checks before packaging
- hooks accept the documented path/list/inline forms while declared paths stay package-relative
- final Plugin Directory listing limits are applied instead of relying only on looser package limits
- secret-shaped files, bytecode caches, symlinks, local absolute user paths, normalization collisions, and public exclusions are rejected

The validator is dependency-free and intentionally conservative. Official OpenAI validation and review remain authoritative.

## Two separate gates

A plugin can be structurally valid without being ready for public review.

### Package preflight

Checks the artifact itself:

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/validate_plugin.py . --json
```

### Submission readiness

Checks the public listing, publisher/policy requirements, Skill scan readiness, and MCP review material when applicable.

See:

```text
skills/chatgpt-codex-plugin-autopilot/references/submission-checklist.md
```

Autopilot reports `locally validated`, `submitted`, `approved`, and `published` as different states.

## Install

Download the ZIP attached to the latest GitHub Release and install or upload it through the supported ChatGPT/Codex Plugin or Skill flow available to your account and workspace.

For repository or personal testing, the current OpenAI plugin flow also supports local marketplace sources. Test the installed cached copy in a fresh chat after changing a plugin.

## Self-hosting contract

This repository uses the same validator and deterministic packager shipped inside the Plugin to validate and package itself.

A release is blocked unless:

1. unit tests pass
2. the staged plugin self-validates
3. deterministic archive builds match
4. archive contents are inspected
5. a fresh extraction validates again
6. the public release surface passes its checks

The release scripts do not publish to the OpenAI Plugin Directory and do not claim directory approval.

## Local verification

```bash
python3 -m unittest discover -s tests -v
python3 scripts/self_check.py
python3 scripts/build_release.py --out-dir dist
```

For an arbitrary target plugin:

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/validate_plugin.py /path/to/plugin --json
python3 skills/chatgpt-codex-plugin-autopilot/scripts/package_plugin.py /path/to/plugin /tmp/plugin-a.zip --json
python3 skills/chatgpt-codex-plugin-autopilot/scripts/package_plugin.py /path/to/plugin /tmp/plugin-b.zip --json
cmp /tmp/plugin-a.zip /tmp/plugin-b.zip
unzip -Z1 /tmp/plugin-a.zip
```

Extract the archive into a clean directory and run the validator again against the extracted copy.

## Architecture support

Autopilot can audit and prepare:

- Skills-only plugins
- MCP-backed plugins
- hybrid Skill + MCP plugins
- optional lifecycle hooks
- registered app/MCP compatibility mappings for local or workspace packaging

The Autopilot plugin itself remains Skills-only. It does not require an MCP server, app runtime, registry credential, hidden telemetry, or remote service.

## Knowledge included

The shipped Skill includes dated references for:

- current OpenAI plugin package contract
- architecture selection
- submission and review failures
- public submission readiness
- deterministic release practice

The operating contract requires re-checking official OpenAI documentation before changing a public plugin because these rules can evolve.

## Status boundaries

A green CI run proves this repository passed its configured checks.

A valid deterministic ZIP proves an artifact was prepared consistently.

Neither proves that OpenAI accepted or published the plugin in the public Plugin Directory.

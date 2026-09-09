# AGENTS.md — Agent Interface Contract
# chatgpt-codex-plugin-autopilot
# Copyright (c) 2026 Mamdouh Aboammar — MIT License

## What this repository is

**Plugin Autopilot** is a self-hosting ChatGPT/Codex Plugin that converts agentic repositories into focused, validated, deterministically packaged Plugins for the ChatGPT and Codex Plugin Directory.

It packages and validates the same Skills it uses to convert other repositories.

## Available Skills (9 total)

All skills live in `skills/`. Load the relevant SKILL.md before acting.

| Skill | Location | Trigger |
|---|---|---|
| `chatgpt-codex-plugin-autopilot` | `skills/chatgpt-codex-plugin-autopilot/SKILL.md` | Main orchestrator — conversion, validation, packaging, submission |
| `agentic-repo-discovery` | `skills/agentic-repo-discovery/SKILL.md` | Find reusable workflows in a repository |
| `workflow-to-skill-compiler` | `skills/workflow-to-skill-compiler/SKILL.md` | Convert playbooks/prompts/commands to portable Skills |
| `plugin-experience-architect` | `skills/plugin-experience-architect/SKILL.md` | Design the Plugin's public surface and UX |
| `host-workspace-operator` | `skills/host-workspace-operator/SKILL.md` | Native read/list/search/grep/write/patch/shell/Python |
| `sandbox-python-executor` | `skills/sandbox-python-executor/SKILL.md` | Require real Python execution evidence |
| `plugin-brand-identity-designer` | `skills/plugin-brand-identity-designer/SKILL.md` | Create SVG brand identity (light + dark + icon) |
| `plugin-directory-listing-writer` | `skills/plugin-directory-listing-writer/SKILL.md` | Prepare Plugin Directory metadata and reviewer pack |
| `submission-pack-builder` | `skills/submission-pack-builder/SKILL.md` | Assemble submission evidence |

## Key scripts

| Script | Purpose |
|---|---|
| `bash init.sh` | **Copy-in engine init** — verify Python, count skills, run self-check + tests, confirm ownership |
| `python3 scripts/self_check.py` | Validate release surface (skills=9, manifests present) |
| `python3 -m unittest discover -s tests -v` | Run all 92 regression tests |
| `python3 scripts/build_release.py --out-dir dist` | Build deterministic ZIP release |
| `python3 skills/chatgpt-codex-plugin-autopilot/scripts/analyze_repo.py <path> --json` | Analyze a repo for plugin conversion |
| `python3 skills/chatgpt-codex-plugin-autopilot/scripts/validate_plugin.py . --json` | Validate plugin package |
| `python3 skills/chatgpt-codex-plugin-autopilot/scripts/package_plugin.py . dist/out.zip --json` | Package plugin to ZIP |

## Agent operating rules

1. Always run `python3 -m unittest discover -s tests -v` before committing.
2. Always run `python3 scripts/self_check.py` before releasing.
3. Releases are triggered by tag push (`git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`).
4. The tag version must exactly match `".codex-plugin/plugin.json".version`.
5. Never claim a script ran if it was not executed — show real output.
6. Never add MCP dependencies just to make the Plugin appear more capable.
7. Do not add secrets, credentials, or personal paths to any committed file.

## Conventional commit prefixes

`feat:` `fix:` `docs:` `test:` `chore:` `refactor:` `ci:` + `(#issue)` suffix.

## Branch naming

`issue/<id>-<slug>` — e.g. `issue/50-ai-discovery-files`

## Author & copyright

All code © 2026 **Mamdouh Aboammar** — MIT License.
Repository: https://github.com/imMamdouhaboammar/chatgpt-codex-plugin-autopilot

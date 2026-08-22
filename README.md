# ChatGPT/Codex Plugin Autopilot

A lot of strong agentic work already exists in GitHub repositories.

The problem is that the useful part is often buried in `AGENTS.md`, prompts, playbooks, commands, scripts, custom agents, or repo-specific workflows. The repository may be excellent for its original author and still be difficult to install, discover, or reuse as a ChatGPT/Codex Plugin.

Plugin Autopilot is for that gap.

Give it an existing agentic repository. It helps find the workflows worth sharing, decide what should become Skills, keep internal-only material out of the public package, choose whether an external app/MCP runtime is actually necessary, then validate and package the result against the current ChatGPT/Codex Plugin contract.

It also still does the strict preflight work from earlier releases: package validation, deterministic ZIPs, submission readiness checks, and clear status boundaries between local proof and OpenAI review.

## The 0.4 flow

```text
AGENTIC REPO
    |
    v
DISCOVER
Find Skills, agents, workflows, playbooks, commands and runtime signals
    |
    v
DECIDE
preserve_skill | compile_skill | reference_only | runtime_dependency | internal_only | discard
    |
    v
COMPILE
Turn selected workflows into portable focused Skills
    |
    v
DESIGN
Shape a clear Plugin around user jobs, not the repo's folder structure
    |
    v
PROVE
Tests -> strict preflight -> deterministic package -> clean extraction check
    |
    v
PREPARE
Reviewer evidence and submission material for the exact validated artifact
```

The important part is the second step. Autopilot does not assume every clever agent or internal workflow belongs in a public Plugin.

## Start with repository discovery

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/analyze_repo.py /path/to/repo --json
```

The analyzer is dependency-free and read-only. It inventories likely agentic workflow material and produces a deterministic report with:

- existing Skills
- agent definitions such as `AGENTS.md`
- workflow/playbook/command/prompt candidates
- MCP/app/hook signals
- an initial `skills-only`, `MCP-backed`, or `hybrid` recommendation
- next conversion actions
- warnings such as undeclared `.mcp.json` or `.app.json`

It is deliberately a discovery tool, not an automatic publisher. A human or agent still reviews the candidates in context and sets the public product boundary.

## Focused Skills included

### `agentic-repo-discovery`

Use it when the starting point is an existing repository rather than a finished Plugin. It turns raw repo signals into a candidate/disposition map and identifies what should stay internal.

### `workflow-to-skill-compiler`

Use it to convert a selected playbook, prompt chain, runbook, command, or agent workflow into a portable Skill without throwing away its decision logic, approval gates, evidence requirements, or stop conditions.

### `plugin-experience-architect`

Use it after the candidate Skills exist. It reduces overlap, defines the public Skill set, decides required versus optional app dependencies, and makes listing capabilities and starter prompts correspond to real user jobs.

### `submission-pack-builder`

Use it only after the exact artifact passes local preflight. It prepares reviewer evidence while keeping `locally_validated`, `submission_ready`, `submitted`, `approved`, and `published` as different states.

### `chatgpt-codex-plugin-autopilot`

The main orchestrator. It can run the complete conversion path or audit/repair a repository that is already shaped as a Plugin.

## Architecture decisions

Autopilot supports three target shapes:

- **Skills-only** when the workflow can be delivered with instructions, references, portable scripts, and host capabilities without a required external service.
- **MCP-backed** when the core job requires external data, authentication, or remote actions.
- **Hybrid** when reusable reasoning/process belongs in Skills and external data/actions belong in an app or MCP server.

The presence of API code, `.mcp.json`, or an MCP server in the source repository is evidence to inspect, not a reason by itself to force a runtime dependency.

Plugin Autopilot itself remains Skills-only.

## What strict preflight catches

The validator still checks the failure classes that usually show up late:

- `.codex-plugin/` contains `plugin.json` only
- `interface.logo` and `interface.composerIcon` exist and point to square supported images
- declared asset paths reject whitespace, control characters, absolute/drive paths, package escapes, and `..` traversal
- every intended direct child under `skills/` is a real Skill directory containing `SKILL.md`
- loose files such as `skills/registry.json` fail strict preflight instead of being silently ignored
- Skill metadata names are unique and satisfy identity limits
- optional `agents/openai.yaml` receives structural checks for documented interface, policy, and dependency fields
- root `.app.json` / `.mcp.json` only activate when the manifest declares them
- declared app and MCP mappings receive structural checks before packaging
- final Plugin Directory listing limits are applied instead of relying only on looser package limits
- secret-shaped files, bytecode caches, symlinks, local absolute user paths, normalization collisions, and public exclusions are rejected
- repo marketplace metadata and reviewer submission material are contract-tested without being added to the runtime ZIP

The validator is dependency-free and intentionally conservative. Official OpenAI validation and review remain authoritative.

## Two separate gates

A plugin can be structurally valid without being ready for public review.

### Package preflight

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/validate_plugin.py . --json
```

This answers whether the artifact is structurally safe, internally consistent, and packageable.

### Submission readiness

Use:

```text
skills/chatgpt-codex-plugin-autopilot/references/submission-checklist.md
submission/reviewer-packet.json
```

This checks the public listing, publisher/policy requirements, Skill scan readiness, reviewer evidence, and MCP review material when applicable.

The reviewer packet is repository-maintained preparation material, not an OpenAI-defined upload schema.

## Deterministic packaging

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/package_plugin.py . /tmp/plugin-a.zip --json
python3 skills/chatgpt-codex-plugin-autopilot/scripts/package_plugin.py . /tmp/plugin-b.zip --json
cmp /tmp/plugin-a.zip /tmp/plugin-b.zip
unzip -Z1 /tmp/plugin-a.zip
```

Extract the archive into a clean directory and run the validator again against the extracted copy.

## Self-hosting contract

This repository uses the same validator and deterministic packager shipped inside the Plugin to validate and package itself.

A release is blocked unless:

1. unit tests pass
2. the staged plugin self-validates
3. deterministic archive builds match
4. archive contents are inspected
5. a fresh extraction validates again
6. the public release surface passes its checks

Local verification:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/self_check.py
python3 scripts/build_release.py --out-dir dist
```

The release scripts do not publish to the OpenAI Plugin Directory and do not claim directory approval.

## Current distribution context

OpenAI moved discovery to the Plugin Directory on July 9, 2026. Plugins are now the main discovery unit across ChatGPT and Codex and can package Skills, apps, and app templates. Skills follow the Agent Skills open standard.

Because this can change, the Autopilot operating contract requires checking the current official OpenAI documentation before modifying a public Plugin or preparing a submission.

## Goal

The goal is not to turn every repository into a Plugin.

It is to make the genuinely useful agentic workflows already sitting in repositories easier for other people to discover, install, understand, and reuse, while preserving the quality and safety boundaries that made those workflows useful in the first place.

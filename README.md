# ChatGPT/Codex Plugin Autopilot

A lot of strong agentic work already exists in GitHub repositories.

The useful part is often buried in `AGENTS.md`, prompts, playbooks, commands, scripts, custom agents, or repo-specific workflows. The repository may be excellent for its original author and still be difficult for someone else to discover, install, or reuse as a ChatGPT/Codex Plugin.

Plugin Autopilot is for that gap.

Give it an existing agentic repository. It helps find the workflows worth sharing, decide what should become Skills, keep internal-only material out of the public package, choose whether an external app/MCP runtime is genuinely required, shape the public Plugin, build its SVG identity and Plugin Directory metadata, then validate and package the exact result.

It also keeps the strict release work from earlier versions: package validation, deterministic ZIPs, clean-extraction checks, submission evidence, and explicit boundaries between local proof and OpenAI review.

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
BRAND
Create a product-specific SVG identity with light + dark variants
    |
    v
LIST
Prepare Plugin Directory fields, capabilities, prompts and publisher gaps
    |
    v
PROVE
Tests -> directory gate -> strict preflight -> deterministic package -> clean extraction
    |
    v
PREPARE
Reviewer evidence and submission material for the exact validated artifact
```

The important principle is that Autopilot does not assume every clever agent or internal workflow belongs in a public Plugin. Conversion is a product and distribution decision, not a folder-copy operation.

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

It is deliberately a discovery tool, not an automatic publisher. A maintainer still reviews candidates in context and sets the public product boundary.

## Focused Skills included

### `agentic-repo-discovery`

Use it when the starting point is an existing repository rather than a finished Plugin. It turns raw repo signals into a candidate/disposition map and identifies what should stay internal.

### `workflow-to-skill-compiler`

Use it to convert a selected playbook, prompt chain, runbook, command, or agent workflow into a portable Skill without throwing away its real decision logic, approval gates, evidence requirements, or stop conditions.

### `plugin-experience-architect`

Use it after the candidate Skills exist. It reduces overlap, defines the public Skill set, decides required versus optional app dependencies, creates starter/discovery prompt directions, and defines the visual idea the Plugin identity should express.

### `plugin-brand-identity-designer`

Use it after the public product boundary is stable. It requires a self-contained SVG identity kit with `logo-light.svg`, `logo-dark.svg`, and a compact square icon. Both variants share one geometry and must represent the Plugin's actual job rather than generic AI imagery.

### `plugin-directory-listing-writer`

Use it to turn the exact Plugin into truthful public metadata: Name, Subtitle, Description, Category, verified Developer name, Website, Customer support, Privacy policy, Terms, Version, Package name, Capabilities, starter prompts, and current reviewer material. Missing publisher or legal facts remain missing instead of being guessed.

### `submission-pack-builder`

Use it only after package, brand, and listing gates pass for the exact artifact. It prepares reviewer evidence while keeping `listing_ready`, `locally_validated`, `submission_ready`, `submitted`, `approved`, and `published` as different states.

### `chatgpt-codex-plugin-autopilot`

The main orchestrator. It can run the complete conversion path or audit/repair a repository that is already shaped as a Plugin.

## Architecture decisions

Autopilot supports three target shapes:

- **Skills-only** when the workflow can be delivered with instructions, references, portable scripts, and host capabilities without a required external service.
- **MCP-backed** when the core job requires external data, authentication, or remote actions.
- **Hybrid** when reusable reasoning/process belongs in Skills and external data/actions belong in an app or MCP server.

The presence of API code, `.mcp.json`, or an MCP server in the source repository is evidence to inspect, not a reason by itself to force a runtime dependency.

Plugin Autopilot itself remains Skills-only.

## Brand pack

Autopilot now treats visual identity as part of Plugin preparation rather than an afterthought.

For public Plugin work, the expected identity kit is:

```text
assets/
  logo-light.svg
  logo-dark.svg
  <composer-icon>.svg
```

The light and dark variants must share one core geometry, remain readable at small sizes, and be self-contained SVGs with no external font or image dependency.

The Autopilot 0.4 mark represents multiple repository/workflow inputs converging into one packaged Plugin. Its rationale and usage rules live in `docs/brand-system.md`.

Do not invent undocumented manifest fields just to declare the dark variant. Package both variants and declare only fields supported by the current OpenAI Plugin contract.

## Plugin Directory pack

The repository keeps listing evidence separately from the runtime ZIP in `submission/listing.json`.

Build and validate it with:

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/build_directory_pack.py . --listing submission/listing.json --json
```

The pack covers:

- Name
- Subtitle / short description
- Description / long description
- Category
- Developer name
- Website URL
- Customer support URL
- Privacy policy URL
- Terms of Service URL
- Version
- Package name
- Capabilities
- starter prompts
- light/dark/icon asset paths

`developerName` is not automatically trusted just because it appears in `plugin.json`. It still has to match the verified developer or business identity used in the OpenAI submission flow.

Metadata is also treated as a discovery surface. The workflow calls for direct, indirect, and negative golden prompts so vague names/descriptions can be fixed before submission rather than keyword-stuffed after a routing problem appears.

## What strict preflight catches

The validator checks failure classes that often show up late:

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

## Separate gates

A Plugin can be structurally valid while its public identity, listing, or submission evidence is incomplete.

### Directory listing gate

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/build_directory_pack.py . --listing submission/listing.json --json
```

This checks the repository-maintained listing pack, SVG light/dark assets, field limits, HTTPS public URLs, capabilities, starter prompts, and missing facts.

### Package preflight

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/validate_plugin.py . --json
```

This answers whether the runtime artifact is structurally safe, internally consistent, and packageable.

### Submission readiness

Use:

```text
skills/chatgpt-codex-plugin-autopilot/references/submission-checklist.md
skills/chatgpt-codex-plugin-autopilot/references/branding-and-listing.md
submission/listing.json
submission/reviewer-packet.json
```

This checks the public listing, publisher/policy requirements, brand evidence, Skill scan readiness, reviewer cases, and MCP review material when applicable.

These repository JSON files are preparation/evidence formats, not OpenAI upload schemas.

## Deterministic packaging

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/package_plugin.py . /tmp/plugin-a.zip --json
python3 skills/chatgpt-codex-plugin-autopilot/scripts/package_plugin.py . /tmp/plugin-b.zip --json
cmp /tmp/plugin-a.zip /tmp/plugin-b.zip
unzip -Z1 /tmp/plugin-a.zip
```

Extract the archive into a clean directory and run the validator again against the extracted copy.

## Self-hosting contract

This repository uses the same analyzer, listing gate, validator, and deterministic packager that it ships to validate its own Plugin surface.

A release is blocked unless:

1. unit tests pass
2. the directory listing pack passes
3. the staged Plugin self-validates
4. deterministic archive builds match
5. archive contents are inspected
6. a fresh extraction validates again
7. the public release evidence surface passes its checks

Local verification:

```bash
python3 -m unittest discover -s tests -v
python3 skills/chatgpt-codex-plugin-autopilot/scripts/build_directory_pack.py . --listing submission/listing.json --json
python3 scripts/self_check.py
python3 scripts/build_release.py --out-dir dist
```

The release scripts do not publish to the OpenAI Plugin Directory and do not claim directory approval.

## Current distribution context

The public Plugin Directory is shared across ChatGPT and Codex. Current OpenAI submission guidance requires public listing information, a verified developer/business identity, reviewer test material, and other evidence depending on whether the Plugin is Skills-only or MCP-backed.

Because the contract can change, Autopilot requires checking current official OpenAI documentation before modifying a public Plugin or preparing a submission.

## Goal

The goal is not to turn every repository into a Plugin.

It is to make genuinely useful agentic workflows already sitting in repositories easier for other people to discover, install, understand, and reuse, while preserving the product, safety, privacy, and evidence boundaries that made those workflows useful in the first place.

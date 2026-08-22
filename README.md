# ChatGPT/Codex Plugin Autopilot

There are excellent agentic workflows sitting inside repositories that most people will never use.

Sometimes they live in `AGENTS.md`. Sometimes they are buried in playbooks, prompts, custom agents, scripts, commands, or repo-specific conventions. They may work brilliantly for the original author and still be awkward to discover, install, or reuse in ChatGPT and Codex.

Plugin Autopilot is built for that gap.

Give it an agentic repository. It finds the workflows worth sharing, helps decide what should become public Skills, keeps internal material out of the package, chooses whether an external MCP/app boundary is genuinely required, adds a common host-workspace Skill for file/repository work, prepares the visual identity and Plugin Directory listing, executes local verification when the host allows it, validates the package, and builds deterministic release artifacts.

And Plugin Autopilot is itself a Plugin. It packages and validates the same Skills it uses to convert other repositories.

## The 0.5 flow

```text
AGENTIC REPO
    |
    v
DISCOVER
Skills, agents, playbooks, prompts, commands, runtime signals
    |
    v
DECIDE
preserve | compile | reference | runtime | internal | discard
    |
    v
COMPILE
Turn real workflows into focused portable Skills
    |
    v
WORKSPACE
Add host-native read/list/search/grep/write/patch/shell/Python behavior
    |
    v
EXECUTE
Use host Python and repository tools when available, with real evidence
    |
    v
DESIGN
Shape the Plugin around user jobs
    |
    v
BRAND
Create product-specific light + dark SVG identity
    |
    v
LIST
Prepare public Plugin Directory metadata and reviewer material
    |
    v
PROVE
Tests -> preflight -> deterministic package -> clean extraction
```

The goal is not to copy every folder from a repository into a Plugin. The goal is to preserve the useful agentic behavior and make it portable without pretending the Plugin has permissions or tools the current host did not provide.

## Start with repository discovery

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/analyze_repo.py /path/to/repo --json
```

The analyzer is dependency-free and read-only. It reports:

- existing Skills
- agent definitions such as `AGENTS.md`
- workflow/playbook/command/prompt candidates
- MCP/app/hook signals
- `skills-only`, `MCP-backed`, or `hybrid` architecture recommendation
- a `hostWorkspace` capability profile
- conversion next actions
- warnings such as undeclared `.mcp.json` or `.app.json`

For repository conversions, the analyzer recommends a common workspace baseline with:

```text
read
list
search
grep
write
patch
shell
python
```

These are host-native capabilities. Plugin Autopilot does not invent Plugin manifest permissions for them.

## Add workspace behavior to the generated Plugin

For a file or repository-oriented Plugin:

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/install_host_workspace_skill.py /path/to/plugin
```

This installs `skills/host-workspace-operator/` into the target Plugin.

The installer is deliberately conservative:

- if the Skill is missing, it installs the canonical copy
- if the installed copy is identical, it does nothing
- if the target contains a customized copy, it refuses to overwrite it

The generated Skill follows a simple operating rule:

- read/list/search/grep before mutation
- patch before broad replacement when possible
- write only when the workflow is authorized to change files
- shell only when repository commands are actually needed
- Python for deterministic parsing, transformations, hashes, packaging, and verification
- never claim a tool ran when the host did not provide it

## Host Python in ChatGPT and Codex

`skills/sandbox-python-executor/` adds an execution policy for local deterministic work.

OpenAI refers to Code Interpreter as the **python tool**. When ChatGPT provides that tool and verification matters, the Skill tells the model to actually use it instead of returning a code block and calling the work tested.

Typical uses:

- parse manifests and reports
- inspect archives
- calculate SHA256
- run Plugin Autopilot's dependency-free Python validators/packagers
- transform mounted files
- verify deterministic calculations

When Python is unavailable, the Skill requires the model to say so and keep execution-dependent conclusions unverified.

This does not add a remote code-execution service or fake `code_interpreter` field to the Plugin manifest.

## Included Skills

### `chatgpt-codex-plugin-autopilot`

The main orchestrator for conversion, validation, packaging, submission preparation, and release discipline.

### `agentic-repo-discovery`

Finds candidate agentic workflows and sets the public/private boundary.

### `workflow-to-skill-compiler`

Converts real playbooks, commands, prompt chains, and agent workflows into portable Skills while preserving decisions, approvals, tests, evidence, and stop conditions.

### `plugin-experience-architect`

Defines the public Skill set, architecture, starter prompts, host-workspace capability profile, mutation boundary, and discovery behavior.

### `host-workspace-operator`

A shared policy for native read/list/search/grep/write/patch/shell/Python operations supplied by the host.

### `sandbox-python-executor`

Requires real Python execution evidence when the host exposes Python and deterministic execution matters.

### `plugin-brand-identity-designer`

Creates a product-specific square SVG identity with light and dark variants plus a compact icon.

### `plugin-directory-listing-writer`

Prepares accurate Plugin Directory fields, starter prompts, capability language, public URLs, and reviewer-facing metadata.

### `submission-pack-builder`

Assembles evidence for the exact validated artifact without confusing local readiness with OpenAI approval.

## Host tools are not Plugin permissions

OpenAI surfaces and models can expose different tool sets. Modern models may support capabilities such as file search, Code Interpreter, hosted shell, apply patch, computer use, MCP, and tool search, but availability depends on the product/model/session.

Plugin Autopilot therefore uses capability-oriented Skills rather than undocumented manifest fields.

For example, a generated Skill can say:

```text
search for the relevant implementation
read the matching files
patch the smallest required change
run the relevant tests
```

The current host decides which actual tools satisfy those operations.

For an external authenticated service, use a documented MCP/app boundary. For local workspace behavior, use the host-native capability profile.

## Architecture choices

Autopilot supports:

- **Skills-only** for portable workflows that need no external service
- **MCP-backed** when the core job depends on external authenticated data/actions
- **Hybrid** when reusable process lives in Skills while remote operations live behind MCP/apps

Local read/write/search/grep/shell/Python behavior alone does not make a Plugin MCP-backed.

Plugin Autopilot itself remains Skills-only.

## Brand pack

Autopilot-prepared public Plugins should include:

```text
assets/
  logo-light.svg
  logo-dark.svg
  <composer-icon>.svg
```

The light and dark variants share one geometry and should represent the real job of the Plugin.

## Directory listing pack

Build it with:

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/build_directory_pack.py . --listing submission/listing.json --json
```

The repository-maintained pack covers Name, Subtitle, Description, Category, Developer name, Website, Customer support, Privacy policy, Terms, Version, Package name, Capabilities, starter prompts, and brand asset paths.

Publisher identity still has to match the verified OpenAI identity used during submission. Repository metadata cannot prove that by itself.

## Strict preflight

When execution is available, actually run:

```bash
python3 skills/chatgpt-codex-plugin-autopilot/scripts/validate_plugin.py . --json
python3 skills/chatgpt-codex-plugin-autopilot/scripts/build_directory_pack.py . --listing submission/listing.json --json
python3 skills/chatgpt-codex-plugin-autopilot/scripts/package_plugin.py . /tmp/plugin-a.zip --json
python3 skills/chatgpt-codex-plugin-autopilot/scripts/package_plugin.py . /tmp/plugin-b.zip --json
cmp /tmp/plugin-a.zip /tmp/plugin-b.zip
unzip -Z1 /tmp/plugin-a.zip
```

Then extract the archive into a clean directory and validate the extraction again.

## Self-hosting contract

This repository uses its own Plugin scripts and Skills to check its own release surface.

A release is blocked unless:

1. unit/regression tests pass
2. the directory listing pack passes
3. the staged Plugin self-validates
4. the package contains all expected Skills, including workspace and Python execution policies
5. deterministic archive builds match
6. archive contents are inspected
7. a fresh extraction validates again

Local verification:

```bash
python3 -m unittest discover -s tests -v
python3 skills/chatgpt-codex-plugin-autopilot/scripts/build_directory_pack.py . --listing submission/listing.json --json
python3 scripts/self_check.py
python3 scripts/build_release.py --out-dir dist
```

The release scripts do not claim OpenAI Plugin Directory approval.

## Current distribution context

The Plugin Directory is the public discovery surface across ChatGPT and Codex. Plugins can package Skills and, when required, app/MCP integrations. Skills remain the portable workflow unit.

The current OpenAI contract can change. Plugin Autopilot therefore requires re-checking official OpenAI documentation before public submission or when changing tool/dependency declarations.

## Goal

Make useful agentic workflows easier for other people to discover and use without stripping away the checks that make them reliable.

A good conversion should leave users with a Plugin that can understand the job, inspect the relevant workspace, make only authorized changes, execute real verification when tools are available, explain what it actually did, and package the result cleanly for ChatGPT and Codex.

# Repo to Plugin Conversion Pipeline

Use this pipeline when the starting point is an agentic repository rather than an already-shaped ChatGPT/Codex Plugin.

## 1. Discover before converting

Run:

```bash
python3 <autopilot-skill>/scripts/analyze_repo.py <target-repo> --json
```

Treat the report as evidence, not as permission to publish everything it finds. The analyzer intentionally identifies candidates conservatively and does not rewrite the target repository.

Review:

- existing `skills/*/SKILL.md`
- `AGENTS.md`, `CLAUDE.md`, and agent directories
- workflow, playbook, command, prompt, recipe, and runbook content
- `.mcp.json`, `.app.json`, hooks, and existing plugin metadata
- scripts or services that imply runtime dependencies
- internal-only, unsafe, secret-bearing, proprietary, or organization-specific capabilities

## 2. Decide the public product boundary

A useful Plugin is not a dump of the repository.

For every candidate choose exactly one disposition:

- `preserve_skill`: already a coherent reusable Skill; repair only what the current contract requires
- `compile_skill`: convert a repeatable workflow into a focused Skill
- `reference_only`: useful support material that should be loaded only from an owning Skill
- `runtime_dependency`: behavior requires an MCP app/server or another declared runtime component
- `internal_only`: valuable internally but inappropriate, unsafe, secret-bearing, or too organization-specific for public distribution
- `discard`: implementation detail with no direct user workflow value

Record the reason for every `internal_only` and `discard` decision. Exclusion is part of product quality.

## 3. Choose architecture from behavior

Choose `skills-only` when the user value can be delivered from instructions, local scripts, references, and host capabilities without a required external service.

Choose `MCP-backed` when the core workflow requires external data, remote actions, authentication, or a server-side capability that a Skill cannot honestly provide alone.

Choose `hybrid` when reusable reasoning/process belongs in Skills while external data/actions belong in MCP-backed apps.

Never add MCP merely because the source repository contains a server, API client, or tool directory. Never force a remote dependency when the workflow is fully portable as a Skill.

## 4. Compile workflows into Skills

Use `workflow-to-skill-compiler` for each selected workflow.

A compiled Skill should have:

- one clear job
- a trigger-oriented `description` beginning with `Use when ...`
- instructions that preserve the source workflow's real decision logic
- progressive disclosure through `references/` when the source is large
- deterministic scripts under `scripts/` only when they add repeatable mechanical value
- no absolute local paths, hidden dependencies, copied secrets, or source-repository assumptions that will break after installation
- explicit stop conditions and evidence requirements where the source workflow depends on uncertain or current information

Do not mechanically convert one source file into one Skill. Merge fragments that serve one workflow and split source documents that contain multiple unrelated jobs.

## 5. Design the Plugin experience

Use `plugin-experience-architect` after candidate compilation.

Design from the user's job, not the source repository taxonomy. Decide:

- plugin name and listing promise
- which Skills deserve public discovery
- capability language
- starter prompts that represent valuable real tasks
- whether implicit invocation is appropriate per Skill
- optional vs required apps
- what users should understand before authenticating an external app

A Plugin with twenty technically valid Skills can be worse than one with four sharply differentiated workflows.

## 6. Validate the artifact

Run repository-native tests and the strict Autopilot preflight. Then package twice and compare bytes. A converter must not weaken the validator to make generated output pass.

## 7. Build the submission evidence

Use `submission-pack-builder` only after the exact artifact passes package preflight.

Keep separate statuses for:

- analyzed
- conversion planned
- locally validated
- submission ready
- submitted
- approved
- published

The submission pack should explain what the Plugin does for users, what runtime capabilities it needs, what was excluded from the source repository, how reviewers can test it, and what evidence supports each public claim.

## Conversion report contract

For serious conversions, leave a repository-maintained report such as `plugin-conversion-report.md` or an equivalent JSON artifact containing:

- source repository/ref
- analyzer report or summary
- candidate disposition table
- architecture decision and rationale
- public exclusions
- generated/modified files
- tests and validation evidence
- unresolved risks
- submission status

This report is not part of the public Plugin package unless deliberately included. It exists so maintainers can reproduce and audit the conversion later.

# Repo to Plugin Conversion Pipeline

Use this pipeline when the starting point is an agentic repository rather than an already-shaped ChatGPT/Codex Plugin.

## 1. Discover before converting

Run:

```bash
python3 <autopilot-skill>/scripts/analyze_repo.py <target-repo> --json
```

Treat the report as evidence, not permission to publish everything it finds. Review existing Skills, agent instructions, playbooks, prompts, commands, MCP/app configuration, hooks, runtime dependencies, and internal-only material.

The analyzer also emits a `hostWorkspace` profile for the generated Plugin and recommends installing the canonical workspace Skill for repository-oriented conversions.

## 2. Decide the public product boundary

For every candidate choose one disposition:

- `preserve_skill`
- `compile_skill`
- `reference_only`
- `runtime_dependency`
- `internal_only`
- `discard`

Record why anything is excluded. A useful Plugin is not a dump of the source repository.

## 3. Choose architecture from behavior

Choose `skills-only` when the user job can be delivered through Skills, references, local scripts, and host-native capabilities.

Choose `MCP-backed` when the core job genuinely requires external data, remote actions, authentication, or a server-side capability.

Choose `hybrid` when reusable reasoning/process belongs in Skills while external actions/data belong in an MCP-backed integration.

Host-native read/write/search/grep/shell/patch/Python operations do not by themselves make a Plugin MCP-backed.

## 4. Compile workflows into Skills

Use `workflow-to-skill-compiler`.

Preserve the workflow's real trigger, decisions, actions, validation, approvals, evidence, and stop conditions. Replace machine-specific assumptions with portable contracts.

When the source workflow interacts with files or code, describe operations by capability:

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

Do not invent Plugin manifest fields or Skill dependencies for host-native operations.

## 5. Design the Plugin experience and host capability profile

Use `plugin-experience-architect`.

Define:

- public Skill set and exclusions
- user-facing capability language
- starter prompts
- required/optional external apps
- direct/indirect/negative discovery tests
- host-workspace capability profile
- read-only vs mutation boundary
- whether Python execution materially improves verification

For repository/file-oriented Plugins, the normal baseline is read/list/search/grep for discovery, write/patch for authorized edits, shell for commands that require it, and Python for deterministic local work.

## 6. Install the workspace Skill

Run:

```bash
python3 <autopilot-skill>/scripts/install_host_workspace_skill.py <target-plugin>
```

This installs `skills/host-workspace-operator/` into the target Plugin.

The installer is deterministic and non-destructive:

- missing Skill -> install canonical copy
- identical Skill -> no-op
- customized existing Skill -> stop and require review

This Skill teaches the generated Plugin how to use host-native read/list/search/grep/write/patch/shell/Python capabilities when present. It does not grant those permissions.

## 7. Add host-native Python execution behavior

Use `sandbox-python-executor` when deterministic computation, parsing, hashing, archive inspection, file transformation, or package verification is part of the workflow.

In ChatGPT, when the **python tool** is available, execute the work with it. In Codex, use the safe host execution environment provided to the session.

Never claim execution when the tool is unavailable. Do not fabricate stdout, hashes, generated files, test results, or validation status.

## 8. Design the SVG brand pack

Use `plugin-brand-identity-designer` after the product boundary is stable.

Every Autopilot-prepared public Plugin should include:

```text
assets/logo-light.svg
assets/logo-dark.svg
assets/<composer-icon>.svg
```

Both logo variants share one core geometry and represent the actual Plugin job rather than generic AI imagery.

## 9. Build the Plugin Directory listing

Use `plugin-directory-listing-writer`, then run:

```bash
python3 <autopilot-skill>/scripts/build_directory_pack.py <target-plugin> --json
```

Prepare Name, Subtitle, Description, Category, verified Developer name, Website, Customer support, Privacy policy, Terms, Version, Package name, Capabilities, brand paths, and starter prompts.

Describe workspace/Python behavior accurately as host-dependent behavior. Do not claim the Plugin grants filesystem or execution permissions.

## 10. Validate the artifact

When host execution is available, actually run repository-native tests and Autopilot preflight instead of only printing commands.

Then package twice, compare bytes/hashes, extract a clean copy, and validate the extraction.

The generic gate includes:

```bash
python3 <autopilot-skill>/scripts/validate_plugin.py <target-plugin> --json
python3 <autopilot-skill>/scripts/build_directory_pack.py <target-plugin> --json
python3 <autopilot-skill>/scripts/package_plugin.py <target-plugin> /tmp/plugin-a.zip --json
python3 <autopilot-skill>/scripts/package_plugin.py <target-plugin> /tmp/plugin-b.zip --json
cmp /tmp/plugin-a.zip /tmp/plugin-b.zip
```

## 11. Build submission evidence

Use `submission-pack-builder` only after the exact artifact passes the relevant package, workspace, brand, listing, and execution gates.

Keep separate statuses for:

- analyzed
- conversion planned
- workspace ready
- brand ready
- listing ready
- locally validated
- submission ready
- submitted
- approved
- published

At the 2026-08-22 baseline, the official OpenAI submission flow asks for at least five positive and three negative reviewer cases. Re-check live requirements before submission.

## Conversion report contract

For serious conversions, preserve a repository-maintained report containing:

- source repository/ref
- analyzer summary
- candidate disposition table
- architecture decision
- host-workspace capability profile
- installed workspace Skill status
- mutation boundary
- public exclusions
- generated/modified files
- brand assets
- listing values and publisher/legal gaps
- direct/indirect/negative discovery tests
- executed verification evidence and skipped checks
- hashes/artifact identity when applicable
- unresolved risks
- submission state

This evidence report is not automatically part of the public Plugin package.

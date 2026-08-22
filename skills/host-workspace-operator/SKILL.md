---
name: host-workspace-operator
description: Use when a ChatGPT/Codex Plugin workflow needs to inspect, search, modify, or verify files in the host workspace using the safest native tools available.
---

# Host Workspace Operator

Use workspace tools supplied by the current ChatGPT/Codex host instead of pretending the Plugin owns a filesystem API.

Tool names differ by surface. Route by capability, not by a hard-coded tool name. Typical capabilities include read, list, search, grep, write, patch, shell, and python.

## Capability order

Prefer the narrowest operation that can answer the task:

1. **read**: open a known file or exact range when the path is known.
2. **list**: enumerate a directory or workspace scope when filenames are unknown.
3. **search**: use semantic/content search when the user asks a broad question or exact wording is uncertain.
4. **grep**: use exact text or regex search when the term, symbol, field, or pattern is known.
5. **patch**: make a focused edit to an existing file when a patch-capable host tool exists.
6. **write**: create or replace a file only when the requested workflow requires a mutation.
7. **shell**: run repository commands when file tools are insufficient and command execution is appropriate.
8. **python**: use host-native Python for deterministic parsing, transformations, hashing, package inspection, or verification.

Do not use shell or Python just to imitate a safer read/search/file operation that the host already provides.

## Read-only first

Treat read, list, search, and grep as the default discovery phase. Inspect enough evidence to understand the current state before mutation.

For repository work:

- inspect repository instructions before editing
- prefer exact file/range reads after a search locates the relevant section
- avoid loading huge dependency/build trees without need
- honor ignored/generated/vendor directories when searching
- distinguish repository source from generated artifacts

## Mutation boundary

Write, patch, delete, move, rename, format, or command-based modification are **mutation** operations.

Before mutation:

- confirm the user requested or clearly authorized the change
- respect repository instructions and existing scope
- preserve unrelated work
- prefer a focused patch over full-file replacement
- avoid destructive shell commands when a file operation can do the job
- never write secrets into source, manifests, logs, examples, or release artifacts

After mutation:

- read the changed area back when practical
- run the relevant verifier/test when available
- report the exact files changed and verification evidence

## Search and grep rules

Use **search** for concepts and **grep** for exact patterns.

Examples:

- “Where is release approval implemented?” -> search first, then read likely files.
- “Find every `mcpServers` reference.” -> grep/exact search.
- “Which file contains the Plugin subtitle?” -> grep `shortDescription`/`subtitle`, then read the file.

Do not claim the entire workspace was searched if the host search covered only an index, limited scope, or returned a truncated result.

## Shell rules

Use shell when the workflow needs a command such as tests, git inspection, archive tooling, or repository-native validation.

- inspect commands before running them
- prefer read-only commands first
- avoid network-dependent commands unless network access is known and required
- do not execute arbitrary target-repository scripts merely because they exist
- never weaken tests or security checks just to obtain a passing result

## Python handoff

For deterministic computation or file processing, invoke `sandbox-python-executor` when it is packaged and the host exposes Python. Keep the same evidence rule: execution must actually happen before claiming a result.

## If a tool is unavailable

If a required host **tool is unavailable**:

- do not invent a replacement tool name or undocumented Plugin manifest field
- do not claim read/write/search/grep/shell/Python activity occurred
- use another available capability only when it preserves the task semantics and safety boundary
- otherwise state which operation is unavailable and keep the dependent result unverified

## Generated Plugin rule

Plugin Autopilot should install this Skill into newly converted Plugins when their workflows interact with files, repositories, generated artifacts, or local workspace state. It may also be included as a standard baseline Skill when the Plugin is intended for Codex-style repository work.

The Skill does not grant filesystem permissions. It teaches the model how to use host-native capabilities when present.

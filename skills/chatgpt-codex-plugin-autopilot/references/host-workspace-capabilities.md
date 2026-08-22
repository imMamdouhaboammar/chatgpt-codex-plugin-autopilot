# Host Workspace Capability Contract

Checked against current OpenAI developer documentation on 2026-08-22.

Current OpenAI model/tool surfaces may provide capabilities such as file search, Code Interpreter/Python, hosted shell, apply patch, computer use, MCP, and other host-native tools. Availability differs by product, model, account, and session. The Plugin must not assume that a tool exists merely because another OpenAI surface documents it.

## Core rule

A Skill may instruct the model how to use host-native capabilities. It does not grant filesystem, shell, patch, search, or Python permissions by declaring arbitrary fields in `plugin.json` or `agents/openai.yaml`.

Do not invent manifest or Skill dependency fields for:

- read
- list
- search
- grep
- write
- patch
- shell
- Python / Code Interpreter

Use documented Plugin fields only. Where a documented MCP tool dependency is genuinely required, declare it according to the current Plugin contract. Host-native tools remain host-controlled.

## Capability model for generated Plugins

When converting a repository, Autopilot should decide whether the resulting Plugin benefits from these host-native operations:

| Capability | Typical job | Default boundary |
| --- | --- | --- |
| read | inspect a known file or range | read-only |
| list | inspect directory/workspace shape | read-only |
| search | semantic or broad content discovery | read-only |
| grep | exact text/regex/symbol lookup | read-only |
| write | create/replace content | mutation |
| patch | focused edit to existing content | mutation |
| shell | tests, git, archive/repository commands | depends on command |
| python | deterministic parsing, transformations, hashes, validation | local execution |

The generated Plugin should prefer the narrowest operation that solves the task. Read/search before mutation. Patch before broad file replacement. File tools before shell when shell adds no value. Python for deterministic computation rather than as a generic filesystem substitute.

## Generated baseline Skill

For Plugins whose workflows interact with repositories, local files, generated artifacts, or workspace state, Autopilot installs the canonical `host-workspace-operator` Skill:

```bash
python3 <autopilot-skill>/scripts/install_host_workspace_skill.py <target-plugin>
```

The installer:

- copies the reviewed canonical Skill and `agents/openai.yaml`
- is deterministic
- is idempotent when the installed copy is unchanged
- refuses to overwrite a customized existing copy

The Plugin can then adapt its domain Skills to invoke those capabilities while preserving one shared mutation/evidence policy.

## Read-only phase

Before changing a repository or file workspace:

1. inspect repository/user instructions
2. list only the required scope
3. search or grep to locate relevant files/sections
4. read exact files/ranges
5. establish the current state and affected surface

Do not claim exhaustive workspace coverage when the host search index, result cap, or mount scope is incomplete.

## Mutation phase

Treat write, patch, delete, move, rename, and mutating shell commands as state changes.

A generated Plugin should:

- mutate only when requested or clearly authorized
- preserve unrelated work
- avoid destructive shell operations when a focused file edit is sufficient
- read changed areas back when practical
- run relevant tests/validators when host execution exists
- report changed files and verification evidence

## Tool-unavailable behavior

If a host-native operation is unavailable:

- do not claim it ran
- do not fabricate file contents, search coverage, diffs, stdout, hashes, or test evidence
- use a semantically equivalent available capability only when safe
- otherwise state the unavailable operation and keep dependent conclusions unverified

## ChatGPT and Codex distinction

Codex commonly provides repository-oriented execution and editing capabilities. ChatGPT may expose different file/search/Python capabilities depending on the surface and current session. A portable Skill should therefore express intent by capability, while allowing the host to map that intent to the actual tool.

## API distinction

Applications built with the OpenAI API can explicitly provide hosted tools such as web search, file search, Code Interpreter, hosted shell, apply patch, MCP tools, or function tools when supported by the chosen model. That application-level tool configuration is different from a Plugin package installed inside ChatGPT/Codex.

Do not copy Responses API tool configuration fields into a Plugin manifest unless the current Plugin documentation explicitly defines them.

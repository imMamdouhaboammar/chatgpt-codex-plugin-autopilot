---
name: workflow-to-skill-compiler
description: Use when a repository has a valuable agentic workflow, prompt chain, playbook, command, or runbook that should become a portable ChatGPT/Codex Skill without losing its real decision logic.
---

# Workflow to Skill Compiler

Convert source workflows into portable Skills. Preserve behavior, not file shape.

## Compilation rules

1. Define one user job for the Skill. If the source mixes unrelated jobs, split it before conversion.
2. Trace the source workflow from trigger to evidence, decisions, actions, validation, and stop conditions.
3. Write Skill metadata for discovery. The `description` must say when to use the Skill, not merely what topic it contains.
4. Keep the main `SKILL.md` focused on execution. Move deep reference material into `references/` and deterministic mechanical helpers into `scripts/`.
5. Replace source-repository assumptions with portable contracts. Remove absolute paths, personal machine locations, private aliases, hidden environment assumptions, and undocumented dependencies.
6. Preserve meaningful gates. Do not flatten approval, safety, testing, evidence, or verification steps just to make the Skill shorter.
7. Prefer host capabilities over unnecessary bundled runtime code. Add MCP only when the workflow genuinely needs external data/actions that cannot be represented honestly as Skill guidance.
8. Keep tool names capability-oriented where possible so the Skill can travel across compatible hosts.
9. When the workflow touches files, repositories, generated artifacts, or local workspace state, integrate the `host-workspace-operator` contract. Prefer read/list/search/grep for discovery, patch/write only for authorized mutations, shell for repository commands, and `sandbox-python-executor` for deterministic Python work.
10. Add `agents/openai.yaml` only when interface metadata, product targeting, invocation policy, icons, or documented MCP tool dependencies materially improve the Skill. Do not invent dependencies for host-native filesystem, shell, patch, search, or Python tools.
11. Run public-distribution review before packaging. Internal workflows may contain capabilities that should never be mirrored into a public Skill.

## Workspace-capability compilation

When the source workflow includes operations such as:

- reading files
- listing directories
- searching concepts or filenames
- exact grep/regex lookup
- creating or editing files
- applying focused patches
- running tests or repository commands
- deterministic Python/file processing

represent those operations as host-native capability requirements in the Skill instructions. Do not hard-code one product's tool names unless the current host contract requires it.

For generated Plugins, the main Autopilot should install the canonical workspace Skill with:

```bash
python3 <autopilot-skill>/scripts/install_host_workspace_skill.py <target-plugin>
```

The installer is intentionally non-destructive. If the target already contains a customized `host-workspace-operator`, review it instead of overwriting it.

## Quality gate

Reject the compilation if:

- it is mostly a pasted prompt with no operating logic
- it cannot explain its trigger and completion condition
- it depends on files that will not exist after installation
- it silently drops source validation or approval gates
- multiple Skills are near-duplicates with different names
- the Skill description is so broad that it will collide with unrelated workflows
- generated instructions claim tools or permissions the Plugin does not actually provide
- mutation operations are mixed into read-only discovery without a clear authorization boundary
- the Skill says it searched, read, wrote, patched, ran shell, or executed Python without host evidence

## Handoff

After compilation, pass the Skill set and its workspace-capability needs to `plugin-experience-architect`. The experience brief should state which host-native operations the Plugin benefits from and which are mutation-capable. Then run the main Autopilot generation and validation gates.

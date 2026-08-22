---
name: agentic-repo-discovery
description: Use when an existing repository contains agents, prompts, workflows, playbooks, commands, or Skills and you need to identify which capabilities are worth converting into a ChatGPT/Codex Plugin.
---

# Agentic Repo Discovery

Find the reusable user workflows inside a repository before creating Plugin files.

## Procedure

1. Read repository instructions and the main README first.
2. Run the bundled analyzer when filesystem execution is available:

```bash
python3 ../chatgpt-codex-plugin-autopilot/scripts/analyze_repo.py <target-repo> --json
```

3. Inspect high-scoring candidates in context. The analyzer finds signals; it does not understand the full product by itself.
4. Build a candidate disposition table using: `preserve_skill`, `compile_skill`, `reference_only`, `runtime_dependency`, `internal_only`, or `discard`.
5. Identify the user's repeatable job for every candidate. Reject candidates whose only value is repository maintenance trivia unless that is the intended Plugin product.
6. Flag secrets, organization-specific instructions, destructive operations, security-sensitive workflows, hidden telemetry, and policy-sensitive capabilities for explicit public-distribution review.
7. Recommend `skills-only`, `MCP-backed`, or `hybrid` from actual behavior. Treat `.mcp.json` or `.app.json` as evidence to inspect, not automatic proof that the public Plugin needs them.
8. Hand selected workflow candidates to `workflow-to-skill-compiler` and the overall product boundary to `plugin-experience-architect`.

## Output

Return a concise conversion brief containing:

- repository/ref inspected
- reusable jobs discovered
- candidate dispositions with reasons
- architecture recommendation with confidence
- runtime dependencies
- public exclusions
- missing evidence
- next conversion actions

Do not generate Plugin configuration before this boundary is clear.

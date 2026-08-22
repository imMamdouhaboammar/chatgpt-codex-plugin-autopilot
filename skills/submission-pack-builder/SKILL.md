---
name: submission-pack-builder
description: Use when an exact ChatGPT/Codex Plugin artifact has passed local package validation and you need a reviewer-ready submission evidence pack without confusing preparation, submission, approval, and publication states.
---

# Submission Pack Builder

Prepare evidence for the exact validated artifact. Do not use submission copy to hide unresolved package or product problems.

## Preconditions

Require:

- exact plugin version/ref
- successful repository-native tests
- successful Autopilot package preflight
- deterministic package result when promised
- reviewed public Skill set and exclusions
- architecture decision: `skills-only`, `MCP-backed`, or `hybrid`

If the host also provides a dedicated Skill Submission Pack Writer, use it for the current portal-facing prose and field formatting after these evidence requirements are satisfied. This Skill remains the evidence contract and status gate.

## Build the pack

1. Re-check the current official OpenAI submission requirements.
2. Record the artifact SHA256 and source commit/ref.
3. Summarize the Plugin's user-facing job in plain language tied to actual packaged capabilities.
4. List each public Skill and any required/optional app dependency.
5. Record public exclusions from the source repository and why they were excluded.
6. Build reviewer test cases from real Plugin behavior. Positive cases should cover intended workflows; negative cases should show boundaries, refusal, or non-trigger behavior where relevant.
7. For MCP-backed/hybrid Plugins, document server/auth model, read/write behavior, sensitive actions, reviewer access requirements, tool annotations, and current production evidence required by the official submission flow.
8. Verify listing fields, branding, URLs, privacy/terms/support claims, and category against the exact artifact.
9. Record unresolved warnings instead of converting them into confident marketing language.
10. Emit one status only: `submission_ready` or `not_ready`, with blockers.

## Status discipline

Never use these as synonyms:

- `locally_validated`
- `submission_ready`
- `submitted`
- `approved`
- `published`

A reviewer packet proves preparation, not acceptance by OpenAI.

## Evidence output

The pack should contain or reference:

- source ref and artifact hash
- architecture
- listing fields
- Skill/app inventory
- reviewer test cases
- safety and public-exclusion notes
- privacy/terms/support URLs where applicable
- MCP review material where applicable
- validation evidence
- residual warnings
- exact submission state

Use `../chatgpt-codex-plugin-autopilot/references/submission-checklist.md` as the baseline and current official documentation as the authority.

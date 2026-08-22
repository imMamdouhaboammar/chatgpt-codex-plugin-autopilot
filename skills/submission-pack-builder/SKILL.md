---
name: submission-pack-builder
description: Use when an exact ChatGPT/Codex Plugin artifact has passed local package, brand, and listing gates and you need reviewer-ready submission evidence without confusing preparation, submission, approval, and publication states.
---

# Submission Pack Builder

Prepare evidence for the exact validated artifact. Do not use submission copy to hide unresolved package, brand, listing, or product problems.

## Preconditions

Require:

- exact Plugin version/ref
- successful repository-native tests
- successful Autopilot package preflight
- deterministic package result when promised
- reviewed public Skill set and exclusions
- architecture decision: `skills-only`, `MCP-backed`, or `hybrid`
- reviewed Plugin experience brief
- product-specific SVG brand pack with light and dark variants plus the declared small icon/composer asset
- successful directory listing pack with no blocking missing fields
- verified developer/business identity still confirmed in the OpenAI submission surface rather than inferred from repository metadata

If the host also provides a dedicated Skill Submission Pack Writer, use it for current portal-facing prose and field formatting after these evidence requirements are satisfied. This Skill remains the evidence contract and status gate.

## Build the pack

1. Re-check the current official OpenAI submission requirements.
2. Record the artifact SHA256 and source commit/ref.
3. Summarize the Plugin's user-facing job in plain language tied to actual packaged capabilities.
4. List each public Skill and any required/optional app dependency.
5. Record public exclusions from the source repository and why they were excluded.
6. Include the exact directory listing fields and brand asset paths used for the artifact. Do not substitute a draft listing from another ref or version.
7. Include discovery evidence from direct, indirect, and negative golden prompts when available. Record routing misses or ambiguous metadata instead of hiding them.
8. Build reviewer test cases from real Plugin behavior. Positive cases should cover intended workflows; negative cases should show boundaries, refusal, clarification, fallback, or non-trigger behavior where relevant.
9. At the repository's 2026-08-22 OpenAI baseline, require at least five positive and three negative reviewer cases. Re-check the live official requirement before every public submission.
10. For MCP-backed/hybrid Plugins, document server/auth model, read/write behavior, sensitive actions, reviewer access requirements, tool annotations, and current production evidence required by the official submission flow.
11. Verify listing fields, branding, URLs, privacy/terms/support claims, category, package name, version, and capabilities against the exact artifact.
12. Record unresolved warnings instead of converting them into confident public claims.
13. Emit one status only: `submission_ready` or `not_ready`, with blockers.

## Status discipline

Never use these as synonyms:

- `brand_ready`
- `listing_ready`
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
- public Skill/app inventory
- public exclusions
- brand rationale and exact light/dark/icon asset paths
- exact listing fields and field-limit checks
- developer identity verification status
- golden prompt set and discovery observations
- reviewer test cases
- privacy/terms/support URLs where applicable
- MCP review material where applicable
- validation and deterministic-package evidence
- residual warnings
- exact submission state

Use `../chatgpt-codex-plugin-autopilot/references/submission-checklist.md`, `../chatgpt-codex-plugin-autopilot/references/branding-and-listing.md`, and current official OpenAI documentation as the authority chain.

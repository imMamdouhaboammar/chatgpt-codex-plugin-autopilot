---
name: plugin-directory-listing-writer
description: Use when a validated ChatGPT/Codex Plugin needs accurate Plugin Directory fields, discovery metadata, starter prompts, and reviewer-facing listing details grounded in the packaged product.
---

# Plugin Directory Listing Writer

Turn the exact Plugin artifact into clear public listing metadata. Treat listing copy as product metadata that affects both user understanding and model discovery.

## Authority and freshness

Re-check the current official OpenAI Plugin submission, packaging, metadata, and guideline pages before finalizing a public listing. Portal fields and limits can change. Current official documentation overrides remembered limits and examples.

## Required listing pack

Prepare these fields when the current portal requires them:

- Name
- Subtitle / short description
- Description / long description
- Category
- Developer name / verified developer identity
- Website URL
- Customer support URL
- Privacy policy URL
- Terms of Service URL
- Version
- Package name
- Capabilities
- logo asset
- starter prompts
- availability notes when relevant
- release notes

Use `build_directory_pack.py` to extract package-backed fields and expose missing portal-only material. Do not silently invent missing publisher or legal information.

## Writing rules

### Name

Use the customer-facing product or workflow name. Do not expose internal repository slugs unless they are already the public brand.

### Subtitle

Describe the plain user function in one short line. Prefer a direct verb or outcome. Keep it within the current portal limit; when the form specifies 30 characters, enforce 30 characters rather than relying on a looser package limit.

Avoid claims such as "best", "perfect", "revolutionary", or unverifiable performance language.

### Description

Explain:

1. what users can do with the Plugin
2. which repeatable workflows it covers
3. what external data/actions it needs, if any
4. material boundaries users should understand

Write from observable packaged behavior. Do not convert implementation detail into customer value claims.

### Developer identity

The developer name must match the verified individual or business identity selected in the OpenAI Platform submission flow. Never infer a legal publisher name from a GitHub username, repository owner, email domain, or package author field.

### URLs

Require public, accurate URLs. The support, privacy, terms, and website pages must match the actual publisher and data handling. Missing URLs are blockers for submission readiness when the current portal requires them.

### Capabilities

Use short user-facing capability statements. Each capability should describe meaningful work the Plugin can actually perform. Remove duplicates and internal mechanics.

### Starter prompts

Create prompts for the highest-value workflows, not cosmetic variants of the same request. Include direct and indirect phrasing where helpful. Test them against the final Plugin.

## Discovery evaluation

Build a golden prompt set before final metadata sign-off:

- direct prompts that explicitly name the Plugin or workflow
- indirect prompts that describe the desired outcome
- negative prompts where the Plugin should not trigger

Record expected behavior for each prompt. Revise names/descriptions when recall or precision is poor rather than stuffing unrelated keywords into metadata.

## Submission test material

When current OpenAI submission requirements call for reviewer test cases, prepare at least the required positive and negative cases. As of the 2026-08-22 baseline used by this repository, the official portal asks for at least five positive and three negative cases. Re-check before every submission.

Each positive case should state:

- user prompt
- expected Skill/tool/workflow behavior
- expected result shape
- fixture or account data required

Each negative case should state:

- prompt/scenario
- expected refusal, clarification, or fallback
- why the Plugin should not complete the action

## Output

Produce a directory pack with:

- source commit/ref and version
- exact field values
- character-count checks where applicable
- asset paths
- starter prompts
- golden prompt evaluation set
- reviewer tests
- missing publisher/legal information
- claims that still need evidence
- status: `listing_ready` or `not_ready`

Hand the pack to `submission-pack-builder`. Listing readiness is not submission, approval, or publication.

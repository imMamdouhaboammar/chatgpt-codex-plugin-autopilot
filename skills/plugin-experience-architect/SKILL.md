---
name: plugin-experience-architect
description: Use when a set of candidate Skills or app capabilities is technically valid but still needs to become a clear, useful ChatGPT/Codex Plugin that people can understand, discover, and invoke for real work.
---

# Plugin Experience Architect

Design the Plugin around user jobs rather than the source repository's internal taxonomy.

## Product decisions

1. State the primary user and the recurring job the Plugin should help complete.
2. Group candidate Skills by distinct user outcome. Merge duplicates and remove implementation-only capabilities from public discovery.
3. Make Skill boundaries mutually understandable: each Skill should answer a different invocation question.
4. Decide which external apps are required, optional, or unnecessary. A Skill should not force authentication unless its workflow truly depends on external data or actions.
5. Write Plugin listing language from observable capability. Do not promise outcomes the packaged Skills/apps cannot provide.
6. Choose capabilities that describe meaningful work, not repository internals such as "JSON validation" unless that is itself a user-facing job.
7. Write starter prompts as concrete tasks a user would genuinely ask. Cover the Plugin's highest-value workflows without repeating the same request in different words.
8. Review implicit invocation policy per Skill. Narrow, low-risk workflows may be suitable for implicit discovery; sensitive or destructive workflows need tighter invocation boundaries.
9. Check the portfolio for discovery collisions, jargon, unexplained acronyms, and source-project naming that means nothing to a new user.
10. Keep the public surface intentionally smaller than the repository when that produces a clearer product.
11. Define the one product idea the brand mark should express. Describe the relationship/action visually without prescribing generic AI symbols.
12. Create a discovery test brief with direct, indirect, and negative prompt families before final listing copy is frozen.

## Decision test

For every public Skill, answer:

- Who needs this?
- What triggers it?
- What finished result does it produce?
- Why is this a separate Skill rather than part of another one?
- Does it require an app or runtime dependency?
- What could go wrong if it is invoked implicitly?
- What source evidence proves the workflow is real?

If these answers are weak, return the candidate to discovery/compilation instead of polishing the listing.

## Output

Produce a Plugin experience brief containing:

- primary audience and recurring job
- public Skill set and exclusions
- required/optional app dependencies
- Plugin promise grounded in packaged behavior
- capability list
- up to three starter prompt directions
- direct, indirect, and negative discovery-prompt directions
- invocation-policy notes
- one visual idea for the brand mark
- listing risks or unsupported claims

## Handoff order

Do not jump straight from product design to submission.

1. Hand the stable Plugin concept to `plugin-brand-identity-designer` for the light/dark SVG identity pack and compact composer/icon asset.
2. Hand the exact capabilities, starter prompts, brand paths, and discovery test brief to `plugin-directory-listing-writer`.
3. Run the main Autopilot package validator and `build_directory_pack.py` against the exact artifact.
4. Only after those gates pass, hand the artifact and evidence to `submission-pack-builder`.

If branding or listing work exposes a confused product boundary, return to this Skill instead of polishing around the problem.

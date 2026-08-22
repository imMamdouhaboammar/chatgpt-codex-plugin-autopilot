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
5. Define the host-workspace capability profile. Decide whether the Plugin benefits from read, list, search, grep, write, patch, shell, and Python, and distinguish read-only discovery from mutation-capable operations.
6. For Plugins that interact with files, repositories, generated artifacts, or local workspace state, include `host-workspace-operator` as a baseline Skill. For deterministic computation/file processing, pair it with `sandbox-python-executor` when appropriate.
7. Write Plugin listing language from observable capability. Do not promise outcomes the packaged Skills/apps or current host cannot provide.
8. Choose capabilities that describe meaningful user work, not internal mechanics. Host-native operations may support a capability without becoming the marketing headline.
9. Write starter prompts as concrete tasks a user would genuinely ask. Cover the Plugin's highest-value workflows without repeating the same request in different words.
10. Review implicit invocation policy per Skill. Narrow, low-risk workflows may be suitable for implicit discovery; sensitive or destructive workflows need tighter invocation boundaries.
11. Check the portfolio for discovery collisions, jargon, unexplained acronyms, and source-project naming that means nothing to a new user.
12. Keep the public surface intentionally smaller than the repository when that produces a clearer product.
13. Define the one product idea the brand mark should express. Describe the relationship/action visually without prescribing generic AI symbols.
14. Create a discovery test brief with direct, indirect, and negative prompt families before final listing copy is frozen.

## Host-workspace capability profile

Record each operation with one of these dispositions:

- `preferred`: the Plugin commonly needs the operation when the host provides it
- `optional`: useful for some workflows but not required for the core job
- `mutation`: changes workspace state and needs an explicit authorization boundary
- `not_needed`: should not be surfaced merely because a host may provide it

Assess at least:

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

Do not describe these as permissions granted by the Plugin. They are host-native capabilities the Skill can use when present.

If the Plugin performs repository work, default read/list/search/grep to the discovery phase. Treat write/patch and mutating shell commands as mutation operations. Use Python for deterministic local computation and verification, not as a generic substitute for narrower file/search tools.

## Decision test

For every public Skill, answer:

- Who needs this?
- What triggers it?
- What finished result does it produce?
- Why is this a separate Skill rather than part of another one?
- Does it require an app or runtime dependency?
- Which host-native read/search/mutation capabilities help complete it?
- What could go wrong if it is invoked implicitly?
- What source evidence proves the workflow is real?

If these answers are weak, return the candidate to discovery/compilation instead of polishing the listing.

## Output

Produce a Plugin experience brief containing:

- primary audience and recurring job
- public Skill set and exclusions
- required/optional app dependencies
- host-workspace capability profile
- mutation boundary for write/patch/shell actions
- whether `host-workspace-operator` should be installed
- whether `sandbox-python-executor` is needed
- Plugin promise grounded in packaged behavior
- capability list
- up to three starter prompt directions
- direct, indirect, and negative discovery-prompt directions
- invocation-policy notes
- one visual idea for the brand mark
- listing risks or unsupported claims

## Handoff order

Do not jump straight from product design to submission.

1. If the target Plugin uses local files or repository state, install the canonical workspace Skill with `install_host_workspace_skill.py`. Do not overwrite an existing customized version without review.
2. Hand the stable Plugin concept to `plugin-brand-identity-designer` for the light/dark SVG identity pack and compact composer/icon asset.
3. Hand the exact capabilities, starter prompts, brand paths, host-workspace profile, and discovery test brief to `plugin-directory-listing-writer`.
4. Run the main Autopilot package validator and `build_directory_pack.py` against the exact artifact.
5. Only after those gates pass, hand the artifact and evidence to `submission-pack-builder`.

If workspace capability planning, branding, or listing work exposes a confused product boundary, return to this Skill instead of polishing around the problem.

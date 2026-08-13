# Public Plugin Submission Checklist

Use this after the package itself passes local validation. Package validity and public directory readiness are separate gates.

Re-check the official OpenAI submission documentation before every public submission. This checklist was verified on 2026-08-13.

## Gate 1: Package identity and shape

- `.codex-plugin/plugin.json` exists and is the only entry inside `.codex-plugin/`
- plugin `name`, strict semver `version`, description, author, and final listing metadata pass the current limits
- `interface.logo` and `interface.composerIcon` reference real square package assets
- every immediate child of `skills/` intended for import is a real directory containing `SKILL.md`
- Skill names are unique within the plugin and combined plugin/Skill identities fit the current limit
- optional `agents/openai.yaml` files use the documented Skill interface metadata shape
- `.app.json` is declared only when the package intentionally references registered app/MCP mappings
- `.mcp.json` is declared only when the package intentionally distributes bundled MCP server configuration
- all declared asset and component paths are relative, package-contained, and free of traversal
- no secrets, local user paths, transient bytecode, operating-system metadata, symlinks, or excluded internal capabilities are present

## Gate 2: Product classification

Choose one architecture from actual requirements, not from files that happen to exist in the repository:

- Skills-only: reusable instructions/workflows with no required MCP capability
- MCP-backed: external tools or service capability provided through MCP
- Hybrid: bundled Skills plus MCP capability

A root `.app.json` or `.mcp.json` that is not declared by the manifest is ignored by the package importer. Treat that as a warning and confirm whether the file should be removed or declared.

## Gate 3: Final directory listing

Prepare the current public listing fields before submission:

- display name
- short description
- long description
- developer name
- supported category
- capabilities where used
- starter prompts where used
- logo and composer icon
- public website, support, privacy policy, and terms links required by the submission form

Keep final-directory limits stricter than package-upload limits. Do not tune copy against only permissive package limits.

## Gate 4: Publisher and policy readiness

- developer or business identity is verified as required by the current OpenAI Platform flow
- the submitter has the required plugin submission permission for the publishing organization
- required policy attestations are complete
- every bundled Skill is ready for the platform safety/security scan
- privacy and terms copy match the product's actual behavior
- public capabilities do not include material intentionally excluded after moderation or security review

## Gate 5: Reviewer tests and submission material

Every public plugin submission, including Skills-only plugins, needs reviewer material that can be reproduced without private context.

Prepare at least five positive test cases. Each must include:

- user prompt
- expected tool, Skill, or workflow behavior
- expected result shape
- test account or fixture data required to reproduce it

Prepare at least three negative test cases. Each must include:

- user prompt or scenario
- expected refusal, clarification, or safe fallback behavior
- why the plugin should not complete the requested action

Also prepare realistic starter prompts, country or region availability, and release notes for the exact version being submitted.

This repository keeps a reviewer-oriented copy of those materials in `submission/reviewer-packet.json`. It is a repository convenience file, not an OpenAI-defined upload schema.

## Gate 6: MCP-backed additions

Only when the plugin is MCP-backed, prepare the extra server review material required by the current submission flow, including:

- production HTTPS MCP server URL
- current domain verification
- successful current tool scan
- explicit tool annotations for read-only, open-world, and destructive behavior
- content security policy when the plugin has UI
- demo credentials when authentication is required, in the reviewer-safe form currently accepted by OpenAI

Do not add an MCP server merely to make a Skills-only plugin look more complete. Architecture must reflect actual product behavior.

## Gate 7: Artifact proof

Before upload:

1. run repository-native tests
2. run `validate_plugin.py`
3. build the plugin artifact twice from the same source
4. require byte-identical output and matching SHA256
5. inspect archive entries and compressed/uncompressed limits
6. extract into a fresh directory
7. rerun the validator against the extracted copy
8. smoke the install or local marketplace path when the available host supports it
9. use the same final Skill tree in the submission draft that passed local tests

## Gate 8: State reporting

Report publication state precisely:

- package prepared
- locally validated
- submitted
- under review
- approved
- failed or rejected
- published

A green CI run, GitHub Release, valid ZIP, local installation, or workspace publication is not evidence that OpenAI approved the universal public Plugins Directory submission.

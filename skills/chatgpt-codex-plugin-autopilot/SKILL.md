---
name: chatgpt-codex-plugin-autopilot
description: Use when building, repairing, validating, packaging, submitting, publishing, or auditing a ChatGPT/Codex Plugin in any repository. Handles skills-only, MCP-backed, hybrid plugins, strict package preflight, Plugin Directory readiness, moderation-safe public packaging, deterministic ZIPs, and Full Autopilot Publish.
---

# ChatGPT/Codex Plugin Autopilot

Take an arbitrary repository from discovery to a verified ChatGPT/Codex Plugin artifact and, when explicitly authorized, through release/submission. Treat the target repository as authoritative for product behavior and release channels. Never require Riqor, Bun, Node, or a project-specific layout unless the target already requires it.

## Operating contract

1. Verify the current official OpenAI Plugin and Skill documentation before editing public plugin configuration. Current official docs override remembered schema, examples, and numeric limits. Read `references/official-contract.md` and record the verification date.
2. Inspect repository instructions, dirty state, package metadata, manifests, Skills, MCP/app configuration, hooks, assets, legal/support pages, CI, tags, release scripts, and registry policy before changing anything.
3. Classify the target using `references/architectures.md` as `skills-only`, `MCP-backed`, or `hybrid`. Classify from declared active components and actual product behavior, not from stray `.app.json` or `.mcp.json` files.
4. Run a public-distribution safety review before generating or packaging public Skills. Internal capability does not imply Plugin Directory suitability.
5. Build or repair `.codex-plugin/plugin.json`, focused Skills, optional `agents/openai.yaml`, optional MCP/app configuration, optional hooks, square branding, and accurate public URLs.
6. Enforce package shape before copywriting polish: only `plugin.json` inside `.codex-plugin/`; every intended Skill as an immediate real child directory of `skills/` with `SKILL.md`; no direct files or symlinks under `skills/` that are expected to import as Skills.
7. Validate declared asset text as well as resolved files. Reject outer whitespace, control characters, absolute/drive paths, `..` traversal, package escapes, missing files, and invalid required branding dimensions.
8. Validate `agents/openai.yaml` when present. Require its documented `interface` metadata and validate supported policy/dependency fields without pretending the local dependency-free checker replaces the official YAML/uploader implementation.
9. Treat `.app.json` and `.mcp.json` as active only when the manifest declares `apps` or `mcpServers` respectively. Warn on undeclared root files because OpenAI ignores them. Validate declared mappings structurally before packaging.
10. Apply final Plugin Directory limits, not only looser package-validation limits. Keep category, listing copy, starter prompts, URLs, branding, and capabilities within the current final rules.
11. Run repository-native tests plus `scripts/validate_plugin.py` and fail closed on every blocking local preflight error.
12. Build the ZIP twice with `scripts/package_plugin.py` and require byte-identical SHA256 results. Extract a fresh copy and validate the extraction again.
13. Inspect archive root, files, counts, excluded capabilities, secrets/privacy boundary, package-relative paths, and installation behavior.
14. Smoke a fresh install on every available ChatGPT/Codex surface. Prefer a repo/personal local marketplace when available and test the installed cached copy in a new chat. Do not claim unavailable surfaces were tested.
15. Run the separate submission-readiness gate in `references/submission-checklist.md`. A valid ZIP is not automatically ready for public review.
16. Diagnose uploader or review failures using `references/submission-errors.md`; repair root causes and every generated/runtime reference, then rerun the complete gate.
17. Under Full Autopilot Publish, commit, tag, push, publish, and create releases without another routine confirmation only after all gates pass and only within the user's authorized release scope. Follow `references/release-playbook.md`.
18. Download published artifacts and compare hashes or bytes whenever the channel supports deterministic identity. Report exact commit, tag, versions, hashes, test evidence, remote checks, directory state, and any residual warning.

## Package preflight vs submission readiness

Keep these as separate decisions.

### Package preflight

Answers: is this plugin artifact structurally safe, importable, deterministic, and internally consistent?

Check at minimum:

- `.codex-plugin/plugin.json` is present and alone in its manifest directory
- declared component paths are safe and point to the documented root locations
- required logo and composer icon are square valid package images
- `skills/` contains importable Skill directories, not loose intended Skill files
- Skill frontmatter/body/identity are valid and Skill names are unique
- optional Skill `agents/openai.yaml` is structurally valid
- declared app/MCP files are structurally valid; undeclared files do not affect architecture
- package contains no secret-shaped files, transient bytecode, symlinks, excluded capabilities, normalization collisions, or local absolute user paths
- deterministic packager produces the same bytes from the same source

### Submission readiness

Answers: can this exact artifact and product enter the current public OpenAI review flow with the required listing and review material?

Use `references/submission-checklist.md`. Verify publisher identity/policy state, final listing fields, Skill scans, and the additional MCP review material when the plugin is MCP-backed.

Never collapse `locally validated`, `submitted`, `approved`, and `published` into one status.

## Public-distribution safety gate

Review every public Skill name, description, instructions, references, generated native-agent copy, profile registration, routing index, capability label, and packaged executable behavior for usage-policy and moderation risk. Never blindly mirror all internal agents into a public plugin.

When a capability must stay internal, place the exclusion at the canonical generation or packaging boundary. Remove every public replica and registration, including generated Skill directories, reference instructions, native-agent copies, profile entries, maps, indexes, manifest counts/copy, runtime mirrors, and archive entries. Regeneration must not restore an excluded capability.

Pass each excluded slug to the validator:

```bash
python3 <skill-root>/scripts/validate_plugin.py <plugin-root> --exclude <slug> --json
```

A stale excluded slug in any public path or UTF-8 text file is a blocking failure.

## Strict generic preflight

```bash
python3 <skill-root>/scripts/validate_plugin.py <plugin-root> --json
python3 <skill-root>/scripts/package_plugin.py <plugin-root> /tmp/plugin-a.zip --json
python3 <skill-root>/scripts/package_plugin.py <plugin-root> /tmp/plugin-b.zip --json
cmp /tmp/plugin-a.zip /tmp/plugin-b.zip
unzip -Z1 /tmp/plugin-a.zip
```

Then extract the ZIP into a clean directory and rerun `validate_plugin.py` against the extraction.

Keep repository-native quality, security, domain acceptance, smoke, and release checks in addition to this generic gate. Generic plugin tooling does not replace project-specific validation, the official uploader, Skill safety scans, or MCP review.

## Learned failure patterns that must stay covered

These are regression contracts, not anecdotes:

- a loose `skills/registry.json` can exist in a repository yet be ignored by Skill import; move registry/config under an owning Skill or another valid location and migrate every consumer
- missing `interface.logo` or `interface.composerIcon` blocks directory branding validation; both must resolve to square assets
- a path such as `./assets/../assets/icon.svg` can resolve inside the package but is still an unsafe declaration because it contains traversal
- extra files inside `.codex-plugin/` are misplaced even if harmless to the repository
- undeclared `.app.json` / `.mcp.json` do not activate app/MCP capability
- Skill metadata `name` and folder slug are not the same contract; enforce identity uniqueness and limits, not an invented equality rule
- `agents/openai.yaml` is a separate Skill interface surface and must be validated when bundled
- a local marketplace/install success is useful evidence but not public directory approval

## Stop conditions

Stop before irreversible publication when current required OpenAI rules cannot be verified, repository identity is ambiguous, required credentials are unavailable, tests or validation fail, the target version already exists on an immutable registry, archive identity is nondeterministic when determinism is promised, public policy copy contradicts behavior, the public submission surface requires evidence that cannot be produced honestly, or the requested action exceeds the user's authorized scope.

Do not weaken tests, hide uploader failures, rewrite released tags, inject registry credentials into CI, force-push unrelated history, or claim a successful Plugin Directory submission when only a local ZIP was prepared.

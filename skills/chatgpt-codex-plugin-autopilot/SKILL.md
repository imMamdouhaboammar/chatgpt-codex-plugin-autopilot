---
name: chatgpt-codex-plugin-autopilot
description: Use when converting an agentic repository into a ChatGPT/Codex Plugin or when building, repairing, validating, packaging, submitting, publishing, or auditing an existing Plugin.
---

# ChatGPT/Codex Plugin Autopilot

Take an arbitrary repository from agentic-workflow discovery to a verified ChatGPT/Codex Plugin artifact and, when explicitly authorized, through release/submission. This repository is itself a ChatGPT/Codex Plugin and must remain capable of validating and packaging its own installed surface.

Treat the target repository as authoritative for product behavior and release channels. Never require Riqor, Bun, Node, or a project-specific layout unless the target already requires it.

## Operating contract

1. Verify the current **official OpenAI Plugin** and Skill documentation before editing public configuration. Current official docs override remembered schema, examples, limits, and tool availability. Read `references/official-contract.md`, `references/branding-and-listing.md`, `references/host-python-sandbox.md`, and `references/host-workspace-capabilities.md`.
2. Inspect repository instructions, package metadata, manifests, Skills, agents, workflows, MCP/app configuration, hooks, assets, legal/support pages, CI, release scripts, tags, and public-distribution constraints before changing anything.
3. When the repository is not already a coherent Plugin, run Repo-to-Plugin conversion first. Use `scripts/analyze_repo.py` plus `agentic-repo-discovery` to identify candidate workflows and set the public boundary.
4. Classify the target as `skills-only`, `MCP-backed`, or `hybrid` from declared active components and actual user behavior, not from stray `.app.json` or `.mcp.json` files.
5. Run the **public-distribution safety** review before mirroring internal capabilities into public Skills.
6. Compile selected workflows with `workflow-to-skill-compiler`. Preserve decisions, approvals, tests, evidence, and stop conditions.
7. Build the host-workspace capability profile with `plugin-experience-architect`. Decide whether the Plugin needs read, list, search, grep, write, patch, shell, and Python. Keep read-only discovery separate from mutation operations.
8. For Plugins that interact with files, repositories, generated artifacts, or workspace state, install the canonical `host-workspace-operator` Skill with `scripts/install_host_workspace_skill.py`. Do not overwrite a customized existing copy without review.
9. When deterministic computation, parsing, hashing, archive inspection, or Python-based verification is useful, include and invoke `sandbox-python-executor`. In ChatGPT, explicitly use the **python tool** when it is available. Do not claim execution without execution evidence.
10. Build or repair `.codex-plugin/plugin.json`, focused Skills, optional `agents/openai.yaml`, optional MCP/app configuration, optional hooks, square branding, and accurate public URLs.
11. For public preparation, require the product-specific SVG brand pack from `plugin-brand-identity-designer`: `assets/logo-light.svg`, `assets/logo-dark.svg`, and a compact square icon.
12. Build truthful public metadata through `plugin-directory-listing-writer`: Name, Subtitle, Description, Category, verified Developer name, Website, Customer support, Privacy policy, Terms, Version, Package name, Capabilities, starter prompts, and reviewer material.
13. Enforce package shape before copy polish. Only `plugin.json` belongs inside `.codex-plugin/`; every intended Skill is an immediate real child directory of `skills/` containing `SKILL.md`.
14. Validate declared paths and assets. Reject outer whitespace, control characters, absolute paths, drive paths, `..` traversal, package escapes, missing files, invalid square branding, secret-shaped files, transient bytecode, and symlinks.
15. Validate `agents/openai.yaml` when present. Do not invent dependencies for host-native read/write/search/grep/shell/patch/Python capabilities. Documented Skill dependencies remain limited to the current official contract.
16. Treat `.app.json` and `.mcp.json` as active only when the manifest declares the matching component.
17. Run repository-native tests plus `scripts/validate_plugin.py` and fail closed on blocking errors. When the host provides execution tools, **execute the checks**; do not merely print commands and describe them as verified.
18. Build the ZIP twice with `scripts/package_plugin.py` and require deterministic byte identity or matching SHA256. Extract a fresh copy and validate it again.
19. Inspect archive contents, excluded capabilities, secret/privacy boundaries, package-relative paths, installation behavior, and generated workspace Skills.
20. Smoke a fresh install on every available ChatGPT/Codex surface. Do not claim unavailable surfaces were tested.
21. Run the separate submission-readiness gate. A valid ZIP, logo, listing, or successful local install is not OpenAI approval.
22. Diagnose uploader/review failures from the current official docs and `references/submission-errors.md`; fix root causes and rerun the entire gate.
23. Under **Full Autopilot Publish**, commit, tag, push, publish, and create releases without another routine confirmation only after all gates pass and only within the user's authorized release scope.
24. Report exact commit, tag, version, hashes, executed tests, skipped checks, remote status, and residual warnings.

## Repo-to-Plugin conversion mode

### Stage A: discover

Run:

```bash
python3 <autopilot-skill>/scripts/analyze_repo.py <target-repo> --json
```

Use `agentic-repo-discovery` to assign each candidate one disposition:

```text
preserve_skill
compile_skill
reference_only
runtime_dependency
internal_only
discard
```

Do not treat discovery as automatic publication.

### Stage B: compile workflows

Use `workflow-to-skill-compiler`. One source file does not have to become one Skill. Merge fragments serving one job, split mixed workflows, and keep private or unsafe capabilities out of the public package.

When a workflow touches local files or code, express its operations using host capabilities rather than one hard-coded tool implementation.

### Stage C: design the Plugin experience

Use `plugin-experience-architect` to define:

- primary user and recurring job
- public Skill set and exclusions
- required/optional app dependencies
- capability language and starter prompts
- invocation boundaries
- host-workspace capability profile
- mutation boundary
- whether `host-workspace-operator` should be installed
- whether `sandbox-python-executor` is needed

### Stage D: install the host workspace baseline

For repository/file-oriented Plugins, run:

```bash
python3 <autopilot-skill>/scripts/install_host_workspace_skill.py <target-plugin>
```

The generated Plugin receives a portable Skill covering:

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

These are host-native capabilities, not permissions granted by the Plugin. The Skill maps intent to whichever compatible tools the current ChatGPT/Codex host exposes.

Default behavior:

- read/list/search/grep first for discovery
- patch before broad rewrite when available
- write only for authorized mutation
- shell for repository commands when narrower tools are insufficient
- Python for deterministic computation and verification
- no fabricated tool use when a capability is unavailable

The installer is idempotent and refuses to overwrite a customized existing `host-workspace-operator`.

### Stage E: execute in the host sandbox

Use `sandbox-python-executor` when a claim depends on real local computation, package inspection, hashing, file transformation, or the bundled Python validators/packagers.

In ChatGPT, when the **python tool** is available, use it. In Codex, use the safe host execution environment available to the session. Preserve execution evidence such as status, important output, generated file paths, and hashes.

If the required tool is unavailable, state that limitation and keep execution-dependent claims unverified.

### Stage F: design the brand identity

Use `plugin-brand-identity-designer` after the product boundary is stable. Create product-specific light/dark SVG variants sharing one geometry plus a small icon. Do not invent unsupported manifest fields for extra variants.

### Stage G: build the Plugin Directory listing

Use `plugin-directory-listing-writer`, then run:

```bash
python3 <autopilot-skill>/scripts/build_directory_pack.py <target-plugin> --json
```

Missing verified publisher/legal information is a blocker, not a copywriting opportunity.

### Stage H: prove and prepare submission

Run package preflight, deterministic packaging, clean extraction validation, reviewer tests, and discovery checks. Only then use `submission-pack-builder`.

Keep these states separate:

```text
analyzed
conversion planned
workspace ready
brand ready
listing ready
locally validated
submission ready
submitted
approved
published
```

## Host workspace operations rule

`host-workspace-operator` is the shared execution policy for local workspace work.

Use the narrowest available capability:

- `read`: known file/range
- `list`: directory/workspace shape
- `search`: broad or semantic discovery
- `grep`: exact text, regex, symbol, or field lookup
- `patch`: focused existing-file edit
- `write`: create/replace content when authorized
- `shell`: tests, git, archive, or repository commands
- `python`: deterministic parsing, transformations, hashes, and validation

Read-only operations should establish the current state before mutations. Write, patch, delete, move, rename, formatting changes, and mutating shell commands are state changes and must respect the user's authorization and repository instructions.

A generated Skill must never say it searched, read, wrote, patched, ran shell, or executed Python unless the current host actually produced evidence of that action.

See `references/host-workspace-capabilities.md`.

## Host-native Python rule

`sandbox-python-executor` is an execution policy around host capabilities supplied by ChatGPT/Codex. It is not an MCP server and does not grant a Python tool.

When Python is available and materially improves correctness:

- execute deterministic work instead of mental simulation
- prefer bundled reviewed scripts when they already implement the check
- keep target-repository access read-only by default
- inspect untrusted target scripts before running them
- do not assume sandbox internet access
- return execution evidence

When unavailable, do not claim tests, validation, packaging, hashes, or generated files were executed.

See `references/host-python-sandbox.md`.

## Package preflight

Check at minimum:

- `.codex-plugin/plugin.json` is present and alone in its manifest directory
- declared component paths are safe and point to documented root locations
- required logo and composer icon are valid square images
- public Autopilot-produced Plugins contain committed light/dark SVG variants
- every direct child under `skills/` is a valid Skill directory
- `host-workspace-operator` is present when the Plugin's conversion plan requires local workspace operations
- Skill frontmatter/body/identity are valid and names are unique
- optional `agents/openai.yaml` is valid
- declared app/MCP files are structurally valid; undeclared root files do not alter architecture
- package contains no secrets, bytecode, symlinks, excluded capabilities, normalization collisions, or local absolute user paths
- deterministic packager produces the same bytes from the same source

## Submission readiness

Use `references/submission-checklist.md` plus current official documentation. Verify publisher identity, listing fields, brand assets, public Skill inventory, host-capability claims, starter prompts, required reviewer cases, and MCP review material when applicable.

Never collapse `locally validated`, `submitted`, `approved`, and `published` into one status.

## Public-distribution safety gate

Review every public Skill name, description, instruction, reference, generated copy, capability label, and packaged executable behavior. Never blindly mirror all internal agents into a public Plugin.

When a capability must stay internal, remove every public replica, registration, generated Skill, runtime mirror, reference, index entry, and archive entry. Regeneration must not restore it.

Pass excluded slugs to the validator:

```bash
python3 <autopilot-skill>/scripts/validate_plugin.py <plugin-root> --exclude <slug> --json
```

## Strict generic preflight

When execution is available, actually run:

```bash
python3 <autopilot-skill>/scripts/validate_plugin.py <plugin-root> --json
python3 <autopilot-skill>/scripts/build_directory_pack.py <plugin-root> --json
python3 <autopilot-skill>/scripts/package_plugin.py <plugin-root> /tmp/plugin-a.zip --json
python3 <autopilot-skill>/scripts/package_plugin.py <plugin-root> /tmp/plugin-b.zip --json
cmp /tmp/plugin-a.zip /tmp/plugin-b.zip
unzip -Z1 /tmp/plugin-a.zip
```

Then extract to a clean directory and rerun `validate_plugin.py` against the extraction.

Repository-native quality, security, domain acceptance, and smoke checks remain additional gates.

## Learned failure patterns that must stay covered

- a loose `skills/registry.json` can be ignored by Skill import; move intended metadata under a valid owner and migrate consumers
- missing `interface.logo` or `interface.composerIcon` blocks directory branding validation
- a path such as `./assets/../assets/icon.svg` is unsafe even if it resolves inside the package
- extra files inside `.codex-plugin/` are misplaced
- undeclared `.app.json` / `.mcp.json` do not activate app/MCP capability
- Skill metadata `name` and directory slug are separate contracts
- `agents/openai.yaml` must be validated when bundled
- host-native read/write/search/grep/shell/patch/Python capabilities must not be represented as invented manifest dependencies
- a local install is evidence, not public directory approval
- GitHub/package authorship is not proof of verified OpenAI developer identity
- a good-looking logo or complete listing is not proof of technical validity
- a Plugin Skill can require execution behavior but cannot fabricate host tool availability

## Stop conditions

Stop before irreversible publication when required OpenAI rules cannot be verified, repository identity is ambiguous, credentials are unavailable, tests/validation fail, a target immutable version already exists, package identity is nondeterministic when determinism is promised, public copy contradicts behavior, publisher/legal listing facts are missing, reviewer evidence cannot be produced honestly, or the requested action exceeds authorization.

Do not weaken tests, hide uploader failures, rewrite released tags, inject registry credentials into CI, force-push unrelated history, overwrite customized workspace Skills without review, claim tool execution that did not occur, or claim Plugin Directory publication when only a local artifact was prepared.

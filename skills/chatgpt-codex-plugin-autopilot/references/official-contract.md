# Official OpenAI Plugin Contract Baseline

Checked against official OpenAI documentation on 2026-08-13. Re-check these pages at the start of every public plugin task because package and submission rules can change:

- https://developers.openai.com/plugins/concepts/plugins
- https://developers.openai.com/plugins/concepts/skills
- https://developers.openai.com/plugins/build/plugins
- https://developers.openai.com/plugins/deploy/submission-errors
- https://developers.openai.com/plugins/deploy/submission

Current official documentation is authoritative over this snapshot.

## Plugin package shape

Every plugin uses `.codex-plugin/plugin.json` as the native manifest entry point. Only `plugin.json` belongs inside `.codex-plugin/`.

Plugin-root resources may include:

```text
.codex-plugin/plugin.json
skills/
hooks/
.app.json
.mcp.json
assets/
```

Keep declared component paths relative to the plugin root and `./`-prefixed where the manifest expects paths. `skills` points to the root `skills/` directory, `mcpServers` points to `./.mcp.json`, `apps` points to `./.app.json`, and hook paths follow the same package-relative safety rules.

Public plugins are published to the universal Plugin Directory shared by ChatGPT and Codex. Repo or personal marketplaces are authoring, testing, and private/team distribution surfaces; a local install is not evidence of public-directory acceptance.

## Skills

A Skill is an immediate child directory of `skills/` with a required regular `SKILL.md` file. Supporting files may live inside the Skill, including `scripts/`, `references/`, `assets/`, and `agents/openai.yaml`.

Files or symlinks directly under `skills/` are not imported as Skills. Plugin Autopilot treats those ignored entries as a strict-preflight failure so intended capabilities cannot silently disappear from a release artifact.

`SKILL.md` needs YAML front matter with non-empty `name` and `description`, followed by non-empty instructions. The combined `plugin-name:skill-name` identity must fit the current limit, and Skill names must be unique within one plugin. OpenAI normalizes outer/internal whitespace during import. The Skill metadata name does not need to equal the directory name under the current documented contract.

ChatGPT and Codex initially discover Skills from metadata and load the full instructions after selection. Keep discovery copy precise and trigger-oriented rather than making every Skill generic.

## Skill agent metadata

A Skill may define `skills/<skill>/agents/openai.yaml`. This is separate from the plugin manifest `interface` and uses snake_case fields.

When the file is present:

- top level is a YAML mapping
- `interface` is required
- `interface.display_name` and `interface.short_description` are required and non-empty
- `interface.icon_small` and `interface.icon_large` are optional relative asset paths
- `interface.brand_color` is an optional six-digit hex color
- `interface.default_prompt` is optional and non-empty when provided
- `policy` is optional and supports `products` plus `allow_implicit_invocation`
- `products` may contain `CHAT`, `CODEX`, or both
- `allow_implicit_invocation` is boolean
- `dependencies` is optional and currently supports `tools`

Do not put Skill interface settings in `metadata` inside `SKILL.md`; the documented interface location is `agents/openai.yaml`.

## Manifest and final-directory metadata

Use strict semver for `version`. Plugin name is limited to the current supported ASCII identifier form and length. Description and author metadata must satisfy package validation.

For final public directory submission, use the stricter listing limits rather than only package-upload limits:

- `interface.displayName`: required, one line, <= 30 characters
- `interface.shortDescription`: required, one line, <= 30 characters
- `interface.longDescription`: required, <= 4,000 characters
- `interface.developerName`: required, one line, <= 80 characters
- `interface.category`: required, supported category
- `interface.capabilities`: at most 20 items, each non-empty, one line, <= 120 characters
- `interface.defaultPrompt`: at most 3 prompts, unique after normalization, one line, <= 128 characters, no app `@mention`
- final listing URLs: HTTPS and <= 1,024 characters
- `interface.brandColor` / `brandColorDark`: optional six-digit hex colors with current contrast requirements

Website, support, privacy, and terms URLs are required for MCP-backed public submissions and optional for skills-only submissions under the current final-directory rules. For a serious skills-only product, stable accurate URLs remain a good default when the product actually has them.

## Branding and declared assets

`interface.logo` and `interface.composerIcon` are required for directory submission and must reference square images.

Supported branding formats are PNG, JPG/JPEG, WebP, and SVG. Images must stay within the current file-size and dimension limits. SVG must be valid UTF-8 XML with an `<svg>` root and numeric positive square dimensions.

Declared asset paths must:

- be strings
- be non-empty
- contain no outer whitespace or control characters
- remain relative to the plugin package
- contain no absolute path, drive prefix, or `..` traversal segment
- resolve to a real package file

Manifest branding assets should use `./`-prefixed paths. Screenshots are package assets too and should be validated as declared paths.

## App references

`.app.json` is a compatibility mapping for registered MCP server connections. It is imported only when `plugin.json` declares:

```json
"apps": "./.app.json"
```

An undeclared root `.app.json` is ignored.

For local/workspace packages, `.app.json` uses a top-level `apps` object. Each alias maps to an object with a required string `id`; optional `optional` and `required` values must be booleans when supplied. The official submission error reference defines the current accepted ID families. The package/build documentation also documents current `plugin_asdk_app...` developer-mode IDs, so re-check both pages when validating a newly generated mapping.

A public skills-only submission does not publish a reference to an existing ChatGPT app. An MCP-backed public submission uses the MCP submission route and submits the MCP server integration directly.

## Bundled MCP configuration

`.mcp.json` is imported only when `plugin.json` declares:

```json
"mcpServers": "./.mcp.json"
```

An undeclared root `.mcp.json` is ignored and must not change package architecture classification.

The documented bundled MCP format accepts either a direct server map or a wrapped `mcp_servers` object. Server entries are configuration objects.

## Hooks

Plugins may include lifecycle hooks. If hooks live at `./hooks/hooks.json`, default discovery may avoid a manifest `hooks` field. When the manifest declares hooks, current Codex documentation supports a path, a list of paths, an inline hooks object, or a list containing inline/path entries.

Plugin hooks are not automatically trusted merely because a plugin is installed. Keep hook commands package-relative/portable and avoid hidden telemetry, credential collection, or permission bypasses.

## Public ZIP limits and hygiene

Current public package checks include limits for archive entries, extracted size, and individual members. Keep the deterministic packager stricter than the platform where practical and reject common release contamination:

- symlinks and unsupported special files
- transient Python bytecode and cache directories
- `.DS_Store`, `Thumbs.db`, AppleDouble files
- secret-shaped configuration files
- normalization/case path collisions
- accidental absolute local user paths
- explicitly excluded internal capabilities

Prefer archive-root layout with `.codex-plugin/` directly at ZIP root because it avoids root-wrapper ambiguity.

## Submission readiness beyond the ZIP

A package can pass upload validation and still fail final public submission.

Every public submission needs the current publisher identity, policy attestations, and safety/security review for bundled Skills.

MCP-backed final submission currently adds production-server review material including public URLs, demo evidence, exactly five positive test cases, exactly three negative test cases, release notes, domain verification, current tool scan, explicit MCP tool annotations/justifications, and reviewer credentials when OAuth applies.

Use `references/submission-checklist.md` to keep package proof separate from portal/review proof.

## Local marketplace testing

Repo-scoped and personal marketplaces can be used to test plugins before public submission. Current documentation uses `.agents/plugins/marketplace.json` for repo sources and `~/.agents/plugins/marketplace.json` for personal sources. ChatGPT installs a cached copy rather than running directly from the marketplace source, so test a fresh installed copy after changes.

Local marketplace success does not imply public Plugin Directory approval.

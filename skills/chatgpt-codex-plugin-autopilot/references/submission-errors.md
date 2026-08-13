# Submission and Review Failure Playbook

Treat uploader and review messages as evidence. Map each failure to the source that produced it, fix that source, rebuild, and rerun the complete gate. Do not patch only the final ZIP when a generator or installer will recreate the problem.

This playbook was refreshed against the official OpenAI submission error reference on 2026-08-13.

## Package root and `.codex-plugin/`

If the uploader reports an ambiguous plugin root or wrapper siblings, package exactly one plugin root. Prefer `.codex-plugin/` directly at archive root.

Only `plugin.json` belongs inside `.codex-plugin/`. Move Skills, assets, hooks, `.app.json`, and `.mcp.json` to their documented plugin-root locations.

For entry-count, extracted-size, member-size, duplicate-path, normalization collision, unsupported type, or unreadable-member failures, repair the release surface at source. Reject symlinks and special files and remove generated/dev artifacts that are not runtime dependencies.

## Files directly under `skills/`

A direct file such as:

```text
skills/registry.json
```

is not an importable Skill. Every intended Skill must be an immediate real directory containing `SKILL.md`:

```text
skills/
  plugin-router/
    SKILL.md
    registry.json
```

OpenAI currently documents direct files and symlinks under `skills/` as ignored package content. Plugin Autopilot intentionally treats them as a strict preflight failure because silent omission is dangerous when the file was intended to drive runtime behavior.

If moving a file changes runtime references, migrate every source consumer, installer, adapter, test, and generated copy. Do not stop after making the uploader message disappear.

## Manifest and final listing failures

For display name, short description, developer name, category, capabilities, starter prompts, and URL failures, validate against final-directory limits rather than only the more permissive package-upload limits.

Current final submission requires a supported category. Keep display name and short description one line and within final-directory limits. For MCP-backed public submission, supply stable HTTPS website, privacy, terms, and support URLs that describe the real product.

## Missing logo or composer icon

Both `interface.logo` and `interface.composerIcon` are required for directory submission. They must reference real square package images.

A valid manifest pattern is:

```json
"interface": {
  "composerIcon": "./assets/icon.svg",
  "logo": "./assets/logo.svg"
}
```

The image itself must satisfy the current format, file-size, and dimension checks. Do not point a required square field at a horizontal wordmark.

## Unsafe declared asset paths

Reject paths with:

- outer whitespace
- control characters
- absolute filesystem roots
- Windows drive prefixes
- `..` traversal segments
- paths that escape the plugin root
- missing or non-file targets

A path that resolves back inside the package after normalization can still be rejected if its declared text contains unsafe traversal. Validate the declaration, not only the resolved file.

## Skill failures

Each Skill must be an immediate child directory of `skills/` and contain a regular readable `SKILL.md`.

Validate front matter for non-empty `name` and `description`, non-empty instructions, unique Skill names, and the current combined plugin/Skill identity limit.

Do not require Skill metadata `name` to equal the directory slug unless current official documentation explicitly adds that requirement. They are separate concepts under the current error reference.

For large catalogs, keep metadata concise and trigger-oriented. Do not inflate every description just to improve discovery.

## `agents/openai.yaml` failures

When a Skill includes `agents/openai.yaml`, it must contain the documented Skill interface metadata shape. Common failures include:

- missing `interface`
- missing/empty `interface.display_name`
- missing/empty `interface.short_description`
- invalid icon paths
- invalid `brand_color`
- empty `default_prompt`
- unsupported `policy` keys or values
- unsupported dependency keys

Skill interface metadata belongs in `agents/openai.yaml`, not a generic `metadata` field in `SKILL.md`.

Plugin Autopilot stays dependency-free, so its local YAML check intentionally targets the documented metadata subset. The official uploader remains authoritative for complete YAML parsing and future schema additions.

## Undeclared `.app.json` and `.mcp.json`

A root `.app.json` is ignored unless the plugin manifest sets:

```json
"apps": "./.app.json"
```

A root `.mcp.json` is ignored unless the manifest sets:

```json
"mcpServers": "./.mcp.json"
```

Do not classify a plugin as MCP-backed merely because one of these files exists. Decide architecture from declared active components.

When the file is accidental, remove it. When it is required, declare it and validate its content.

## `.app.json` failures

For declared app mappings, validate:

- top level is a JSON object
- `apps` exists and is an object
- every alias maps to an object
- every entry has a string `id`
- IDs use a currently documented eligible family
- optional `optional` / `required` fields are booleans

The public submission portal does not publish a reference to an existing ChatGPT app as a substitute for MCP review. Skills-only and MCP-backed public submissions follow separate paths.

## `.mcp.json` failures

A declared bundled MCP file uses either:

- a direct server map, or
- a top-level `mcp_servers` mapping

Server entries are objects. An empty list or malformed mapping should fail preflight before packaging.

For public MCP submission, package structure is only one part of readiness. Re-check production server, domain verification, tool annotations, demo, test cases, release notes, OAuth review material, and tool scan requirements.

## Hooks

When hooks are declared in the manifest, support the current documented forms instead of assuming a single string path. Hook paths must follow the same safe package-relative rules.

If `hooks/hooks.json` is used through default discovery, do not add a manifest field merely for consistency.

Hooks remain untrusted until the host/user trust flow allows them. Never use hooks for hidden telemetry, credential collection, or permission bypass.

## Moderation or policy review failure

A label such as cyber abuse, fraud/scams, or security risk is not an ordinary schema error. Inspect the actual public capability and instructions before deciding to appeal.

When removal is the selected remediation, delete the rejected capability from every public surface, not only one generated Skill folder. Trace and update:

- canonical public allowlist/exclusion source
- generated Skill instructions
- native-agent public copies
- profile and routing registrations
- generated maps/indexes
- manifest capability/count copy
- runtime/npm mirrors when present
- ZIP entries
- generated documentation counts

Add a regression test that fails if the excluded identity returns. Do not rename an unchanged rejected capability merely to evade review.

## After every remediation

1. regenerate from canonical source
2. rerun repository-native tests
3. rerun generic plugin preflight
4. rebuild twice and compare SHA256
5. inspect archive contents
6. validate a fresh extraction
7. verify public exclusions
8. retest local installation when available
9. resubmit the exact verified artifact

Report the external state precisely. A fixed ZIP is not automatically submitted, approved, or published.

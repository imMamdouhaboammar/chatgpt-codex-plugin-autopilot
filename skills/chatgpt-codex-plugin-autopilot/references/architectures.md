# Plugin Architecture Decisions

Choose the smallest architecture that delivers the requested user outcome. Do not add MCP, apps, hooks, or UI because another plugin uses them.

Architecture is determined by declared active components, not by stray files in a repository.

## Skills-only

Use when the plugin's value is reusable instructions, workflows, references, deterministic local scripts, or host-native tool use without a plugin-owned remote service.

Typical root:

```text
.codex-plugin/
  plugin.json
skills/
  <skill>/
    SKILL.md
    agents/openai.yaml   # optional
assets/
```

Only `plugin.json` belongs inside `.codex-plugin/`.

Keep the manifest `skills` path explicit when the package bundles Skills. Every intended Skill lives in an immediate child directory under `skills/` and contains `SKILL.md`. Do not place registries, indexes, or configuration files directly under `skills/`; put them inside an owning Skill or elsewhere at plugin root and migrate runtime references accordingly.

Stable privacy, terms, support, and website URLs are useful for a public product when they accurately exist, although current final-directory URL requirements are stricter for MCP-backed submissions.

## MCP-backed

Use when the plugin needs an external/private data source, account-specific action, hosted business logic, or tool endpoint that must execute outside ordinary Skill instructions.

There are two package-level compatibility mechanisms:

- `mcpServers: "./.mcp.json"` for bundled MCP server configuration
- `apps: "./.app.json"` for registered app/MCP connection mappings in local/workspace packages

A root `.mcp.json` or `.app.json` without the corresponding manifest declaration is ignored and must not cause Autopilot to classify the plugin as MCP-backed.

MCP-backed public submission has additional review requirements beyond package shape. Re-check the current OpenAI submission flow for production HTTPS server configuration, domain verification, tool scans, tool annotations/justifications, demo evidence, test cases, release notes, and OAuth reviewer access where applicable.

Do not store credentials in `.mcp.json`, `.app.json`, Skill files, examples, CI logs, or release artifacts. Use the authentication/configuration mechanism appropriate to the MCP integration and repository policy.

## Hybrid

Use when both reusable Skill workflows and MCP tools are required. Keep responsibilities explicit: Skills decide/orchestrate repeatable work; MCP tools perform external operations.

Test both directions:

- optional tools fail without corrupting a Skill-only path
- required MCP failures are surfaced rather than replaced with invented results

Keep package validation and server/runtime verification separate so a valid ZIP cannot hide a broken production integration.

## Registered app mappings

`.app.json` is a compatibility surface for registered MCP-backed app connections. It is not a shortcut around public MCP review.

Use it only when the target local/workspace package intentionally references the mapping and `plugin.json` declares `apps: "./.app.json"`.

Validate the current ID format and eligibility against official documentation at execution time because app ID families and developer-mode wiring can evolve.

## Hooks

Add lifecycle hooks only when behavior truly belongs at lifecycle boundaries such as session setup, evidence state, or bounded post-tool checks.

Prefer default `hooks/hooks.json` discovery when it fits the host. If hooks are declared in the manifest, accept the currently documented path/list/inline forms and validate path entries against plugin-root safety rules.

Plugin hooks are not automatically trusted merely because the plugin is installed. Design for explicit review/trust and safe failure.

Hooks must not become hidden telemetry, prompt retention, credential collection, or a way to bypass normal host permissions. Keep commands relative to the plugin installation and portable across supported environments.

## Local marketplace testing

Use repo or personal marketplaces for authoring and installation tests before public submission when the available ChatGPT/Codex surface supports them.

Current OpenAI documentation uses:

```text
$REPO_ROOT/.agents/plugins/marketplace.json
~/.agents/plugins/marketplace.json
```

A marketplace entry points to the plugin folder. ChatGPT installs a cached copy, so test the installed copy in a fresh chat instead of assuming edits to the source folder are already active.

Local marketplace success is not public Plugin Directory approval.

## Public vs internal capabilities

A repository may contain more internal agents/Skills than the public plugin. Model this deliberately. Maintain a canonical public allowlist or exclusion rule at generation time, not a manual deletion after generation.

For every exclusion, verify all relevant surfaces:

- public `skills/<slug>/`
- public native-agent copies if bundled
- profile/config registrations
- generated maps and routing indexes
- default prompts and capabilities copy
- npm/runtime mirrors when present
- ZIP entries
- generated documentation counts

The public generator's check mode should fail if an excluded artifact reappears. This prevents later regeneration from undoing a moderation or security decision.

## Decision rule

Prefer this order:

1. Skills-only when repeatable instructions are enough
2. MCP-backed when external executable capability is actually required
3. Hybrid when both responsibilities are real
4. hooks only for lifecycle behavior
5. UI only as part of the MCP/app experience when it materially improves the user outcome

Do not infer architecture from filenames that the manifest does not declare.

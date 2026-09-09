# OpenAI Submission Contract Conformance Matrix & Drift Control Strategy

**Authoritative Review Date:** 2026-09-09  
**Specification Sources:**
- [OpenAI Plugins: Build Overview](https://developers.openai.com/plugins/build/plugins)
- [OpenAI Plugins: Directory Submission](https://developers.openai.com/plugins/deploy/submission)
- [OpenAI Plugins: Submission Error Reference](https://developers.openai.com/plugins/deploy/submission-errors)
- [OpenAI Codex & ChatGPT Skills Concepts](https://developers.openai.com/plugins/concepts/skills)

---

## 1. Executive Summary & Core Invariant

Plugin Autopilot automates the conversion, validation, packaging, and listing-preparation of ChatGPT and Codex plugins. A fundamental invariant of this project is:

> **Local Proof $\neq$ Public Approval**  
> Passing local preflight guarantees structural package integrity, schema conformance, and fail-closed security. It does not—and cannot—substitute for OpenAI human review, domain verification, verified developer identity binding, or live external service connectivity.

This document inventories the authoritative contract rule families, maps them to local enforcement and regression tests, traces historical contract gaps (#6, #7, #8, #24, #25, #26), and establishes a sustainable drift-control strategy.

---

## 2. Rule Classification Vocabulary

- **`enforced`**: Deterministic local rule enforced by the validator or packager; failure halts preflight.
- **`warning`**: Non-fatal notice emitted for deprecations, forward-compatibility, or conditions requiring human confirmation.
- **`external-only`**: Upstream portal or reviewer verification gate that cannot be proven from package metadata alone.
- **`not-covered`**: Known upstream rule intentionally or temporarily unowned locally.
- **`not-applicable`**: Rule applies to runtime contexts not supported by this plugin's target architecture.

---

## 3. Conformance Matrix

| Rule / Error Family | Upstream Specification | Local Enforcement Symbol | Regression Fixture / Test | Status | Volatility |
|---|---|---|---|---|---|
| **Archive Member Path Length** | Member path $\le$ 1,024 chars (`archive_member_path_too_long`) | `validate_plugin.py:archive_member_path_within_limit`, `package_plugin.py:_collect` | `test_validator_regressions.py:test_archive_member_path_within_limit_exact_boundaries` | `enforced` | Low |
| **Archive Path Depth** | At most 20 path segments (`archive_member_path_too_deep`) | `validate_plugin.py:_walk` | `test_validator_regressions.py:test_rejects_archive_member_path_exceeding_limit` | `enforced` | Low |
| **Path Separators** | Slash `/` only, no backslashes (`archive_member_path_has_backslash`) | `validate_plugin.py:_walk`, `package_plugin.py:_collect` | `test_validator_regressions.py:test_rejects_backslash_in_archive_member_name` | `enforced` | Low |
| **Filesystem Safety & Symlinks** | No symlinks, FIFO, or socket files in public package | `validate_plugin.py:_walk`, `_verify_regular_package_file` | `test_validator_regressions.py:test_rejects_internal_symlinked_skill_before_parsing_target` | `enforced` | Low |
| **Bytecode Hygiene** | No `__pycache__` or `.pyc` files in release package | `validate_plugin.py:_walk`, `self_check.py:stage_plugin` | `test_self_hosting.py:test_self_check_passes` | `enforced` | Low |
| **Deterministic Packaging** | Fixed timestamp (1980-01-01), deflated compression, reproducible SHA-256 | `package_plugin.py:build_archive` | `test_packaging.py`, `scripts/build_release.py` | `enforced` | Low |
| **Manifest Root & Interface** | `plugin.json` requires `name`, `version` (semver), `interface` | `validate_plugin.py:validate_plugin` | `test_plugin_contract.py:test_manifest_schema_conformance` | `enforced` | Low |
| **HTTPS Public URLs** | Author, homepage, repository URLs must be HTTPS or empty string (fixed #6) | `validate_plugin.py:_public_https` | `test_validator_regressions.py:test_rejects_wrong_typed_openai_agent_fields` | `enforced` | Moderate |
| **Listing Limits & Prompts** | Max 3 prompts, $\le$ 128 chars, unique, no `@mention` (fixed #7) | `build_directory_pack.py:_validate_directory_readiness` | `test_distribution_pack.py:test_directory_pack_enforces_url_and_prompt_constraints` | `enforced` | Moderate |
| **Branding Assets (Square/SVG)** | Required `interface.logo` and `composerIcon`, valid dimensions, square | `validate_plugin.py:_validate_branding_asset` | `test_distribution_pack.py:test_autopilot_ships_light_and_dark_svg_logo_variants` | `enforced` | Low |
| **Screenshots on Skills-Only** | Skills-only ZIPs must not include `screenshots` (`screenshot_configuration_excluded`) | `validate_plugin.py:validate_plugin` | `test_validator_regressions.py:test_rejects_screenshots_on_skills_only_packages` | `enforced` | Low |
| **MCP-backed Screenshots** | Custom UI screenshots: 1 per prompt, 706px wide, 400–860px tall | `validate_plugin.py:validate_plugin` | `test_validator_regressions.py:test_accepts_mcp_screenshots_matching_prompt_count_and_dimensions` | `enforced` | Moderate |
| **Skill Layout & Structure** | Immediate child under `skills/`, contains readable `SKILL.md` | `validate_plugin.py:_validate_skills_directory` | `test_skill_surface.py:test_required_skill_files_exist` | `enforced` | Low |
| **Skill Frontmatter YAML** | Fail-closed restricted parser: no tags, valid types, required name/desc | `validate_plugin.py:_parse_skill_frontmatter`, `_parse_restricted_yaml` | `test_skill_frontmatter_yaml.py` | `enforced` | Low |
| **Skill Agent Metadata** | `agents/openai.yaml`: display_name, short_description, policy.products | `validate_plugin.py:_validate_skill_agent_metadata` | `test_validator_regressions.py:test_accepts_quoted_and_list_openai_agent_metadata` | `enforced` | Moderate |
| **Skill Tool Dependencies** | `dependencies.tools` list with MCP/tool shape validation (fixed #25) | `validate_plugin.py:_validate_skill_agent_metadata` | `test_validator_regressions.py:test_validates_skill_agent_dependencies_tools_positive_and_negative` | `enforced` | Moderate |
| **Duplicate App IDs** | Duplicate app ID references produce package warnings (`duplicate_app_reference`), not fatal errors (fixed #24) | `validate_plugin.py:_validate_app_manifest` | `test_validator_regressions.py:test_declared_app_duplicate_id_warns_and_passes_preflight` | `warning` | Moderate |
| **Bundled MCP Server Schema** | `.mcp.json` server entries require `command` or `url`, arg/env types (fixed #26) | `validate_plugin.py:_validate_mcp_manifest` | `test_validator_regressions.py:test_validates_bundled_mcp_configuration_positive_and_negative` | `enforced` | Moderate |
| **MCP Wrapper Naming** | `mcpServers` (camelCase) preferred; `mcp_servers` (snake_case) triggers warning | `validate_plugin.py:_validate_mcp_manifest` | `test_validator_regressions.py:test_validates_bundled_mcp_configuration_positive_and_negative` | `warning` | Moderate |
| **Verified Developer Identity** | Manifest developerName matches verified OpenAI account | `build_directory_pack.py:_validate_directory_readiness` | `test_distribution_pack.py:test_directory_readiness_checks` | `warning` | Low |
| **Domain Verification** | Domain TXT/DNS verification for public app integration | N/A (Portal setting) | N/A | `external-only` | Low |
| **OAuth 2.1 Live Authentication** | Live OAuth handshake and token exchange with external MCP service | N/A (Runtime/Portal) | N/A | `external-only` | Low |
| **Directory Marketplace Listing** | Public inclusion in ChatGPT Plugin Store directory | N/A (OpenAI Review) | N/A | `external-only` | Low |

---

## 4. Tracing Historical Audit Findings

| Issue | Description | Resolution in Code & Tests | Status |
|---|---|---|---|
| **#6** | Empty string in author/repo URL crashed public HTTPS validation | Updated `_public_https` to reject empty strings cleanly | Closed |
| **#7** | Directory listing readiness did not enforce final-directory contract constraints | Enhanced `build_directory_pack.py` with URL HTTPS checks, max lengths, prompt validation | Closed |
| **#8** | Archive member limits and backslash rejection were inconsistently applied | Synchronized `validate_plugin.py` and `package_plugin.py` with exact boundaries and tests | Closed |
| **#24** | Duplicate app ID in `.app.json` was treated as an error instead of warning | Updated `_validate_app_manifest` to emit warning while validating schema | Closed |
| **#25** | Unvalidated `dependencies.tools` contract in `agents/openai.yaml` | Implemented strict structural validation for tool entries and supported MCP types | Closed |
| **#26** | Undervalidated `.mcp.json` server configs (object shape only) | Implemented deep validation for `command`/`url`, `args`, `env`, HTTPS transport | Closed |

---

## 5. Drift-Control Strategy Evaluation

### Strategy A: Checked-In Conformance Matrix + Boundary Regression Fixtures (Recommended)
- **Mechanism:** Maintain a dated, human-reviewable specification matrix alongside deterministic unit tests with negative and positive boundary fixtures. Whenever OpenAI releases a new plugin specification or updates submission errors, a maintainer updates this matrix, adjusts validator rules, and adds test fixtures.
- **Advantages:**
  - 100% deterministic local execution without network access or third-party dependencies.
  - Zero CI flakiness or false positives due to upstream styling, wording, or layout changes.
  - Clear separation of local structural invariants from external portal semantics.
- **Trade-offs:** Requires intentional human maintenance when reviewing platform updates.

### Strategy B: Automated Web Scraping / Schema Linter in CI (Rejected)
- **Mechanism:** Run a scheduled CI workflow that fetches OpenAI documentation pages, parses HTML/markdown tables, and asserts matching constants.
- **Why Rejected:**
  - High fragility: Prose edits, redesigns, cloudflare bot challenges, and DOM restructuring break builds without any underlying API change.
  - Violates the local-first execution invariant and introduces network dependencies into verification gates.
  - Cannot reliably distinguish editorial phrasing changes from load-bearing contract changes.

---

## 6. Maintenance & Review Protocol

1. **Scheduled Audit Cycle:** Review official OpenAI developer documentation quarterly or upon major platform releases (e.g., updates to GPT-4o / Codex / ChatGPT plugins).
2. **Deterministic-First Gate:** Any new rule must be evaluated for whether it can be proven from package files alone. If it requires network access, credentials, or portal state, classify it as `warning` or `external-only` rather than inventing synthetic failure states.
3. **Fail-Closed Forward Compatibility:** Unknown fields in extensible schemas (`agents/openai.yaml`, `.mcp.json`) must trigger informative warnings rather than fatal errors, preventing unnecessary breakage when OpenAI introduces forward-compatible features.

# OmniSkill Profile — chatgpt-codex-plugin-autopilot

This document captures the OmniSkill SkillSpec for this Plugin, documenting trigger language, near-miss negatives, host support, invariants, and quality gates.

## Metadata

| Field | Value |
|---|---|
| **Name** | `chatgpt-codex-plugin-autopilot` |
| **Version** | 0.8.0 |
| **Author** | Mamdouh Aboammar |
| **License** | MIT |
| **OmniSkill mode** | PACKAGE + DISTRIBUTE + VALIDATE |
| **Primary pattern** | Sequential + Multi-tool coordination |

---

## Job

Convert agentic repositories into focused, validated, deterministically packaged ChatGPT/Codex Plugins — finding real workflows, deciding what is public vs. internal, compiling portable Skills, adding workspace operations, verifying with Python when available, building deterministic ZIPs, and preparing reviewer evidence.

## Failure without this skill

Without Plugin Autopilot, an agent tasked with "package this repo as a ChatGPT Plugin" will:

- Copy every folder into the Plugin without boundary analysis
- Invent undocumented manifest fields or fake MCP permissions
- Skip deterministic packaging (non-reproducible ZIPs)
- Claim Python ran without executing it
- Confuse local validation success with OpenAI directory approval
- Produce a generic plugin.json with no brand identity or reviewer metadata

---

## Trigger language (positive)

| Prompt | Reason |
|---|---|
| "Turn this agentic repository into a ChatGPT Plugin" | Core job trigger |
| "Package this repo for the Codex Plugin Directory" | Explicit packaging trigger |
| "Convert my AGENTS.md workflows into Skills" | Workflow-to-skill conversion |
| "Validate and package the plugin in this repo" | Validation + packaging |
| "Build a deterministic release ZIP for this plugin" | Release discipline trigger |
| "Prepare the Plugin Directory listing and reviewer packet" | Submission trigger |
| "Add SVG brand identity to this plugin" | Brand trigger |
| "Run self-check and build release" | Internal gate trigger |

## Near-miss negatives (must NOT trigger)

| Prompt | Reason |
|---|---|
| "Set up a new Python project" | Generic dev task — not plugin conversion |
| "Help me write a ChatGPT system prompt" | Prompt writing, not Plugin packaging |
| "Create a GitHub repository" | Repo creation, not plugin conversion |
| "Fix this Python bug" | Debugging, not plugin packaging |
| "Write a README for my project" | Docs writing, not plugin packaging |

---

## Host support matrix

| Host | Discovery | Workspace | Python | Shell | Status |
|---|---|---|---|---|---|
| ChatGPT (GPT-4o) | ✅ Plugin Directory | ✅ via Code Interpreter | ✅ python tool | ⚠️ limited | Supported |
| Codex | ✅ Plugin manifest | ✅ native | ✅ native | ✅ native | Supported |
| Claude Code | ✅ SKILL.md discovery | ✅ native | ✅ native | ✅ native | Supported |
| Gemini CLI / Antigravity | ✅ skills/ discovery | ✅ native | ✅ native | ✅ native | Supported |
| Cursor | ✅ skills/ discovery | ✅ native | ✅ native | ✅ native | Supported |

---

## Invariants

1. **Never claim a command ran without executing it.** Show actual output.
2. **Never add MCP dependencies** for workflows that need only host-native capabilities.
3. **Never copy internal material** (keys, private prompts, sensitive paths) into the Plugin package.
4. **Never confuse local preflight success** with OpenAI Plugin Directory approval.
5. **Never produce non-deterministic ZIPs** — builds must be bitwise reproducible.
6. **Always run tests before committing** — `python3 -m unittest discover -s tests -v` must be green.
7. **Always verify self-check** — `python3 scripts/self_check.py` must pass before releasing.

---

## Workflow steps

### Phase 1: Discovery (`agentic-repo-discovery`)
- **Freedom**: Low — must follow `analyze_repo.py` output and respect `skills-only` / `MCP-backed` / `hybrid` recommendation
- Scan for `AGENTS.md`, `SKILL.md`, `playbooks/`, `commands/`, `.mcp.json`, `.app.json`
- Warn on undeclared MCP/app files

### Phase 2: Decision (`agentic-repo-discovery` → `plugin-experience-architect`)
- **Freedom**: Medium — agent chooses compile/reference/internal/discard but must justify
- Set public/private boundary; never include private material

### Phase 3: Compilation (`workflow-to-skill-compiler`)
- **Freedom**: Low for invariants, Medium for prose style
- Preserve decisions, approvals, tests, evidence, stop conditions

### Phase 4: Workspace (`host-workspace-operator`)
- **Freedom**: Low — must use host-native operations, not fabricated tools

### Phase 5: Verification (`sandbox-python-executor`)
- **Freedom**: Low — if Python is available, actually run it and show real output

### Phase 6: Design + Brand (`plugin-experience-architect`, `plugin-brand-identity-designer`)
- **Freedom**: High — many valid visual approaches

### Phase 7: Listing (`plugin-directory-listing-writer`)
- **Freedom**: Low — all required fields must be accurate and complete

### Phase 8: Prove + Release (`submission-pack-builder`, `scripts/build_release.py`)
- **Freedom**: Very low — deterministic builds, SHA256 verification, archive inspection

---

## Quality gate (BinEval)

| Dimension | Gate |
|---|---|
| Discovery | Skill loaded on all positive trigger prompts; not loaded on near-miss negatives |
| Clarity | Workflow steps are sequential and unambiguous |
| Structure | All 9 SKILL.md files present with valid YAML frontmatter |
| Robustness | Non-deterministic ZIP → fail; claimed-but-unrun Python → fail |
| Completeness | reviewer-packet.json, listing.json, SHA256SUMS all present in release |

---

## Acceptance gates

A release is accepted when all of the following pass:

```bash
python3 -m unittest discover -s tests -v           # ≥ 92 tests, all OK
python3 scripts/self_check.py                      # PASS skills=9
python3 skills/chatgpt-codex-plugin-autopilot/scripts/build_directory_pack.py . --listing submission/listing.json --json
python3 scripts/build_release.py --out-dir dist-a
python3 scripts/build_release.py --out-dir dist-b
cmp dist-a/chatgpt-codex-plugin-autopilot-*.zip dist-b/chatgpt-codex-plugin-autopilot-*.zip
```

All commands must exit 0. ZIP builds must be bitwise identical.

---

*Last updated: v0.8.0 — © 2026 Mamdouh Aboammar — MIT License*

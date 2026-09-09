# Contributing to ChatGPT Codex Plugin Autopilot

Thank you for contributing to Plugin Autopilot! This document outlines our repository boundaries, development workflow, and verification standards.

---

## 1. Repository & Product Architecture Boundaries

This repository houses the following distinct areas:

- **Primary Product: `chatgpt-codex-plugin-autopilot`**
  - The root plugin package containing skills for repository analysis, skill conversion, brand identity generation, plugin packaging, and OpenAI submission verification.
  - Defined by `.codex-plugin/plugin.json`, `skills/`, `assets/`, `scripts/`, and root legal/support docs (`README.md`, `LICENSE`, `PRIVACY.md`, `TERMS.md`, `SUPPORT.md`, `SECURITY.md`).
  - Staged and packaged deterministically into release ZIP archives via `scripts/build_release.py`.
- **Secondary Subtrees: `plugins/no-ai-slop`**
  - Unbundled reference documentation stubs.
  - Excluded from the root release surface (`scripts/self_check.py:SURFACE`) and not packaged into the primary plugin distribution.
  - Canonical identifier namespace notes are maintained in `plugins/no-ai-slop/README.md`.

---

## 2. Local Verification Commands

Before opening a pull request, run the following single-command verification suite locally:

```bash
# 1. Run full unit and regression test suite
python3 -m unittest discover -s tests -v

# 2. Run repository self-check (validates release surface, schemas, and packaging)
python3 scripts/self_check.py

# 3. Validate directory listing pack and readiness constraints
python3 skills/chatgpt-codex-plugin-autopilot/scripts/build_directory_pack.py . --listing submission/listing.json --json

# 4. Optional release build test
python3 scripts/build_release.py --out-dir dist && rm -rf dist
```

All gates must pass cleanly with exit code 0.

---

## 3. Pull Request & Branch Conventions

- **Branch naming**: Use `issue/<id>-<slug>` for feature or bugfix branches (e.g., `issue/9-security-policy`).
- **Commit messages**: Use conventional commit prefixes (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`) and reference the issue number in the title (e.g., `docs: add repository security policy (#9)`).
- **PR description**: Summarize changes, list modified files, and include `Fixes #<id>` to link and close corresponding issues upon merge.
- **Merge strategy**: Squash and merge onto `main` to preserve clean, linear git history.

---

## 4. Release Provenance

- All releases are published through the single authoritative workflow: `.github/workflows/release.yml`.
- Releases are triggered by pushing immutable semver tags matching manifest versions (`git tag -a v0.5.0 -m "v0.5.0"`).
- The release workflow performs two independent builds, bitwise artifact comparison, and publishes the verified ZIP, `SHA256SUMS`, and reviewer packet to GitHub Releases.
- **Core Invariant**: GitHub Releases verify repository package integrity; they do not imply OpenAI Plugin Directory marketplace approval, which requires separate upstream directory submission.

---

## 5. Security & Responsible Disclosure

If you discover a suspected security vulnerability, **do not open a public GitHub issue**. See [SECURITY.md](./SECURITY.md) for private vulnerability reporting instructions via GitHub Security Advisories.

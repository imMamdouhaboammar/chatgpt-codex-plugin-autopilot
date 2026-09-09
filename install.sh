#!/usr/bin/env bash
# install.sh — Universal multi-agent installer for chatgpt-codex-plugin-autopilot
# Copyright (c) 2026 Mamdouh Aboammar — MIT License
# https://github.com/imMamdouhaboammar/chatgpt-codex-plugin-autopilot
set -euo pipefail

REPO="imMamdouhaboammar/chatgpt-codex-plugin-autopilot"
SKILLS_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")/skills"
PLUGIN_NAME="chatgpt-codex-plugin-autopilot"

echo "🔌 Plugin Autopilot — Universal Installer"
echo "   © 2026 Mamdouh Aboammar — MIT License"
echo "   https://github.com/${REPO}"
echo ""

installed=0

# ── Claude Code / Claude Desktop ──────────────────────────────────────────────
if command -v claude &>/dev/null; then
  CLAUDE_SKILLS="${HOME}/.claude/skills"
  mkdir -p "${CLAUDE_SKILLS}"
  for skill_dir in "${SKILLS_DIR}"/*/; do
    skill_name="$(basename "${skill_dir}")"
    target="${CLAUDE_SKILLS}/${skill_name}"
    if [ -L "${target}" ]; then
      rm "${target}"
    fi
    ln -s "${skill_dir%/}" "${target}"
  done
  echo "✅ Linked skills into Claude Code: ${CLAUDE_SKILLS}"
  installed=$((installed + 1))
fi

# ── Gemini CLI / Antigravity ───────────────────────────────────────────────────
GEMINI_SKILLS="${HOME}/.gemini/config/skills"
if [ -d "${GEMINI_SKILLS}" ]; then
  for skill_dir in "${SKILLS_DIR}"/*/; do
    skill_name="$(basename "${skill_dir}")"
    target="${GEMINI_SKILLS}/${skill_name}"
    if [ -L "${target}" ]; then
      rm "${target}"
    fi
    ln -s "${skill_dir%/}" "${target}"
  done
  echo "✅ Linked skills into Gemini CLI / Antigravity: ${GEMINI_SKILLS}"
  installed=$((installed + 1))
fi

# ── Codex / OpenAI CLI ─────────────────────────────────────────────────────────
CODEX_SKILLS="${HOME}/.codex/skills"
if [ -d "${HOME}/.codex" ]; then
  mkdir -p "${CODEX_SKILLS}"
  for skill_dir in "${SKILLS_DIR}"/*/; do
    skill_name="$(basename "${skill_dir}")"
    target="${CODEX_SKILLS}/${skill_name}"
    if [ -L "${target}" ]; then
      rm "${target}"
    fi
    ln -s "${skill_dir%/}" "${target}"
  done
  echo "✅ Linked skills into Codex: ${CODEX_SKILLS}"
  installed=$((installed + 1))
fi

# ── Cursor ────────────────────────────────────────────────────────────────────
CURSOR_SKILLS="${HOME}/.cursor/skills"
if command -v cursor &>/dev/null || [ -d "${HOME}/.cursor" ]; then
  mkdir -p "${CURSOR_SKILLS}"
  for skill_dir in "${SKILLS_DIR}"/*/; do
    skill_name="$(basename "${skill_dir}")"
    target="${CURSOR_SKILLS}/${skill_name}"
    if [ -L "${target}" ]; then
      rm "${target}"
    fi
    ln -s "${skill_dir%/}" "${target}"
  done
  echo "✅ Linked skills into Cursor: ${CURSOR_SKILLS}"
  installed=$((installed + 1))
fi

echo ""
if [ "${installed}" -eq 0 ]; then
  echo "⚠️  No supported AI harness detected automatically."
  echo "   Manually copy the skills/ directory into your agent's skills path."
  echo "   Skills directory: ${SKILLS_DIR}"
else
  echo "🎉 Installed ${PLUGIN_NAME} into ${installed} agent harness(es)."
fi
echo ""
echo "   Verify by asking your agent: 'Turn this agentic repository into a ChatGPT Plugin.'"

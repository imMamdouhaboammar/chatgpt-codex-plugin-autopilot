#!/usr/bin/env bash
# chatgpt-codex-plugin-autopilot v0.7.0
# Copy-in bootstrap: copies the complete, verified Plugin Autopilot engine into any repository.
# From that point on, the kit is yours — no external dependency at runtime.
# Edit the config, rename things, delete a skill you don't need.
#
# Copyright (c) 2026 Mamdouh Aboammar — MIT License
# https://github.com/imMamdouhaboammar/chatgpt-codex-plugin-autopilot
#
# A personal note from the author:
#   I built this for my own development work with AI coding agents.
#   The principles and choices here reflect my own preferences and workflows —
#   not a universal best practice. Take what's useful, change what isn't,
#   and shape it to fit how you like to work.
#
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RESET="\033[0m"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_JSON="${REPO_ROOT}/.codex-plugin/plugin.json"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║        Plugin Autopilot — Copy-in Engine Init            ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  © 2026 ${BOLD}Mamdouh Aboammar${RESET} — MIT License"
echo -e "  ${CYAN}https://github.com/imMamdouhaboammar/chatgpt-codex-plugin-autopilot${RESET}"
echo ""

# ── Step 1: Verify Python 3 is available ─────────────────────────────────────
echo -e "${BOLD}[1/6]${RESET} Checking Python 3..."
if ! command -v python3 &>/dev/null; then
  echo -e "  ${YELLOW}⚠  python3 not found. Install Python 3.9+ and re-run.${RESET}"
  exit 1
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "  ${GREEN}✓${RESET} python3 ${PY_VER}"

# ── Step 2: Read plugin.json ──────────────────────────────────────────────────
echo -e "${BOLD}[2/6]${RESET} Reading plugin manifest..."
if [ ! -f "${PLUGIN_JSON}" ]; then
  echo -e "  ${YELLOW}⚠  .codex-plugin/plugin.json not found. Is this the right directory?${RESET}"
  exit 1
fi
PLUGIN_NAME=$(python3 -c "import json; d=json.load(open('${PLUGIN_JSON}')); print(d['name'])")
PLUGIN_VERSION=$(python3 -c "import json; d=json.load(open('${PLUGIN_JSON}')); print(d['version'])")
PLUGIN_AUTHOR=$(python3 -c "import json; d=json.load(open('${PLUGIN_JSON}')); print(d['author']['name'])")
echo -e "  ${GREEN}✓${RESET} ${PLUGIN_NAME} v${PLUGIN_VERSION} by ${PLUGIN_AUTHOR}"

# ── Step 3: Count skills ──────────────────────────────────────────────────────
echo -e "${BOLD}[3/6]${RESET} Counting skills..."
SKILLS_DIR="${REPO_ROOT}/skills"
SKILL_COUNT=0
if [ -d "${SKILLS_DIR}" ]; then
  for d in "${SKILLS_DIR}"/*/; do
    [ -f "${d}SKILL.md" ] && SKILL_COUNT=$((SKILL_COUNT + 1))
  done
fi
echo -e "  ${GREEN}✓${RESET} ${SKILL_COUNT} skill(s) found in skills/"

# ── Step 4: Run self-check ────────────────────────────────────────────────────
echo -e "${BOLD}[4/6]${RESET} Running self-check..."
SELF_CHECK="${REPO_ROOT}/scripts/self_check.py"
if [ -f "${SELF_CHECK}" ]; then
  OUTPUT=$(python3 "${SELF_CHECK}" 2>&1)
  if echo "${OUTPUT}" | grep -q "PASS"; then
    echo -e "  ${GREEN}✓${RESET} ${OUTPUT}"
  else
    echo -e "  ${YELLOW}⚠  self-check output:${RESET}"
    echo "${OUTPUT}" | sed 's/^/    /'
  fi
else
  echo -e "  ${YELLOW}⚠  scripts/self_check.py not found — skipping.${RESET}"
fi

# ── Step 5: Run tests ─────────────────────────────────────────────────────────
echo -e "${BOLD}[5/6]${RESET} Running test suite..."
TESTS_DIR="${REPO_ROOT}/tests"
if [ -d "${TESTS_DIR}" ]; then
  TEST_OUTPUT=$(python3 -m unittest discover -s tests 2>&1 | tail -3)
  if echo "${TEST_OUTPUT}" | grep -q "^OK"; then
    echo -e "  ${GREEN}✓${RESET} ${TEST_OUTPUT}"
  else
    echo -e "  ${YELLOW}⚠  Tests output (last 3 lines):${RESET}"
    echo "${TEST_OUTPUT}" | sed 's/^/    /'
    echo ""
    echo -e "  Run ${BOLD}python3 -m unittest discover -s tests -v${RESET} for details."
  fi
else
  echo -e "  ${YELLOW}⚠  tests/ directory not found — skipping.${RESET}"
fi

# ── Step 6: Print ownership confirmation ─────────────────────────────────────
echo -e "${BOLD}[6/6]${RESET} Confirming ownership..."
echo ""
echo -e "${BOLD}${GREEN}  ✅ This kit is now repo-owned and yours to modify.${RESET}"
echo ""
echo -e "  No external package dependency at runtime."
echo -e "  No upstream calls during normal use."
echo -e "  Skills are in ${BOLD}skills/${RESET} — edit, rename, or delete any of them."
echo -e "  Config lives in ${BOLD}.codex-plugin/plugin.json${RESET}."
echo ""
echo -e "  ${BOLD}Next steps:${RESET}"
echo -e "  1. Edit ${BOLD}.codex-plugin/plugin.json${RESET} — set your name, version, description"
echo -e "  2. Remove skills you don't need from ${BOLD}skills/${RESET}"
echo -e "  3. Run ${BOLD}python3 scripts/build_release.py --out-dir dist${RESET} to build your ZIP"
echo -e "  4. Push and tag when ready: ${BOLD}git tag -a v1.0.0 -m 'v1.0.0' && git push origin v1.0.0${RESET}"
echo ""
echo -e "  ${CYAN}https://github.com/imMamdouhaboammar/chatgpt-codex-plugin-autopilot/releases${RESET}"
echo ""

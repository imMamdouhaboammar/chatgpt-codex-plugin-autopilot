import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
SKILL = SKILLS / "chatgpt-codex-plugin-autopilot"
FOCUSED_SKILLS = [
    "agentic-repo-discovery",
    "workflow-to-skill-compiler",
    "plugin-experience-architect",
    "host-workspace-operator",
    "sandbox-python-executor",
    "plugin-brand-identity-designer",
    "plugin-directory-listing-writer",
    "submission-pack-builder",
]


class SkillSurfaceTests(unittest.TestCase):
    def test_required_skill_files_exist(self):
        required = [
            "SKILL.md",
            "agents/openai.yaml",
            "references/architectures.md",
            "references/official-contract.md",
            "references/release-playbook.md",
            "references/submission-errors.md",
            "references/submission-checklist.md",
            "references/conversion-pipeline.md",
            "references/branding-and-listing.md",
            "references/host-python-sandbox.md",
            "references/host-workspace-capabilities.md",
            "scripts/analyze_repo.py",
            "scripts/build_directory_pack.py",
            "scripts/install_host_workspace_skill.py",
            "scripts/validate_plugin.py",
            "scripts/package_plugin.py",
        ]
        for rel in required:
            self.assertTrue((SKILL / rel).is_file(), rel)

    def test_focused_conversion_skills_are_discoverable(self):
        for slug in FOCUSED_SKILLS:
            skill_file = SKILLS / slug / "SKILL.md"
            self.assertTrue(skill_file.is_file(), slug)
            text = skill_file.read_text(encoding="utf-8")
            self.assertRegex(text, rf"(?m)^name:\s*{re.escape(slug)}$")
            description = re.search(r"(?m)^description:\s*(.+)$", text)
            self.assertIsNotNone(description, slug)
            self.assertTrue(description.group(1).startswith("Use when "), slug)

    def test_skill_frontmatter_is_discoverable(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^name:\s*chatgpt-codex-plugin-autopilot$")
        description = re.search(r"(?m)^description:\s*(.+)$", text)
        self.assertIsNotNone(description)
        self.assertTrue(description.group(1).startswith("Use when "))

    def test_skill_contains_self_hosting_release_requirements(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "official OpenAI Plugin",
            "deterministic",
            "Full Autopilot Publish",
            "public-distribution safety",
        ):
            self.assertIn(phrase, text)

    def test_skill_contains_repo_conversion_contract(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "analyze_repo.py",
            "agentic-repo-discovery",
            "workflow-to-skill-compiler",
            "plugin-experience-architect",
            "host-workspace-operator",
            "sandbox-python-executor",
            "install_host_workspace_skill.py",
            "plugin-brand-identity-designer",
            "plugin-directory-listing-writer",
            "submission-pack-builder",
            "build_directory_pack.py",
            "host-python-sandbox.md",
            "host-workspace-capabilities.md",
        ):
            self.assertIn(phrase, text)

    def test_skill_contains_2026_learned_preflight_contract(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "skills/registry.json",
            "agents/openai.yaml",
            "submission-checklist.md",
            "Package preflight",
            "undeclared `.app.json` / `.mcp.json`",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()

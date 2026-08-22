import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github/workflows/ci.yml"
RELEASE = ROOT / ".github/workflows/release.yml"

class WorkflowTests(unittest.TestCase):
    def test_ci_runs_full_self_hosting_gate_with_pinned_actions(self):
        text = CI.read_text(encoding="utf-8")
        self.assertIn("python3 -m unittest discover -s tests -v", text)
        self.assertIn("python3 scripts/self_check.py", text)
        self.assertIn(
            "python3 skills/chatgpt-codex-plugin-autopilot/scripts/build_directory_pack.py . --listing submission/listing.json --json",
            text,
        )
        self.assertIn("python3 scripts/build_release.py --out-dir dist", text)
        self.assertRegex(text, r"actions/checkout@[0-9a-f]{40}")
        self.assertRegex(text, r"actions/upload-artifact@[0-9a-f]{40}")
        self.assertIn("contents: read", text)
        self.assertIn("cd dist && sha256sum -c SHA256SUMS", text)
        self.assertNotRegex(text, r"(?i)npm\s+publish|twine\s+upload")

    def test_release_is_tag_only_and_attaches_verified_plugin_assets(self):
        text = RELEASE.read_text(encoding="utf-8")
        self.assertIn('tags:', text)
        self.assertIn('- "v*"', text)
        self.assertIn("contents: write", text)
        self.assertIn("python3 -m unittest discover -s tests -v", text)
        self.assertIn("python3 scripts/self_check.py", text)
        self.assertGreaterEqual(text.count("scripts/build_release.py"), 2)
        self.assertIn("cmp", text)
        self.assertIn("gh release create", text)
        self.assertIn("SHA256SUMS", text)
        self.assertIn("(cd dist-a && sha256sum -c SHA256SUMS)", text)
        self.assertRegex(text, r"actions/checkout@[0-9a-f]{40}")
        self.assertNotRegex(text, r"(?i)npm\s+publish|twine\s+upload")

if __name__ == "__main__":
    unittest.main()

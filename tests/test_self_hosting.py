import hashlib
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SelfHostingTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run(["python3", *map(str, args)], cwd=ROOT, text=True, capture_output=True)

    def test_self_check_validates_staged_plugin(self):
        proc = self.run_script("scripts/self_check.py", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        report = json.loads(proc.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual(report["architecture"], "skills-only")
        self.assertEqual(report["skills"], 1)

    def test_validator_rejects_transient_python_bytecode(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp) / "plugin"
            subprocess.run(
                ["python3", "scripts/self_check.py", "--json"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            import sys
            sys.path.insert(0, str(ROOT / "scripts"))
            from self_check import stage_plugin

            stage_plugin(stage)
            cache = stage / "skills/chatgpt-codex-plugin-autopilot/scripts/__pycache__"
            cache.mkdir(parents=True)
            (cache / "validate_plugin.cpython-312.pyc").write_bytes(b"transient")
            validator = stage / "skills/chatgpt-codex-plugin-autopilot/scripts/validate_plugin.py"
            proc = subprocess.run(
                ["python3", str(validator), str(stage), "--json"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(proc.returncode, 0, proc.stdout)
            self.assertIn("bytecode", proc.stdout.lower())

    def test_release_build_is_deterministic_and_installable(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            first = self.run_script("scripts/build_release.py", "--out-dir", out, "--json")
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            first_report = json.loads(first.stdout)
            archive = Path(first_report["archive"])
            first_bytes = archive.read_bytes()
            second = self.run_script("scripts/build_release.py", "--out-dir", out, "--json")
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
            second_report = json.loads(second.stdout)
            second_bytes = Path(second_report["archive"]).read_bytes()
            self.assertEqual(first_bytes, second_bytes)
            self.assertEqual(hashlib.sha256(first_bytes).hexdigest(), first_report["sha256"])
            self.assertEqual(first_report["sha256"], second_report["sha256"])
            sums = (out / "SHA256SUMS").read_text(encoding="utf-8")
            self.assertIn(first_report["sha256"], sums)
            with zipfile.ZipFile(archive) as zf:
                names = set(zf.namelist())
                self.assertIn(".codex-plugin/plugin.json", names)
                self.assertIn("skills/chatgpt-codex-plugin-autopilot/SKILL.md", names)
                self.assertNotIn("tests/test_self_hosting.py", names)
                self.assertNotIn("docs/superpowers/plans/2026-08-09-self-hosting-plugin.md", names)
                self.assertNotIn(".agents/plugins/marketplace.json", names)
                self.assertNotIn("submission/reviewer-packet.json", names)


if __name__ == "__main__":
    unittest.main()

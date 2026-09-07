"""Standalone public CLI regression; requires legacy PyYAML, never Graphify."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"
SPEC = ROOT / "spec-to-task-plan/scripts/validate_spec.py"
GRAPH = ROOT / "spec-to-task-plan/scripts/validate_task_graph.py"
WAVE = ROOT / "execute-task-waves/scripts/next_wave.py"
BROWNFIELD = ROOT / "analyze-brownfield-context/scripts/validate_brownfield_bundle.py"


class IndividualRegression(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "standalone with spaces"
        shutil.copytree(FIXTURES / "individual", self.project)

    def command(self, script, *args):
        return subprocess.run([sys.executable, str(script), *map(str, args)],
            cwd=self.root, capture_output=True, text=True, timeout=30)

    def check(self, result, expected=0):
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_all_local_spec_stages_and_wave_interfaces_without_org_setup(self):
        before = {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        for stage in ("requirements", "design", "tasks", "all"):
            self.check(self.command(SPEC, "--project", self.project, "--stage", stage))
        self.check(self.command(GRAPH, self.project / "TASKS.md"))
        wave = json.loads(self.check(self.command(WAVE, self.project / "TASKS.md", "--pretty")).stdout)
        self.assertEqual(wave["wave"], 1)
        self.assertEqual([t["id"] for t in wave["tasks"]], ["2"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.project.rglob("*") if p.is_file()})
        self.assertFalse((self.project / ".sdd").exists())

    def test_completed_wave_never_admits_later_work_early(self):
        path = self.project / "TASKS.md"
        original = path.read_text(encoding="utf-8")
        path.write_text(original.replace("[ ] 2.", "[x] 2."), encoding="utf-8")
        report = json.loads(self.check(self.command(WAVE, path)).stdout)
        self.assertEqual(report["wave"], 2)
        self.assertEqual([t["id"] for t in report["tasks"]], ["3"])
        path.write_text(path.read_text(encoding="utf-8").replace("[ ] 3.", "[x] 3."), encoding="utf-8")
        self.check(self.command(GRAPH, path))
        self.assertEqual(json.loads(self.check(self.command(WAVE, path)).stdout)["status"], "complete")
        # Preserve and document the legacy spec check: all-complete TASKS has
        # no unchecked task, so full spec validation returns 1, not a repaired API.
        self.check(self.command(SPEC, "--project", self.project, "--stage", "all"), 1)

    def test_invalid_local_graph_still_fails_both_existing_tools(self):
        path = self.project / "TASKS.md"
        path.write_text(path.read_text(encoding="utf-8").replace('"tasks":["3"]', '"tasks":["missing"]'), encoding="utf-8")
        self.check(self.command(GRAPH, path), 1)
        self.check(self.command(WAVE, path), 1)

    def test_brownfield_manifest_diff_and_review_are_standalone(self):
        # Missing PyYAML fails this required test with an actionable message.
        try:
            import yaml
        except ImportError:
            self.fail("Legacy brownfield tests require PyYAML; run uv run --with pyyaml python -m unittest discover -s tests -v")
        environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        for args in (("init", "-q"), ("config", "user.name", "Synthetic fixture"),
                     ("config", "user.email", "fixture@example.invalid"),
                     ("config", "commit.gpgsign", "false"), ("config", "core.autocrlf", "false"),
                     ("add", "."), ("-c", "core.hooksPath=" + str(self.root / "no-hooks"), "commit", "-qm", "Synthetic baseline")):
            self.check(subprocess.run(["git", *args], cwd=self.project, env=environment,
                capture_output=True, text=True, timeout=30))
        self.check(self.command(BROWNFIELD, "--project", self.project, "--write-manifest"))
        knowledge = self.project / ".sdd/knowledge"
        manifest = knowledge / "source-manifest.json"
        before = manifest.read_bytes()
        metadata = json.loads(before)
        concept = (FIXTURES / "individual-concept.md.in").read_text(encoding="utf-8")
        for token, key in (("@REVISION@", "source_revision"), ("@FINGERPRINT@", "source_fingerprint"), ("@WORKTREE@", "source_worktree")):
            concept = concept.replace(token, metadata[key])
        for name in ("bundle-state.md", "source.md"):
            (knowledge / name).write_text(concept, encoding="utf-8")
        (knowledge / "index.md").write_text('---\nokf_version: "0.2"\n---\n[State](bundle-state.md)\n[Source](source.md)\n', encoding="utf-8")
        self.check(self.command(BROWNFIELD, "--project", self.project))
        self.assertEqual(yaml.safe_load(concept.split("---", 2)[1])["verified"], [])
        self.assertFalse((self.project / ".sdd/org").exists())
        self.assertFalse((self.project / "graphify-out").exists())
        (self.project / "source.txt").write_text("Changed synthetic source\n", encoding="utf-8")
        diff = json.loads(self.check(self.command(BROWNFIELD, "--project", self.project, "--diff-manifest")).stdout)
        self.assertEqual(diff["changes"], [dict(path="source.txt", change="modified")])
        self.assertEqual(manifest.read_bytes(), before)
        self.check(self.command(BROWNFIELD, "--project", self.project), 1)


if __name__ == "__main__":
    unittest.main()

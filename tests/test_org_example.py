from tests.org_helpers import TIME
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
EXAMPLE = REPO / "examples" / "three-team"
RUNNER = EXAMPLE / "run_example.py"
BUILDER = EXAMPLE / "build_snapshots.py"
COORDINATOR = REPO / "coordinate-org-sdd"


class Example(unittest.TestCase):
    def invoke(self, *args, root=EXAMPLE):
        result = subprocess.run([sys.executable, str(RUNNER), "--example-root", str(root), "--coordinator-skill", str(COORDINATOR), *args, "--format", "json"], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        self.assertEqual(result.stderr, "", result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_all_snapshots_structure_readiness_and_production_isolation(self):
        manifest = json.loads((EXAMPLE / "manifest.json").read_text())
        self.assertEqual(len(manifest["snapshots"]), 9)
        for snapshot in manifest["snapshots"]:
            with self.subTest(snapshot=snapshot["id"]):
                code, report = self.invoke("--snapshot", snapshot["id"], "--mode", "structure")
                self.assertEqual(code, snapshot["structure_exit"])
                code, report = self.invoke("--snapshot", snapshot["id"], "--allow-illustrative")
                self.assertEqual(code, snapshot["illustrative_readiness_exit"], report["diagnostics"])
                self.assertTrue(set(snapshot["expected_codes"]) <= {d["code"] for d in report["diagnostics"]})
                code, report = self.invoke("--snapshot", snapshot["id"])
                self.assertEqual(code, 2); self.assertTrue(report["illustrative"])
                self.assertIn("ILLUSTRATIVE_ONLY", {d["code"] for d in report["diagnostics"]})

    def test_all_three_teams_two_versions_pass_local_validators(self):
        for version in ("v1", "v2"):
            for team in ("catalog", "checkout", "analytics"):
                root = EXAMPLE / "sources" / version / team
                commands = [
                    [sys.executable, str(REPO / "spec-to-task-plan/scripts/validate_spec.py"), "--project", str(root), "--stage", "all"],
                    [sys.executable, str(REPO / "spec-to-task-plan/scripts/validate_task_graph.py"), str(root / "TASKS.md")],
                    [sys.executable, str(REPO / "execute-task-waves/scripts/next_wave.py"), str(root / "TASKS.md")]]
                for command in commands:
                    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_distinct_stages_and_refreshed_history(self):
        for snapshot, stage in (("02-approved-contract", "execution"), ("04-local-complete", "integration"), ("07-integration", "release")):
            self.assertEqual(self.invoke("--snapshot", snapshot, "--stage", stage, "--allow-illustrative")[0], 2)
        old = json.loads((EXAMPLE / "snapshots/08-release/approvals/release-approval.json").read_text())
        preserved = json.loads((EXAMPLE / "snapshots/09-refreshed-knowledge/approvals/release-approval.json").read_text())
        refreshed = json.loads((EXAMPLE / "snapshots/09-refreshed-knowledge/approvals/release-refreshed-approval.json").read_text())
        self.assertEqual(old, preserved)
        self.assertEqual(refreshed["supersedes"], old["id"])
        self.assertNotEqual(refreshed["target"]["digest"], old["target"]["digest"])

    def test_regeneration_deterministic_all_records_synthetic_and_no_machine_roots(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "regenerated"
            result = subprocess.run([sys.executable, str(BUILDER), "--coordinator-skill", str(COORDINATOR), "--output", str(output)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for subtree in ("sources", "snapshots"):
                for path in (EXAMPLE / subtree).rglob("*"):
                    if path.is_file(): self.assertEqual(path.read_bytes(), (output / path.relative_to(EXAMPLE)).read_bytes(), str(path))
            self.assertEqual((EXAMPLE / "manifest.json").read_bytes(), (output / "manifest.json").read_bytes())
            self.assertEqual(self.invoke("--snapshot", "08-release", "--allow-illustrative", root=output)[0], 0)
        for path in (EXAMPLE / "snapshots").rglob("*.json"):
            item = json.loads(path.read_text()); self.assertTrue(item["illustrative"])
            self.assertNotIn(str(REPO), path.read_text())
        attributes = subprocess.check_output(["git", "check-attr", "text", "--", str(EXAMPLE / "sources/v1/catalog/REQUIREMENTS.md")], cwd=REPO, text=True)
        self.assertTrue(attributes.rstrip().endswith("text: unset"))

    def test_builder_rejects_symlink_output_and_preserves_outside(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); output = base / "output"; outside = base / "outside"
            output.mkdir(); outside.mkdir(); sentinel = outside / "scope-decision.txt"; sentinel.write_text("DO NOT CHANGE")
            try: (output / "sources").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError): self.skipTest("Symlink unavailable")
            result = subprocess.run([sys.executable, str(BUILDER), "--coordinator-skill", str(COORDINATOR), "--output", str(output), "--overwrite-generated"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(), "DO NOT CHANGE")


if __name__ == "__main__": unittest.main()

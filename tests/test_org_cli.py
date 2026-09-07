from tests.org_helpers import draft, source, write_bundle
from tests import test_org_readiness as readiness_fixtures
from org_sdd.references import byte_digest, record_digest
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1] / "coordinate-org-sdd"
SCRIPT = SKILL / "scripts" / "validate_org.py"


class CLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.initiative = write_bundle(self.root / "initiative", [draft()])

    def cli(self, *args, script=SCRIPT, cwd=None):
        return subprocess.run([sys.executable, str(script), *map(str, args)], cwd=cwd or self.root,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, text=True)

    def run_json(self, *args, **kwargs):
        result = self.cli(*args, "--format", "json", **kwargs)
        self.assertEqual(result.stderr, "", result.stderr)
        return result.returncode, json.loads(result.stdout)

    def pipeline(self):
        fixture = readiness_fixtures.Readiness("test_passing_pipeline_separate_release_approval")
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.evaluator()  # write synthetic records, no claimed approvals
        mapping = dict(format_version="1.0", repositories=dict(coordination=dict(root=str(fixture.root), basis="snapshot"), team=dict(root=str(fixture.team), basis="snapshot")))
        path = self.root / "map.json"; path.write_text(json.dumps(mapping))
        return fixture, path

    def test_help_and_valid_draft_structure_not_readiness(self):
        self.assertEqual(self.cli("--help").returncode, 0)
        code, report = self.run_json("--initiative", self.initiative)
        self.assertEqual(code, 0); self.assertTrue(report["structural_valid"])
        self.assertTrue(all(s["state"] == "not_evaluated" for s in report["states"]))
        code, report = self.run_json("--initiative", self.initiative, "--mode", "readiness")
        self.assertEqual(code, 2); self.assertTrue(report["structural_valid"])
        self.assertIn("ILLUSTRATIVE_ONLY", {d["code"] for d in report["diagnostics"]})

    def test_invalid_combinations_and_safe_errors(self):
        cases = [(), ("--unknown", "SECRET-do-not-echo"), ("--initiative", self.initiative, "--stage", "execution"),
                 ("--initiative", self.initiative, "--mode", "readiness", "--handoff", "unknown"),
                 ("--initiative", self.initiative, "--mode", "readiness", "--handoff", "work", "--stage", "release"),
                 ("--initiative", self.initiative, "--candidate-task", "1"),
                 ("--initiative", self.initiative, "--as-of", "not-a-time"),
                 ("--digest", self.initiative / "initiative.json"),
                 ("--digest", self.initiative / "initiative.json", "--digest-kind", "record", "--mode", "readiness")]
        for args in cases:
            with self.subTest(args=args):
                code, report = self.run_json(*args)
                self.assertEqual(code, 3); self.assertNotIn("SECRET-do-not-echo", json.dumps(report))

    def test_top_level_io_vs_malformed_artifact(self):
        code, report = self.run_json("--initiative", self.root / "missing")
        self.assertEqual(code, 3); self.assertEqual(report["diagnostics"][0]["code"], "IO_ERROR")
        (self.initiative / "initiative.json").write_text('{"duplicate":true,"duplicate":false}')
        code, report = self.run_json("--initiative", self.initiative)
        self.assertEqual(code, 1); self.assertFalse(report["structural_valid"])
        fixture, mapping = self.pipeline()
        (fixture.root / "initiative.json").write_text("invalid JSON")
        self.assertEqual(self.run_json("--initiative", fixture.root, "--repo-map", mapping)[0], 1)
        code, report = self.run_json("--digest", self.root / "missing-source", "--digest-kind", "source")
        self.assertEqual(code, 3); self.assertEqual(report["digest_kind"], "source"); self.assertIsNone(report["digest"])

    def test_ready_baseline_determinism_no_mutations_and_missing_source(self):
        fixture, mapping = self.pipeline()
        args = ("--initiative", fixture.root, "--mode", "readiness", "--stage", "integration", "--repo-map", mapping, "--allow-illustrative")
        before = {p: p.read_bytes() for p in fixture.root.rglob("*") if p.is_file()}
        code, report = self.run_json(*args)
        self.assertEqual(code, 0, report["diagnostics"])
        self.assertTrue(report["baseline"]["sources"])
        self.assertEqual(report, self.run_json(*args)[1])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        (fixture.root / "definition.txt").unlink()
        code, report = self.run_json(*args)
        self.assertEqual(code, 2)
        self.assertIn("REFERENCE_UNRESOLVED", {d["code"] for d in report["diagnostics"]})

    def test_digest_operations_and_release_without_release_approval(self):
        fixture, mapping = self.pipeline()
        code, report = self.run_json("--digest", fixture.root / "initiative.json", "--digest-kind", "record")
        self.assertEqual(code, 0); self.assertEqual(report["digest"], record_digest(fixture.initiative))
        code, report = self.run_json("--digest", fixture.root / "definition.txt", "--digest-kind", "source")
        self.assertEqual(code, 0); self.assertEqual(report["digest"], byte_digest((fixture.root / "definition.txt").read_bytes()))
        code, report = self.run_json("--digest", fixture.root / "initiative.json", "--digest-kind", "policy")
        self.assertEqual(code, 0)
        code, report = self.run_json("--digest", fixture.root / "initiative.json", "--digest-kind", "release_scope", "--initiative", fixture.root, "--repo-map", mapping, "--allow-illustrative")
        self.assertEqual(code, 0, report["diagnostics"]); self.assertTrue(report["digest"].startswith("sha256:"))
        self.assertFalse(any(r.get("gate") == "release" for r in fixture.items))

    def test_installed_isolated_skill_and_other_cwd(self):
        isolated = self.root / "installed" / "coordinate-org-sdd"
        shutil.copytree(SKILL, isolated, ignore=shutil.ignore_patterns("__pycache__"))
        unrelated = self.root / "other"; unrelated.mkdir()
        code, report = self.run_json("--initiative", self.initiative, script=isolated / "scripts" / "validate_org.py", cwd=unrelated)
        self.assertEqual(code, 0); self.assertTrue(report["structural_valid"])

    def test_text_scope_currency_and_candidate_output(self):
        fixture, mapping = self.pipeline()
        args = ("--initiative", fixture.root, "--mode", "readiness", "--handoff", "work", "--stage", "execution", "--repo-map", mapping, "--allow-illustrative", "--candidate-task", "1")
        result = self.cli(*args)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ILLUSTRATIVE — NOT PRODUCTION AUTHORIZATION", result.stdout)
        self.assertIn("Eligible supplied candidates", result.stdout)
        code, report = self.run_json(*args)
        self.assertEqual(code, 0); self.assertEqual(report["eligible_tasks"], ["1"])
        missing = self.cli(*args[:-1], "missing-candidate")
        self.assertIn("Blocked supplied candidate", missing.stdout)
        self.assertIn("TRACE_UNRESOLVED", missing.stdout)

    def test_nested_coordination_git_root_is_explicit(self):
        workspace = self.root / "workspace"; workspace.mkdir()
        def git(*args): return subprocess.check_output(["git", "-C", str(workspace), *args], stderr=subprocess.DEVNULL).strip()
        git("init"); (workspace / "source.txt").write_bytes(b"committed coordination source")
        git("add", "source.txt"); git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-m", "fixture")
        src = source(); src.update(basis="git", revision=git("rev-parse", "HEAD").decode(), digest=byte_digest(b"committed coordination source"))
        item = draft(); item["provenance"]["sources"] = [src]
        nested = write_bundle(workspace / "initiatives" / "demo", [item])
        mapping = self.root / "git-map.json"
        mapping.write_text(json.dumps(dict(format_version="1.0", repositories=dict(coordination=dict(root=str(workspace), basis="git")))))
        args = ("--initiative", nested, "--mode", "readiness", "--repo-map", mapping, "--allow-illustrative")
        self.assertEqual(self.run_json(*args)[0], 3)
        code, report = self.run_json(*args, "--coordination-root", workspace)
        self.assertEqual(code, 2)  # unresolved draft, but pinned source verified
        self.assertEqual(report["baseline"]["sources"][0]["revision"], src["revision"])
        self.assertEqual(self.run_json(*args, "--coordination-root", self.initiative)[0], 3)
        self.assertEqual(self.run_json(*args, "--coordination-root", self.root / "missing")[0], 3)


if __name__ == "__main__": unittest.main()

"""Observable planning handoff gates; instruction review remains necessary.

These run the shared coordinator CLI rather than implementing another readiness
algorithm or asserting prose. Synthetic actors/evidence never grant authority.
"""
from tests import org_helpers
from tests import test_org_readiness as fixtures
from org_sdd.references import record_digest
from copy import deepcopy
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "coordinate-org-sdd/scripts/validate_org.py"


class Planning(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.Readiness()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def run_gate(self, stage="execution"):
        f = self.fixture
        org_helpers.write_bundle(f.root, f.items)
        mapping = f.root / "repo-map.json"
        mapping.write_text(json.dumps(dict(format_version="1.0", repositories={
            "coordination": dict(root=str(f.root), basis="snapshot"),
            "team": dict(root=str(f.team), basis="snapshot")})), encoding="utf-8")
        before = {p: p.read_bytes() for p in f.root.rglob("*") if p.is_file()}
        result = subprocess.run([sys.executable, str(CLI), "--initiative", str(f.root),
            "--mode", "readiness", "--handoff", "work", "--stage", stage,
            "--repo-map", str(mapping), "--allow-illustrative", "--format", "json"],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(before, {p: p.read_bytes() for p in f.root.rglob("*") if p.is_file()})
        report = json.loads(result.stdout)
        return result.returncode, {d["code"] for d in report["diagnostics"]}, report

    def test_complete_trace_has_no_permission_to_skip_local_gates(self):
        self.assertEqual(self.run_gate()[0], 0)
        for gate in ("requirements", "design", "tasks"):
            approval = next(r for r in self.fixture.items if r["id"] == gate + "-approval")
            approval["status"] = "proposed"
            exit_code, codes, _ = self.run_gate()
            self.assertEqual(exit_code, 2)
            self.assertIn("LOCAL_APPROVAL_MISSING", codes)
            approval["status"] = "approved"

    def test_omitted_and_unresolved_obligations_do_not_pass(self):
        f = self.fixture
        trace = deepcopy(f.handoff["trace"])
        f.handoff["trace"] = []
        self.assertIn("TRACE_UNRESOLVED", self.run_gate()[1])
        f.handoff["trace"] = trace
        f.handoff["trace"][0]["disposition"] = "unresolved"
        self.assertIn("TRACE_UNRESOLVED", self.run_gate()[1])

    def test_missing_current_local_identifier_fails(self):
        self.fixture.handoff["trace"][0]["design_elements"] = ["NONEXISTENT-DESIGN"]
        exit_code, codes, _ = self.run_gate()
        self.assertEqual(exit_code, 2)
        self.assertIn("TRACE_UNRESOLVED", codes)

    def test_not_applicable_requires_exact_approved_resolution(self):
        f = self.fixture
        trace = f.handoff["trace"][0]
        trace.update(disposition="not_applicable", requirements=[], design_elements=[], tasks=[])
        self.assertEqual(self.run_gate()[0], 2)
        evidence = f.new("evidence", "scope-resolution")
        evidence.update(purpose="resolution", outcome="passed", source_refs=[f.definition],
            contract_refs=[f.contract_ref], attachments=[f.attachment("scope.txt", b"Synthetic owner exclusion")])
        trace["resolution_ids"] = [evidence["id"]]
        self.assertEqual(self.run_gate()[0], 2)
        approval = f.approve("resolution", evidence)
        self.assertEqual(self.run_gate()[0], 0)
        # Even a newly approved resolution with the wrong obligation baseline
        # cannot justify exclusion from this handoff.
        evidence["contract_refs"][0] = dict(f.contract_ref, digest=org_helpers.DIGEST)
        approval["target"]["digest"] = record_digest(evidence)
        self.assertEqual(self.run_gate()[0], 2)

    def test_stale_or_conflicted_contract_blocks_before_requirements_gate(self):
        f = self.fixture
        self.assertEqual(self.run_gate("planning")[0], 0)
        rejection = deepcopy(next(r for r in f.items if r["id"] == "contract-approval"))
        rejection.update(id="contract-rejection", decision="rejected")
        f.items.append(rejection)
        exit_code, codes, _ = self.run_gate("planning")
        self.assertEqual(exit_code, 2)
        self.assertIn("APPROVAL_CONFLICT", codes)
        f.items.remove(rejection)
        # Remove the persisted fixture record before testing a separate state.
        (f.root / "approvals/contract-rejection.json").unlink()
        f.contract["display_version"] = "2"
        exit_code, codes, _ = self.run_gate("planning")
        self.assertEqual(exit_code, 2)
        self.assertIn("DIGEST_MISMATCH", codes)

    def test_planning_does_not_require_future_local_artifacts(self):
        f = self.fixture
        f.handoff["local_artifacts"] = dict(requirements=None, design=None, tasks=None)
        f.handoff["trace"] = []
        f.items[:] = [r for r in f.items if r["id"] not in ("requirements-approval", "design-approval", "tasks-approval")]
        self.assertEqual(self.run_gate("planning")[0], 0)
        exit_code, codes, _ = self.run_gate()
        self.assertEqual(exit_code, 2)
        self.assertIn("LOCAL_APPROVAL_MISSING", codes)
        self.assertIn("TRACE_UNRESOLVED", codes)

    def test_isolated_standalone_validator_keeps_existing_interface(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "installed-spec"
            shutil.copytree(ROOT / "spec-to-task-plan", skill)
            project = root / "project"; project.mkdir()
            (project / "REQUIREMENTS.md").write_text(
                "---\ntitle: Synthetic\nversion: 1\nstatus: draft\n---\n"
                "**APP-CORE-001**\nThe system shall preserve standalone planning.\n\n## Glossary\n", encoding="utf-8")
            for stage in ("requirements",):
                result = subprocess.run([sys.executable, str(skill / "scripts/validate_spec.py"),
                    "--project", str(project), "--stage", stage], cwd=str(root),
                    capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((project / ".sdd").exists())
            self.assertFalse((project / "DESIGN.md").exists())
            self.assertFalse((project / "TASKS.md").exists())


if __name__ == "__main__":
    unittest.main()

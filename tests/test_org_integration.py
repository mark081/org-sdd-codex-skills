"""Adversarial end-to-end CLI tests against isolated three-team snapshots."""
from tests import org_helpers
from org_sdd.references import record_digest
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/three-team"
CLI = ROOT / "coordinate-org-sdd/scripts/validate_org.py"


class OrganizationalIntegration(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / "coordination with spaces"
        self.workspace.mkdir()
        self.initiative = self.workspace / "initiative"
        shutil.copytree(EXAMPLE / "snapshots/08-release", self.initiative)
        shutil.copytree(EXAMPLE / "sources", self.workspace / "sources")
        mapping = dict(format_version="1.0", repositories={
            "coordination": dict(root=str(self.workspace), basis="snapshot")})
        for team in ("catalog", "checkout", "analytics"):
            mapping["repositories"][team] = dict(root=str(self.workspace / "sources/v2" / team), basis="snapshot")
        self.mapping = self.root / "repo-map.json"
        self.mapping.write_text(json.dumps(mapping), encoding="utf-8")

    def read(self, path):
        return json.loads((self.initiative / path).read_text(encoding="utf-8"))

    def write(self, path, value):
        (self.initiative / path).write_text(json.dumps(value), encoding="utf-8")

    def run_cli(self, stage="release", handoff=None, illustrative=True, mode="readiness", candidates=()):
        command = [sys.executable, str(CLI), "--initiative", str(self.initiative),
            "--coordination-root", str(self.workspace), "--repo-map", str(self.mapping),
            "--mode", mode, "--format", "json"]
        if mode == "readiness":
            command += ["--stage", stage]
            if handoff:
                command += ["--handoff", handoff]
            for candidate in candidates:
                command += ["--candidate-task", candidate]
        if illustrative:
            command += ["--allow-illustrative"]
        def contents():
            return {p: p.read_bytes() for p in self.workspace.rglob("*") if p.is_file() and not p.is_symlink()}
        before = contents()
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(before, contents(), "Validation mutated source artifacts")
        self.assertEqual(result.stderr, "")
        report = json.loads(result.stdout)
        return result.returncode, report, result.stdout

    def assert_blocked(self, code, **kwargs):
        exit_code, report, output = self.run_cli(**kwargs)
        self.assertEqual(exit_code, 2, report)
        self.assertIn(code, {d["code"] for d in report["diagnostics"]})
        return report, output

    def test_complete_synthetic_pipeline_is_deterministic_and_not_production(self):
        first = self.run_cli()
        self.assertEqual(first[0], 0, first[1])
        self.assertEqual(first, self.run_cli())
        self.assertTrue(first[1]["illustrative"])
        self.assertTrue(first[1]["local_gate_verification_required"])
        self.assert_blocked("ILLUSTRATIVE_ONLY", illustrative=False)
        code, report, _ = self.run_cli(mode="structure", illustrative=False)
        self.assertEqual(code, 0)
        self.assertTrue(all(s["state"] == "not_evaluated" for s in report["states"]))

    def test_duplicate_json_keys_in_unselected_record_fail_global_structure(self):
        path = self.initiative / "knowledge/analytics-knowledge.json"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace('"format_version": "1.0"', '"format_version": "1.0", "format_version": "1.0"'), encoding="utf-8")
        code, report, _ = self.run_cli(stage="execution", handoff="catalog-work", candidates=["1"])
        self.assertEqual(code, 1)
        self.assertFalse(report["structural_valid"])
        self.assertEqual(report.get("eligible_tasks", []), [])
        self.assertIn("FORMAT_INVALID", {d["code"] for d in report["diagnostics"]})

    def test_policy_edit_invalidates_otherwise_approved_handoffs(self):
        initiative = self.read("initiative.json")
        initiative["policy"]["role_assignments"][0]["actors"].append("synthetic-new-reviewer")
        self.write("initiative.json", initiative)
        # Keep the scope target current, isolating the old policy binding.
        approval = self.read("approvals/scope-approval.json")
        approval["target"]["digest"] = record_digest(initiative)
        self.write("approvals/scope-approval.json", approval)
        self.assert_blocked("APPROVAL_STALE", stage="planning", handoff="checkout-work")

    def test_revision_drift_and_missing_private_source_block_without_disclosure(self):
        source = self.workspace / "sources/v2/catalog/implementation.txt"
        original = source.read_bytes()
        secret = b"SYNTHETIC-PRIVATE-CONTENT-DO-NOT-PRINT"
        source.write_bytes(secret)
        _, output = self.assert_blocked("DIGEST_MISMATCH", stage="local_complete", handoff="catalog-work")
        self.assertNotIn(secret.decode(), output)
        source.write_bytes(original)
        # Removing only the explicit participant map simulates inaccessible
        # private source without guessing an alternate root or fetching it.
        mapping = json.loads(self.mapping.read_text(encoding="utf-8"))
        del mapping["repositories"]["catalog"]
        self.mapping.write_text(json.dumps(mapping), encoding="utf-8")
        self.assert_blocked("REFERENCE_UNRESOLVED", stage="execution", handoff="catalog-work")

    def test_traversal_and_external_symlink_are_not_read(self):
        contract = self.read("contracts/catalog-api.json")
        original = contract["definition_refs"][0]["path"]
        contract["definition_refs"][0]["path"] = "../outside.txt"
        self.write("contracts/catalog-api.json", contract)
        code, report, _ = self.run_cli(stage="planning")
        self.assertEqual(code, 1)
        self.assertIn("PATH_UNSAFE", {d["code"] for d in report["diagnostics"]})
        contract["definition_refs"][0]["path"] = original
        self.write("contracts/catalog-api.json", contract)
        external = self.root / "outside.txt"
        external.write_text("SYNTHETIC-OUTSIDE-SECRET", encoding="utf-8")
        source = self.workspace / original
        source.unlink()
        try:
            source.symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable on this host; traversal case passed")
        _, output = self.assert_blocked("PATH_UNSAFE", stage="planning")
        self.assertNotIn("SYNTHETIC-OUTSIDE-SECRET", output)
        self.assertEqual(external.read_text(encoding="utf-8"), "SYNTHETIC-OUTSIDE-SECRET")

    def test_dependency_cycle_blocks_candidates_but_not_independent_planning(self):
        catalog = self.read("handoffs/catalog-work.json")
        catalog["dependencies"].append(dict(id="wait-for-consumer", producer_id="checkout-work",
            required_stage="local_complete", consumer_stage="execution",
            obligations=catalog["obligations"], evidence_ids=[]))
        self.write("handoffs/catalog-work.json", catalog)
        report, _ = self.assert_blocked("DEPENDENCY_CYCLE", stage="execution", handoff="checkout-work", candidates=["1"])
        self.assertEqual(report["eligible_tasks"], [])
        self.assertEqual(self.run_cli(stage="planning", handoff="analytics-work")[0], 0)

    def test_artifact_command_is_inert_even_when_local_evidence_passes(self):
        marker = self.root / "must-not-exist"
        evidence = self.read("evidence/catalog-result.json")
        # A real executable payload remains data; no shell or Python execution
        # is authorized by recording it as the evidence procedure.
        evidence["procedure"] = 'python -c "from pathlib import Path; Path(' + repr(str(marker)) + ').write_text(\'executed\')"'
        self.write("evidence/catalog-result.json", evidence)
        code, report, output = self.run_cli(stage="local_complete", handoff="catalog-work")
        self.assertEqual(code, 0, report)
        self.assertFalse(marker.exists())
        self.assertNotIn(evidence["procedure"], output)

    def test_org_result_does_not_replace_local_graph_or_local_approval(self):
        code, report, _ = self.run_cli(stage="execution", handoff="catalog-work", candidates=["1"])
        self.assertEqual(code, 0, report)
        self.assertEqual(report["eligible_tasks"], ["1"])
        self.assertTrue(report["local_gate_verification_required"])
        # The pinned approved source may remain valid while the working copy's
        # current graph becomes invalid. Existing local checks must still run.
        current = self.root / "current-local"
        shutil.copytree(self.workspace / "sources/v2/catalog", current)
        tasks = current / "TASKS.md"
        text = tasks.read_text(encoding="utf-8")
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
        self.assertIsNotNone(match)
        graph = json.loads(match.group(1))
        graph["waves"][0]["tasks"] = ["missing"]
        tasks.write_text(text[:match.start(1)] + json.dumps(graph) + text[match.end(1):], encoding="utf-8")
        local = subprocess.run([sys.executable, str(ROOT / "spec-to-task-plan/scripts/validate_task_graph.py"), str(tasks)], capture_output=True, text=True, timeout=30)
        self.assertEqual(local.returncode, 1, local.stdout + local.stderr)
        approval = self.read("approvals/catalog-tasks-approval.json")
        approval["status"] = "proposed"
        self.write("approvals/catalog-tasks-approval.json", approval)
        report, _ = self.assert_blocked("LOCAL_APPROVAL_MISSING", stage="execution", handoff="catalog-work", candidates=["1"])
        self.assertEqual(report["eligible_tasks"], [])


if __name__ == "__main__":
    unittest.main()

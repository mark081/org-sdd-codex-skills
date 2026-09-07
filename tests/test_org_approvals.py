from tests.org_helpers import bundle, record, source, write_bundle
from org_sdd.approvals import ApprovalEvaluator, changed_impact
from org_sdd.references import SourceResolver, byte_digest, policy_digest, record_digest
from org_sdd.records import load_initiative
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest


class Approvals(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.items = bundle()
        for item in self.items:
            item.update(owner=dict(actor="reviewer", role="owner"))
        self.items[0]["participants"][0]["owner"] = dict(actor="reviewer", role="owner")
        self.items[0]["policy"]["role_assignments"] = [dict(role="owner", actors=["reviewer", "reviewer-two"])]
        self.items[0]["policy"]["gates"] = [dict(gate=g, required_roles=["owner"]) for g in ("scope", "contract", "requirements", "release")]
        self.items[3].update(status="approved", policy_digest=policy_digest(self.items[0]))
        self.items[3]["provenance"]["review_status"] = "human_confirmed"
        self.items[3]["target"]["digest"] = record_digest(self.items[1])

    def evaluator(self):
        write_bundle(self.root, self.items)
        dataset = load_initiative(self.root)
        self.assertTrue(dataset.valid, dataset.diagnostics)
        resolver = SourceResolver(dict(format_version="1.0", repositories=dict(coordination=dict(root=str(self.root), basis="snapshot"))), ["team"], self.root)
        return ApprovalEvaluator(dataset, resolver, allow_illustrative=True)

    def codes(self, result): return {d.code for d in result.diagnostics}

    def test_current_approval_and_no_future_completion_deadlock(self):
        result = self.evaluator().evaluate("contract", "api")
        self.assertTrue(result.approved, result.diagnostics)
        self.assertEqual(result.approval_ids, ["review"])
        self.assertEqual(self.items[2]["completion_evidence_ids"], [])

    def test_policy_and_target_mutations(self):
        self.items[1]["display_version"] = "new"
        self.assertIn("APPROVAL_STALE", self.codes(self.evaluator().evaluate("contract", "api")))
        self.items[3]["target"]["digest"] = record_digest(self.items[1])
        self.items[0]["policy"]["role_assignments"][0]["actors"].append("new-actor")
        self.assertIn("APPROVAL_STALE", self.codes(self.evaluator().evaluate("contract", "api")))

    def test_conflict_not_timestamp_order(self):
        negative = deepcopy(self.items[3]); negative.update(id="negative", decision="rejected", timestamp="2027-01-01T00:00:00Z")
        self.items.append(negative)
        codes = self.codes(self.evaluator().evaluate("contract", "api"))
        self.assertTrue({"APPROVAL_CONFLICT", "APPROVAL_REJECTED"} <= codes)
        negative.update(supersedes="review", decision="approved")
        self.assertTrue(self.evaluator().evaluate("contract", "api").approved)

    def test_stale_old_actor_does_not_veto_current_coverage(self):
        old = self.items[3]; old["decision"] = "rejected"
        self.items[1]["display_version"] = "updated"
        fresh = deepcopy(old); fresh.update(id="fresh", actor="reviewer-two", decision="approved")
        fresh["target"]["digest"] = record_digest(self.items[1]); self.items.append(fresh)
        result = self.evaluator().evaluate("contract", "api")
        self.assertTrue(result.approved, result.diagnostics)
        self.assertEqual(result.stale_approval_ids, ["review"])
        old["target"]["digest"] = fresh["target"]["digest"]
        self.assertIn("APPROVAL_REJECTED", self.codes(self.evaluator().evaluate("contract", "api")))

    def test_unrelated_role_cannot_veto_gate(self):
        self.items[0]["policy"]["role_assignments"].append(dict(role="unrelated", actors=["reviewer-two"]))
        self.items[3]["policy_digest"] = policy_digest(self.items[0])
        negative = deepcopy(self.items[3]); negative.update(id="unrelated", actor="reviewer-two", role="unrelated", decision="rejected")
        self.items.append(negative)
        self.assertTrue(self.evaluator().evaluate("contract", "api").approved)

    def test_unavailable_approval_provenance_cannot_approve_or_supersede(self):
        approval = self.items[3]
        approval["provenance"]["sources"] = [source("missing-decision.txt")]
        self.assertIn("REFERENCE_UNRESOLVED", self.codes(self.evaluator().evaluate("contract", "api")))
        approval["provenance"]["sources"] = []; approval["decision"] = "rejected"
        successor = deepcopy(approval); successor.update(id="successor", supersedes="review", decision="approved")
        successor["provenance"]["sources"] = [source("missing-decision.txt")]
        self.items.append(successor)
        codes = self.codes(self.evaluator().evaluate("contract", "api"))
        self.assertIn("APPROVAL_REJECTED", codes)
        self.assertIn("REFERENCE_UNRESOLVED", codes)

    def test_draft_successor_cannot_suppress_rejection(self):
        self.items[3]["decision"] = "rejected"
        successor = deepcopy(self.items[3]); successor.update(id="successor", supersedes="review", status="proposed", decision="approved")
        self.items.append(successor)
        self.assertIn("APPROVAL_REJECTED", self.codes(self.evaluator().evaluate("contract", "api")))
        successor.update(status="approved", decision="revoked")
        self.assertIn("APPROVAL_REVOKED", self.codes(self.evaluator().evaluate("contract", "api")))

    def test_owners_roles_illustrative(self):
        self.items[1]["owner"] = dict(unresolved="assign")
        self.assertIn("OWNER_UNRESOLVED", self.codes(self.evaluator().evaluate("contract", "api")))
        self.items[0]["policy"]["gates"][1]["required_roles"] = []
        self.assertIn("POLICY_UNRESOLVED", self.codes(self.evaluator().evaluate("contract", "api")))
        evaluator = self.evaluator(); evaluator.allow_illustrative = False
        self.assertIn("ILLUSTRATIVE_ONLY", self.codes(evaluator.evaluate("contract", "api")))

    def test_referenced_source_drift_and_impact(self):
        (self.root / "source.txt").write_bytes(b"before")
        src = source(); src["digest"] = byte_digest(b"before")
        self.items[1]["definition_refs"] = [src]
        self.items[3]["target"]["digest"] = record_digest(self.items[1])
        evaluator = self.evaluator()
        self.assertTrue(evaluator.evaluate("contract", "api").approved)
        (self.root / "source.txt").write_bytes(b"after")
        self.assertIn("APPROVAL_STALE", self.codes(evaluator.evaluate("contract", "api")))
        impact = changed_impact(evaluator.dataset, changed_sources=[src])
        self.assertTrue({"api", "work", "review"} <= set(impact["record_ids"]))
        self.assertIn("team", impact["participant_ids"])

    def test_source_artifact_approval(self):
        (self.root / "REQUIREMENTS.md").write_bytes(b"approved requirement")
        src = source("REQUIREMENTS.md"); src["digest"] = byte_digest(b"approved requirement")
        self.items[2]["local_artifacts"]["requirements"] = src
        self.items[2]["obligations"][0]["digest"] = record_digest(self.items[1])
        approval = self.items[3]
        approval.update(gate="requirements", target=dict(initiative_id="demo", record_id="work", type="source", digest=src["digest"], source=src))
        self.assertTrue(self.evaluator().evaluate("requirements", "work").approved)
        (self.root / "REQUIREMENTS.md").write_bytes(b"edited requirement")
        self.assertIn("DIGEST_MISMATCH", self.codes(self.evaluator().evaluate("requirements", "work")))

    def test_scope_bootstrap_ignores_future_checks(self):
        (self.root / "decision.txt").write_bytes(b"supplied scope decision")
        src = source("decision.txt"); src["digest"] = byte_digest(b"supplied scope decision")
        initiative = self.items[0]
        initiative["decisions"][0].update(status="resolved", resolution="Supplied decision", evidence=[src])
        initiative["policy"]["disclosure"]["status"] = "resolved"
        initiative["checks"] = [dict(id="later", owner=dict(actor="reviewer", role="owner"), stage="integration", procedure="Later check", expected="Pass", required_sources=[source("not-yet-created.txt")], required_contracts=[])]
        initiative["integration_checks"] = ["later"]
        approval = self.items[3]; approval.update(gate="scope", policy_digest=policy_digest(initiative))
        approval["target"].update(record_id="demo", digest=record_digest(initiative))
        self.assertTrue(self.evaluator().evaluate("scope", "demo").approved)


if __name__ == "__main__": unittest.main()

from tests.org_helpers import bundle, record, source, write_bundle
from org_sdd.approvals import ApprovalEvaluator
from org_sdd.evidence import EvidenceEvaluator
from org_sdd.records import load_initiative
from org_sdd.references import SourceResolver, byte_digest, policy_digest, record_digest
from pathlib import Path
from copy import deepcopy
import json
import tempfile
import unittest


class Evidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.items = bundle()
        for item in self.items:
            item["owner"] = dict(actor="reviewer", role="owner")
            item["provenance"]["review_status"] = "human_confirmed"
        self.items[0]["policy"]["role_assignments"] = [dict(role="owner", actors=["reviewer"])]
        self.items[0]["policy"]["gates"] = [dict(gate="resolution", required_roles=["owner"])]
        self.definition = self.attachment("definition.txt", b"interface definition")
        self.output = self.attachment("output.txt", b"reviewed result")
        self.items[1]["definition_refs"] = [self.definition]
        self.items[1]["compatibility"].update(assessment="compatible", evidence_ids=["result"])
        self.items[4].update(outcome="passed", source_refs=[self.definition], attachments=[self.output])

    def attachment(self, name, content):
        (self.root / name).write_bytes(content)
        ref = source(name); ref["digest"] = byte_digest(content)
        return ref

    def evaluator(self, as_of=None, illustrative=True):
        write_bundle(self.root, self.items)
        dataset = load_initiative(self.root); self.assertTrue(dataset.valid, dataset.diagnostics)
        resolver = SourceResolver(dict(format_version="1.0", repositories=dict(coordination=dict(root=str(self.root), basis="snapshot"))), ["team"], self.root)
        return EvidenceEvaluator(ApprovalEvaluator(dataset, resolver, illustrative), as_of)

    def codes(self, result): return {d.code for d in result.diagnostics}

    def test_first_contract_bootstrap_and_failed_evidence(self):
        self.assertTrue(self.evaluator().compatibility("api").satisfied)
        self.items[4]["outcome"] = "failed"
        self.assertIn("EVIDENCE_FAILED", self.codes(self.evaluator().compatibility("api")))
        self.items[4]["outcome"] = "passed"; self.items[4]["attachments"] = []
        self.assertIn("EVIDENCE_MISSING", self.codes(self.evaluator().compatibility("api")))

    def test_prior_baseline_canonical_not_raw_and_same_identity(self):
        prior = deepcopy(self.items[1]); prior["display_version"] = "before"
        prior_bytes = json.dumps(prior, indent=2).encode()
        prior_source = self.attachment("prior.json", prior_bytes)
        self.items[1]["baseline_digest"] = record_digest(prior)
        self.assertNotEqual(prior_source["digest"], self.items[1]["baseline_digest"])
        self.items[4]["baseline_digests"] = [record_digest(prior)]
        self.items[4]["attachments"].append(prior_source)
        self.assertTrue(self.evaluator().compatibility("api").satisfied)
        self.items[4]["attachments"] = [self.output]
        self.assertIn("COMPATIBILITY_UNRESOLVED", self.codes(self.evaluator().compatibility("api")))
        prior["id"] = "different"; raw = json.dumps(prior).encode(); prior_source = self.attachment("other.json", raw)
        self.items[1]["baseline_digest"] = record_digest(prior); self.items[4]["baseline_digests"] = [record_digest(prior)]
        self.items[4]["attachments"].append(prior_source)
        self.assertFalse(self.evaluator().compatibility("api").satisfied)

    def test_breaking_unknown_need_current_resolution_approval(self):
        self.items[1]["compatibility"]["assessment"] = "unknown"
        self.assertIn("COMPATIBILITY_UNRESOLVED", self.codes(self.evaluator().compatibility("api")))
        resolution = deepcopy(self.items[4]); resolution.update(id="resolve", purpose="resolution")
        self.items.append(resolution); self.items[1]["compatibility"]["resolution_ids"] = ["resolve"]
        approval = self.items[3]; approval.update(status="approved", gate="resolution", policy_digest=policy_digest(self.items[0]))
        approval["target"].update(record_id="resolve", digest=record_digest(resolution))
        self.assertTrue(self.evaluator().compatibility("api").satisfied)
        resolution["procedure"] = "changed migration"
        self.assertIn("APPROVAL_STALE", self.codes(self.evaluator().compatibility("api")))

    def test_exact_check_baseline_and_conflicting_results(self):
        self.items[0]["checks"] = [dict(id="check", owner=dict(actor="reviewer", role="owner"), stage="local_complete", procedure="Run test explicitly", expected="pass", required_sources=[self.definition], required_contracts=[])]
        self.items[4].update(purpose="verification", check_id="check")
        self.assertTrue(self.evaluator().verification("check", ["result"]).satisfied)
        extra = self.attachment("extra.txt", b"extra"); self.items[4]["source_refs"].append(extra)
        self.assertIn("EVIDENCE_STALE", self.codes(self.evaluator().verification("check", ["result"])))
        self.items[4]["source_refs"] = [self.definition]
        second = deepcopy(self.items[4]); second["id"] = "second"; self.items.append(second)
        self.assertIn("EVIDENCE_CONFLICT", self.codes(self.evaluator().verification("check", ["result", "second"])))

    def test_source_drift_illustrative_and_inert_procedure(self):
        self.items[4]["procedure"] = "$(do-not-execute)"
        self.assertTrue(self.evaluator().compatibility("api").satisfied)
        self.assertIn("ILLUSTRATIVE_ONLY", self.codes(self.evaluator(illustrative=False).compatibility("api")))
        (self.root / "definition.txt").write_bytes(b"new definition")
        self.assertIn("DIGEST_MISMATCH", self.codes(self.evaluator().compatibility("api")))

    def test_knowledge_review_expiry_separate_publication(self):
        knowledge = self.items[5]; knowledge.update(freshness="current", source_refs=[self.definition], stale_after="2026-09-10T00:00:00Z")
        evaluator = self.evaluator("2026-09-09T00:00:00Z")
        self.assertTrue(evaluator.knowledge("context").satisfied)
        self.assertIn("PUBLICATION_PENDING", self.codes(evaluator.publication("context")))
        self.assertFalse(self.evaluator().knowledge("context").satisfied)
        self.assertFalse(self.evaluator("2026-09-10T00:00:00Z").knowledge("context").satisfied)
        knowledge["provenance"]["review_status"] = "unreviewed"
        self.assertFalse(self.evaluator("2026-09-09T00:00:00Z").knowledge("context").satisfied)

    def test_publication_requires_matching_payload_not_knowledge_self_hash(self):
        knowledge = self.items[5]; knowledge.update(freshness="current", source_refs=[self.definition])
        knowledge["publication"].update(disposition="published", evidence_ids=["result"])
        self.items[4]["purpose"] = "publication"
        self.assertTrue(self.evaluator().publication("context").satisfied)
        self.items[4]["source_refs"] = []
        self.assertIn("EVIDENCE_STALE", self.codes(self.evaluator().publication("context")))

    def test_not_required_needs_explicit_scoped_resolved_decision(self):
        knowledge = self.items[5]; knowledge["publication"].update(disposition="not_required", reason="assign")
        self.assertFalse(self.evaluator().publication("context").satisfied)
        decision = self.items[0]["decisions"][0]
        decision.update(status="resolved", resolution="Owner supplied publication disposition", evidence=[self.output], affected_ids=["context"], affected_gates=["knowledge"])
        self.assertTrue(self.evaluator().publication("context").satisfied)
        knowledge["publication"]["reason"] = "text mentioning assign without explicit selection"
        self.assertFalse(self.evaluator().publication("context").satisfied)
        knowledge["publication"]["reason"] = "assign"; decision["affected_ids"] = ["api"]
        self.assertFalse(self.evaluator().publication("context").satisfied)


if __name__ == "__main__": unittest.main()

from tests.org_helpers import record, source, write_bundle, ref
from org_sdd.readiness import ReadinessEvaluator
from org_sdd.records import load_initiative
from org_sdd.references import SourceResolver, byte_digest, canonical_bytes, record_digest, policy_digest
from pathlib import Path
from copy import deepcopy
import tempfile
import unittest


class Readiness(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.team = self.root / "team"; self.team.mkdir()
        self.items = []
        self.owner = dict(actor="reviewer", role="owner")
        self.initiative = self.new("initiative", "demo")
        self.initiative.update(integration_owner=self.owner, rollout_owner=self.owner, rollback_owner=self.owner)
        self.initiative["participants"] = [dict(repository_id="team", locator=dict(type="git", url="https://example.invalid/team", path="."), owner=self.owner)]
        self.initiative["policy"]["role_assignments"] = [dict(role="owner", actors=["reviewer"])]
        self.initiative["policy"]["gates"] = [dict(gate=g, required_roles=["owner"]) for g in ("scope", "contract", "requirements", "design", "tasks", "integration", "release", "resolution")]
        decision_source = self.attachment("decision.txt", b"Synthetic owner decision")
        self.initiative["decisions"][0].update(status="resolved", resolution="Synthetic reviewed scope and disclosure", evidence=[decision_source])
        self.initiative["policy"]["disclosure"]["status"] = "resolved"
        self.contract = self.new("contract", "api")
        self.definition = self.attachment("definition.txt", b"Synthetic API definition")
        self.contract["definition_refs"] = [self.definition]
        compatibility = self.new("evidence", "compatibility")
        output = self.attachment("output.txt", b"Synthetic check output")
        compatibility.update(purpose="compatibility", outcome="passed", source_refs=[self.definition], attachments=[output])
        self.contract["compatibility"].update(assessment="compatible", evidence_ids=["compatibility"])
        self.contract_ref = dict(initiative_id="demo", record_id="api", digest=record_digest(self.contract))
        self.handoff = self.new("handoff", "work")
        self.handoff.update(supplying_owner=self.owner, receiving_owner=self.owner, obligations=[self.contract_ref])
        self.handoff["local_artifacts"] = {
            "requirements": self.attachment("REQUIREMENTS.md", b"---\nstatus: approved\n---\n# REQ-1\n", "team"),
            "design": self.attachment("DESIGN.md", b"---\nstatus: approved\n---\n# Component-1\n", "team"),
            "tasks": self.attachment("TASKS.md", b"---\nstatus: approved\n---\n- [x] 1. Implement\n- [ ] 2. Other\n- [ ] 3. Later wave\n", "team")}
        self.handoff["trace"] = [dict(obligation=self.contract_ref, disposition="implemented", requirements=["REQ-1"], design_elements=["Component-1"], tasks=["1"], resolution_ids=[])]
        self.initiative["required_contracts"] = ["api"]; self.initiative["required_handoffs"] = ["work"]
        self.initiative["checks"] = [dict(id=identity, owner=self.owner, stage=stage, procedure="Synthetic explicit test", expected="pass", required_sources=[self.definition], required_contracts=[self.contract_ref]) for identity, stage in (("local-check", "local_complete"), ("integration-check", "integration"))]
        self.initiative["integration_checks"] = ["integration-check"]
        self.handoff["acceptance_checks"] = ["local-check"]
        self.handoff["completion_evidence_ids"] = ["local-result"]
        for identity, check in (("local-result", "local-check"), ("integration-result", "integration-check")):
            item = self.new("evidence", identity)
            item.update(purpose="verification", check_id=check, outcome="passed", source_refs=[self.definition], contract_refs=[self.contract_ref], attachments=[output])
        self.approve("scope", self.initiative)
        self.approve("contract", self.contract)
        for gate in ("requirements", "design", "tasks"): self.approve(gate, self.handoff)
        self.approve("integration", next(r for r in self.items if r["id"] == "integration-result"))

    def new(self, kind, identity):
        result = record(kind, identity); result.update(owner=deepcopy(self.owner), status="approved")
        result["provenance"]["review_status"] = "human_confirmed"
        self.items.append(result); return result

    def attachment(self, name, content, repository_id="coordination"):
        root = self.team if repository_id == "team" else self.root
        (root / name).write_bytes(content)
        result = source(name, repository_id); result["digest"] = byte_digest(content); return result

    def approve(self, gate, target, release_scope=None):
        approval = self.new("approval", gate + "-approval")
        approval.update(gate=gate, policy_digest=policy_digest(self.initiative))
        if gate in ("requirements", "design", "tasks"):
            src = target["local_artifacts"][gate]
            approval["target"] = dict(initiative_id="demo", record_id=target["id"], type="source", digest=src["digest"], source=src)
        else:
            approval["target"] = dict(initiative_id="demo", record_id=target["id"], type="release_scope" if gate == "release" else "record", digest=byte_digest(canonical_bytes(release_scope)) if release_scope is not None else record_digest(target))
        return approval

    def evaluator(self):
        write_bundle(self.root, self.items)
        dataset = load_initiative(self.root)
        self.assertTrue(dataset.valid, dataset.diagnostics)
        mapping = dict(format_version="1.0", repositories=dict(coordination=dict(root=str(self.root), basis="snapshot"), team=dict(root=str(self.team), basis="snapshot")))
        return ReadinessEvaluator(dataset, SourceResolver(mapping, ["team"], self.root), allow_illustrative=True)

    def codes(self, result): return {d.code for d in result.diagnostics}

    def test_passing_pipeline_separate_release_approval(self):
        evaluator = self.evaluator()
        for stage in ("planning", "execution", "local_complete", "integration"):
            report = evaluator.evaluate(stage=stage)
            self.assertTrue(report.ready, (stage, report.diagnostics))
        release = evaluator.evaluate(stage="release")
        self.assertFalse(release.ready); self.assertIsNotNone(release.release_scope)
        self.approve("release", self.initiative, release.release_scope)
        report = self.evaluator().evaluate(stage="release")
        self.assertTrue(report.ready, report.diagnostics)
        self.assertTrue(report.local_gate_verification_required)

    def test_failed_integration_does_not_undo_local_completion(self):
        next(r for r in self.items if r["id"] == "integration-result")["outcome"] = "failed"
        evaluator = self.evaluator()
        self.assertTrue(evaluator.evaluate(stage="local_complete").ready)
        self.assertFalse(evaluator.evaluate(stage="integration").ready)
        self.assertFalse(evaluator.evaluate(stage="release").ready)

    def test_trace_identifier_and_repository_validation(self):
        self.handoff["trace"][0]["requirements"] = ["REQ-MISSING"]
        self.assertIn("TRACE_UNRESOLVED", self.codes(self.evaluator().evaluate(stage="execution")))
        self.handoff["trace"][0]["requirements"] = ["REQ-1"]
        self.handoff["local_artifacts"]["tasks"]["repository_id"] = "coordination"
        self.assertIn("TRACE_UNRESOLVED", self.codes(self.evaluator().evaluate(stage="execution")))

    def test_task_id_is_not_a_prefix_of_leaf_id(self):
        src = self.attachment("TASKS.md", b"- [x] 1.2. Child only\n", "team")
        self.handoff["local_artifacts"]["tasks"] = src
        approval = next(r for r in self.items if r["id"] == "tasks-approval")
        approval["target"].update(digest=src["digest"], source=src)
        report = self.evaluator().evaluate("work", "execution", ["1"])
        self.assertEqual(report.eligible_tasks, [])
        self.assertIn("TRACE_UNRESOLVED", self.codes(report))

    def test_participant_ownership_is_checked_by_scope_and_contract(self):
        self.initiative["participants"][0]["owner"] = dict(unresolved="assign")
        approval = next(r for r in self.items if r["id"] == "scope-approval")
        approval["target"]["digest"] = record_digest(self.initiative)
        self.assertIn("OWNER_UNRESOLVED", self.codes(self.evaluator().evaluate(stage="planning")))

    def test_unrelated_edge_evidence_cannot_satisfy_obligation(self):
        unrelated = self.new("evidence", "unrelated")
        unrelated.update(purpose="publication", outcome="passed", attachments=[self.attachment("unrelated.txt", b"unrelated proof")])
        self.handoff["dependencies"] = [dict(id="review", consumer_stage="execution", producer_id="api", required_stage="contract_approved", obligations=[self.contract_ref], evidence_ids=["unrelated"])]
        self.assertIn("EVIDENCE_STALE", self.codes(self.evaluator().evaluate(stage="execution")))

    def test_long_acyclic_chain_is_evaluated_without_recursive_depth(self):
        prior = "work"
        for index in range(1050):
            item = self.new("handoff", "chain-" + str(index))
            item.update(supplying_owner=self.owner, receiving_owner=self.owner, obligations=[])
            item["dependencies"] = [dict(id="previous", consumer_stage="planning", producer_id=prior, required_stage="planning", obligations=[], evidence_ids=[])]
            prior = item["id"]
        report = self.evaluator().evaluate(prior, "planning")
        self.assertTrue(report.ready, report.diagnostics[:2])

    def test_incomplete_local_handoff_never_reported_current(self):
        next(r for r in self.items if r["id"] == "local-result")["outcome"] = "failed"
        report = self.evaluator().evaluate(stage="integration")
        self.assertFalse(report.ready)
        self.assertFalse(report.handoff_current["work"])

    def test_source_approval_and_authored_status_cannot_bypass_evidence(self):
        next(r for r in self.items if r["id"] == "tasks-approval")["status"] = "proposed"
        self.assertIn("LOCAL_APPROVAL_MISSING", self.codes(self.evaluator().evaluate(stage="execution")))
        self.assertFalse(self.evaluator().evaluate(stage="local_complete").ready)

    def test_pending_publication_keeps_local_completion_separate(self):
        knowledge = self.new("knowledge", "context"); knowledge.update(freshness="current", source_refs=[self.definition])
        self.handoff["knowledge_ids"] = ["context"]
        evaluator = self.evaluator(); local = evaluator.evaluate(stage="local_complete")
        self.assertTrue(local.ready, local.diagnostics)
        self.assertFalse(local.handoff_current["work"])
        self.assertIn("PUBLICATION_PENDING", self.codes(evaluator.evaluate(stage="integration")))

    def test_scoped_candidate_filter_intersects_supplied_wave(self):
        # Existing current-wave candidates are 1 and 2; task 3 exists locally but
        # belongs to a later wave and must never appear without being supplied.
        producer = self.new("handoff", "provider")
        producer.update(supplying_owner=self.owner, receiving_owner=self.owner, obligations=[])
        self.handoff["dependencies"] = [dict(id="wait", consumer_stage="execution", producer_id="provider", required_stage="local_complete", obligations=[self.contract_ref], evidence_ids=[])]
        report = self.evaluator().evaluate("work", "execution", ["1", "2"])
        self.assertFalse(report.ready)
        self.assertEqual(report.eligible_tasks, ["2"])
        self.assertEqual(set(report.blocked_tasks), {"1"})
        self.assertNotIn("3", report.eligible_tasks)
        self.assertNotIn("3", report.blocked_tasks)
        next(r for r in self.items if r["id"] == "tasks-approval")["status"] = "proposed"
        self.assertEqual(self.evaluator().evaluate("work", "execution", ["1", "2"]).eligible_tasks, [])

    def test_structural_corruption_and_vacuous_scope_fail_closed(self):
        evaluator = self.evaluator(); evaluator.dataset.diagnostics.append(evaluator.error("work", "id", "FORMAT_INVALID", "Synthetic corruption"))
        evaluator = ReadinessEvaluator(evaluator.dataset, evaluator.resolver, True)
        self.assertFalse(evaluator.evaluate("work", "execution", ["1"]).structural_valid)
        self.initiative["required_handoffs"] = []
        self.assertFalse(self.evaluator().evaluate(stage="planning").ready)

    def test_contract_acceptance_check_not_orphaned(self):
        # This extra contract check is not selected by any handoff; it must not
        # block contract planning, but integration must require its evidence.
        self.contract["acceptance_checks"] = ["orphan-check"]
        self.initiative["checks"].append(dict(id="orphan-check", owner=self.owner, stage="local_complete", procedure="Synthetic required obligation check", expected="pass", required_sources=[], required_contracts=[]))
        new_ref = dict(initiative_id="demo", record_id="api", digest=record_digest(self.contract))
        self.handoff["obligations"] = [new_ref]; self.handoff["trace"][0]["obligation"] = new_ref
        for check in self.initiative["checks"]:
            if check["required_contracts"]: check["required_contracts"] = [new_ref]
        for item in self.items:
            if item["kind"] == "evidence" and item["contract_refs"]: item["contract_refs"] = [new_ref]
        for approval in self.items:
            if approval["kind"] == "approval":
                if approval["target"]["type"] == "record":
                    target = next(r for r in self.items if r["id"] == approval["target"]["record_id"])
                    approval["target"]["digest"] = record_digest(target)
        evaluator = self.evaluator()
        self.assertTrue(evaluator.evaluate(stage="planning").ready)
        self.assertIn("EVIDENCE_MISSING", self.codes(evaluator.evaluate(stage="integration")))


if __name__ == "__main__": unittest.main()

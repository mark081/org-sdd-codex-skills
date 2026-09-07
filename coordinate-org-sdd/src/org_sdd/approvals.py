"""Revision-bound approval consistency, not human identity authentication.

ApprovalEvaluator(dataset, resolver).evaluate(gate, target_id, ...)->ApprovalResult
checks effective role coverage and exact gate-scoped prerequisites. Additional
stage/evidence predicates are supplied as prerequisite_diagnostics; no graph or
future completion requirement is inferred here. changed_impact reports reverse
reference impact conservatively, independently of gate-specific readiness.
"""
from dataclasses import dataclass

from .diagnostics import Diagnostic, sorted_diagnostics
from .records import RR, SR, walk
from .references import byte_digest, canonical_bytes, policy_digest, record_digest


@dataclass
class ApprovalResult:
    approved: bool
    approval_ids: list
    diagnostics: list
    target_digest: object = None
    stale_approval_ids: object = None


class ApprovalEvaluator:
    def __init__(self, dataset, resolver, allow_illustrative=False):
        self.dataset = dataset
        self.records = dataset.records
        self.initiative = dataset.initiative
        self.resolver = resolver
        self.allow_illustrative = allow_illustrative

    def diagnostic(self, identity, field, code, message):
        return Diagnostic(code, self.dataset.files.get(identity, "<record>"), identity, field, message)

    def owner_diagnostics(self, owner, identity, field="owner"):
        roles = {r["role"]: r["actors"] for r in self.initiative["policy"]["role_assignments"]}
        if "unresolved" in owner or owner.get("actor") not in roles.get(owner.get("role"), []):
            return [self.diagnostic(identity, field, "OWNER_UNRESOLVED", "Supply an accountable owner matching a recorded role assignment")]
        return []

    def reference_diagnostics(self, target, gate, source=None):
        """Check identity, not future lifecycle completion. Return safe diagnostics."""
        diagnostics, visited = [], set()
        def inspect(value, identity, field):
            for child_field, item in walk(value, field):
                if not isinstance(item, dict): continue
                if set(item) == set(SR[1]):
                    diagnostics.extend(self.resolver.resolve(item, self.dataset.files.get(identity, "<record>"), identity, child_field).diagnostics)
                elif set(item) == set(RR[1]):
                    record = self.records.get(item["record_id"])
                    if record is None or record["initiative_id"] != item["initiative_id"]:
                        diagnostics.append(self.diagnostic(identity, child_field, "REFERENCE_UNRESOLVED", "Referenced record is unavailable"))
                    elif record_digest(record) != item["digest"]:
                        diagnostics.append(self.diagnostic(identity, child_field, "DIGEST_MISMATCH", "Referenced record differs from pinned baseline"))
                    else: inspect_record(record)
        def inspect_record(record):
            identity = record["id"]
            if identity in visited: return
            visited.add(identity)
            inspect(record["provenance"]["sources"], identity, "provenance.sources")
            kind = record["kind"]
            if kind == "contract":
                inspect(record["definition_refs"], identity, "definition_refs")
                # ID-linked review evidence must remain current; implementation
                # acceptance checks are deliberately not contract prerequisites.
                for key in ("evidence_ids", "resolution_ids"):
                    for evidence_id in record["compatibility"][key]:
                        evidence = self.records.get(evidence_id)
                        if evidence is None: diagnostics.append(self.diagnostic(identity, "compatibility." + key, "REFERENCE_UNRESOLVED", "Review evidence is unavailable"))
                        else: inspect_record(evidence)
            elif kind == "initiative":
                inspect(record["decisions"], identity, "decisions")
                # No checks, handoff completion or release evidence here.
            elif kind == "handoff":
                inspect(record["obligations"], identity, "obligations")
            elif kind in ("evidence", "knowledge"):
                inspect(record, identity, "")
        inspect_record(target)
        if source is not None: inspect(source, target["id"], "local_artifacts." + gate)
        return diagnostics

    def evaluate(self, gate, target_id, source=None, release_scope=None, prerequisite_diagnostics=()):
        if not self.dataset.valid:
            return ApprovalResult(False, [], list(self.dataset.diagnostics))
        target = self.records.get(target_id)
        if target is None:
            return ApprovalResult(False, [], [self.diagnostic(target_id, "target", "REFERENCE_UNRESOLVED", "Approval target is unavailable")])
        diagnostics = list(prerequisite_diagnostics)
        diagnostics.extend(self.owner_diagnostics(target["owner"], target_id))
        if gate == "scope":
            for i, participant in enumerate(self.initiative["participants"]):
                diagnostics.extend(self.owner_diagnostics(participant["owner"], self.initiative["id"], f"participants[{i}].owner"))
        elif gate == "contract":
            relevant = {target.get("provider"), *target.get("consumers", [])}
            for i, participant in enumerate(self.initiative["participants"]):
                if participant["repository_id"] in relevant:
                    diagnostics.extend(self.owner_diagnostics(participant["owner"], self.initiative["id"], f"participants[{i}].owner"))
        if target["status"] in ("withdrawn", "superseded"):
            diagnostics.append(self.diagnostic(target_id, "status", "APPROVAL_STALE", "Historical target cannot satisfy a current gate"))
        if target["illustrative"] and not self.allow_illustrative:
            diagnostics.append(self.diagnostic(target_id, "illustrative", "ILLUSTRATIVE_ONLY", "Synthetic records cannot authorize production work"))
        policy = self.initiative["policy"]
        roles = {entry["role"]: entry["actors"] for entry in policy["role_assignments"]}
        required = next((entry["required_roles"] for entry in policy["gates"] if entry["gate"] == gate), [])
        if not required or any(not roles.get(role) for role in required):
            diagnostics.append(self.diagnostic(target_id, "policy.gates", "POLICY_UNRESOLVED", "Supply nonempty gate role assignments"))
        for decision in self.initiative["decisions"]:
            if decision["status"] == "unresolved" and gate in decision["affected_gates"] and (target_id in decision["affected_ids"] or self.initiative["id"] in decision["affected_ids"]):
                diagnostics.append(self.diagnostic(target_id, "decisions", "POLICY_UNRESOLVED", "Resolve the applicable recorded decision before this gate"))
        if gate == "scope" and policy["disclosure"]["status"] != "resolved":
            diagnostics.append(self.diagnostic(target_id, "policy.disclosure", "POLICY_UNRESOLVED", "Resolve disclosure before organizational sharing"))
        target_type = "source" if gate in ("requirements", "design", "tasks") else "release_scope" if gate == "release" else "record"
        if target_type == "source":
            expected_source = target.get("local_artifacts", {}).get(gate)
            if source is None: source = expected_source
            if source is None or source != expected_source:
                return ApprovalResult(False, [], diagnostics + [self.diagnostic(target_id, "local_artifacts." + gate, "REFERENCE_UNRESOLVED", "Supply the exact local artifact reference")])
            digest = source["digest"]
        elif target_type == "release_scope":
            if release_scope is None:
                return ApprovalResult(False, [], diagnostics + [self.diagnostic(target_id, "release_scope", "REFERENCE_UNRESOLVED", "Supply explicitly selected current release scope")])
            digest = byte_digest(canonical_bytes(release_scope))
        else: digest = record_digest(target)
        reference_errors = self.reference_diagnostics(target, gate, source)
        diagnostics.extend(reference_errors)
        if reference_errors or prerequisite_diagnostics:
            diagnostics.append(self.diagnostic(target_id, "target", "APPROVAL_STALE", "Approval prerequisites need revalidation"))
        current_policy = policy_digest(self.initiative)
        all_approvals = [r for r in self.records.values() if r["kind"] == "approval"]
        def captured(record, verify_sources=False):
            return (record["status"] == "approved" and record["provenance"]["review_status"] == "human_confirmed"
                    and record["actor"] in roles.get(record["role"], [])
                    and not self.owner_diagnostics(record["owner"], record["id"])
                    and (not verify_sources or not self.reference_diagnostics(record, record["gate"])))
        # A draft successor cannot suppress a previously captured rejection.
        superseded = {r["supersedes"] for r in all_approvals if "supersedes" in r and captured(r, verify_sources=True)
                      and (self.allow_illustrative or not r["illustrative"])}
        decisions = {}
        accepted = []
        stale = []
        stale_roles = set()
        for approval in sorted(all_approvals, key=lambda r: r["id"]):
            pin = approval["target"]
            if approval["gate"] != gate or pin["record_id"] != target_id or pin["type"] != target_type: continue
            if approval["role"] not in required: continue
            identity = approval["id"]
            if identity in superseded or not captured(approval): continue
            if approval["illustrative"] and not self.allow_illustrative:
                diagnostics.append(self.diagnostic(identity, "illustrative", "ILLUSTRATIVE_ONLY", "Synthetic approval is not production authority")); continue
            if pin["digest"] != digest or approval["policy_digest"] != current_policy or (target_type == "source" and pin["source"] != source):
                stale.append(identity); stale_roles.add(approval["role"]); continue
            capture_errors = self.reference_diagnostics(approval, gate)
            if capture_errors:
                diagnostics.extend(capture_errors)
                stale.append(identity); stale_roles.add(approval["role"]); continue
            decisions.setdefault(approval["role"], []).append(approval)
        for role, records in decisions.items():
            values = {r["decision"] for r in records}
            if len(values) > 1:
                diagnostics.append(self.diagnostic(target_id, "approvals", "APPROVAL_CONFLICT", "Resolve contradictory effective role decisions explicitly"))
            for approval in records:
                if approval["decision"] != "approved":
                    diagnostics.append(self.diagnostic(approval["id"], "decision", "APPROVAL_REJECTED" if approval["decision"] == "rejected" else "APPROVAL_REVOKED", "An effective negative decision blocks this gate"))
                elif role in required: accepted.append(approval["id"])
        for role in required:
            if not any(r["decision"] == "approved" for r in decisions.get(role, [])):
                diagnostics.append(self.diagnostic(target_id, "approvals", "APPROVAL_MISSING", "A required role lacks a current approving decision"))
                if role in stale_roles:
                    diagnostics.append(self.diagnostic(target_id, "approvals", "APPROVAL_STALE", "Prior approval cannot cover the current role baseline"))
        return ApprovalResult(not diagnostics, sorted(accepted), sorted_diagnostics(diagnostics), digest, sorted(stale))


def changed_impact(dataset, changed_ids=(), changed_sources=()):
    """Conservative reverse content/ID-link closure, not execution eligibility.

    changed_sources contains SourceRef objects; repository/path select impacted
    claims across revisions. Returned participant IDs identify review recipients,
    not authorization to contact them. Policy mutation starts at initiative ID.
    """
    reverse, seeds = {}, set(changed_ids)
    source_keys = {(s["repository_id"], s["path"]) for s in changed_sources}
    link_fields = {"required_contracts", "required_handoffs", "evidence_ids", "resolution_ids", "completion_evidence_ids", "knowledge_ids"}
    for identity, record in dataset.records.items():
        for field, value in walk(record):
            if isinstance(value, dict):
                if set(value) == set(SR[1]) and (value["repository_id"], value["path"]) in source_keys: seeds.add(identity)
                if "record_id" in value and "initiative_id" in value: reverse.setdefault(value["record_id"], set()).add(identity)
                if "producer_id" in value: reverse.setdefault(value["producer_id"], set()).add(identity)
                for key in link_fields:
                    for linked in value.get(key, []): reverse.setdefault(linked, set()).add(identity)
        if record["kind"] == "approval": reverse.setdefault(dataset.initiative["id"], set()).add(identity)
    affected, pending = set(), list(seeds)
    while pending:
        identity = pending.pop()
        if identity in affected: continue
        affected.add(identity); pending.extend(reverse.get(identity, ()))
    participants = set()
    for identity in affected:
        record = dataset.records.get(identity, {})
        if record.get("kind") == "handoff": participants.add(record["repository_id"])
        if record.get("kind") == "contract": participants.update([record["provider"], *record["consumers"]])
        if record.get("kind") == "knowledge": participants.update(record["affected_participants"])
    return {"record_ids": sorted(affected & dataset.records.keys()), "participant_ids": sorted(participants)}

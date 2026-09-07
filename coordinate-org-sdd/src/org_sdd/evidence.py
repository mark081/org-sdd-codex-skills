"""Current evidence predicates, never test execution or overall stage readiness.

EvidenceEvaluator(approval_evaluator, as_of=None) exposes verification(check_id,
evidence_ids), compatibility(contract_id), resolution(ids, ...), knowledge(id),
and publication(id). Each returns EvidenceResult; knowledge checks local review,
publication separately checks organizational currency to avoid completion loops.
Publication pins the union of knowledge source_refs/okf_refs and the exact
contract_refs, with reviewed output attachments; it does not prove remote truth.
not_required uses publication.reason as the exact resolved decision ID scoped
to the knowledge gate and this knowledge record (or its initiative), not prose.
"""
from dataclasses import dataclass
from datetime import datetime

from .diagnostics import sorted_diagnostics
from .records import parse_json, valid_time
from .references import ReferenceFailure, record_digest


def source_identity(ref):
    return tuple(ref[key] for key in ("repository_id", "path", "revision", "digest", "basis"))


def contract_identity(ref):
    return tuple(ref[key] for key in ("initiative_id", "record_id", "digest"))


def identity_set(refs, kind="source"):
    return {source_identity(ref) if kind == "source" else contract_identity(ref) for ref in refs}


@dataclass
class EvidenceResult:
    satisfied: bool
    evidence_ids: list
    diagnostics: list


class EvidenceEvaluator:
    def __init__(self, approvals, as_of=None):
        self.approvals = approvals
        self.dataset = approvals.dataset
        self.records = approvals.records
        self.initiative = approvals.initiative
        self.resolver = approvals.resolver
        self.as_of = as_of

    def error(self, identity, field, code, message):
        return self.approvals.diagnostic(identity, field, code, message)

    def result(self, ids, diagnostics):
        return EvidenceResult(not diagnostics, sorted(set(ids)), sorted_diagnostics(diagnostics))

    def base(self, identity, purpose=None):
        diagnostics = []
        if not self.dataset.valid: return list(self.dataset.diagnostics)
        record = self.records.get(identity)
        if not record or record["kind"] != "evidence":
            return [self.error(identity, "evidence", "EVIDENCE_MISSING", "Supply the required evidence record")]
        if purpose is not None and record["purpose"] != purpose:
            diagnostics.append(self.error(identity, "purpose", "EVIDENCE_STALE", "Evidence purpose does not match its obligation"))
        diagnostics.extend(self.approvals.owner_diagnostics(record["owner"], identity))
        if record["status"] in ("superseded", "withdrawn") or record["provenance"]["review_status"] != "human_confirmed":
            diagnostics.append(self.error(identity, "provenance.review_status", "EVIDENCE_STALE", "Evidence requires current human review"))
        if record["illustrative"] and not self.approvals.allow_illustrative:
            diagnostics.append(self.error(identity, "illustrative", "ILLUSTRATIVE_ONLY", "Synthetic evidence cannot satisfy production readiness"))
        if record["outcome"] != "passed":
            diagnostics.append(self.error(identity, "outcome", "EVIDENCE_FAILED", "Record a passing result before this obligation can pass"))
        if not record["attachments"]:
            diagnostics.append(self.error(identity, "attachments", "EVIDENCE_MISSING", "Supply verifiable result attachments"))
        reference_errors = self.approvals.reference_diagnostics(record, "integration")
        diagnostics.extend(reference_errors)
        if reference_errors:
            diagnostics.append(self.error(identity, "source_refs", "EVIDENCE_STALE", "Evidence baseline is unavailable or changed"))
        return diagnostics

    def match(self, record, sources, contracts, baselines=None):
        errors = []
        for field, actual, expected in (("source_refs", identity_set(record["source_refs"]), identity_set(sources)),
                                        ("contract_refs", identity_set(record["contract_refs"], "contract"), identity_set(contracts, "contract"))):
            if actual != expected:
                errors.append(self.error(record["id"], field, "EVIDENCE_STALE", "Evidence does not match the exact required identity set"))
        if baselines is not None and set(record["baseline_digests"]) != set(baselines):
            errors.append(self.error(record["id"], "baseline_digests", "EVIDENCE_STALE", "Evidence prior baseline does not match"))
        return errors

    def verification(self, check_id, evidence_ids):
        if not self.dataset.valid: return self.result([], list(self.dataset.diagnostics))
        check = next((c for c in self.initiative["checks"] if c["id"] == check_id), None)
        if check is None:
            return self.result([], [self.error(self.initiative["id"], "checks", "EVIDENCE_MISSING", "Register the required check")])
        diagnostics = self.approvals.owner_diagnostics(check["owner"], self.initiative["id"], "checks.owner")
        if not evidence_ids:
            return self.result([], diagnostics + [self.error(self.initiative["id"], "checks", "EVIDENCE_MISSING", "Select evidence for the required check")])
        selected = []
        for identity in evidence_ids:
            diagnostics.extend(self.base(identity, "verification"))
            record = self.records.get(identity)
            if not record or record["kind"] != "evidence": continue
            if record["check_id"] != check_id:
                diagnostics.append(self.error(identity, "check_id", "EVIDENCE_STALE", "Evidence names another check"))
            diagnostics.extend(self.match(record, check["required_sources"], check["required_contracts"]))
            selected.append(identity)
        # Multiple distinct active results are ambiguous, never timestamp-ranked.
        active = [self.records[i] for i in selected if self.records[i]["status"] not in ("superseded", "withdrawn")]
        if len({record_digest(record) for record in active}) > 1:
            diagnostics.append(self.error(self.initiative["id"], "checks", "EVIDENCE_CONFLICT", "Select one unambiguous current result per check"))
        return self.result(selected, diagnostics)

    def resolution(self, evidence_ids, sources, contracts=(), baselines=()):
        if not evidence_ids:
            return self.result([], [self.error(self.initiative["id"], "resolution_ids", "COMPATIBILITY_UNRESOLVED", "Supply owner-approved resolution evidence")])
        diagnostics = []
        for identity in evidence_ids:
            diagnostics.extend(self.base(identity, "resolution"))
            record = self.records.get(identity)
            if not record or record["kind"] != "evidence": continue
            diagnostics.extend(self.match(record, sources, contracts, baselines))
            diagnostics.extend(self.approvals.evaluate("resolution", identity).diagnostics)
        return self.result(evidence_ids, diagnostics)

    def _prior_baseline(self, contract, records):
        baseline = contract["baseline_digest"]
        if baseline is None: return []
        for evidence in records:
            for source in evidence["attachments"]:
                resolved = self.resolver.resolve(source)
                if not resolved.valid: continue
                try:
                    previous = parse_json(resolved.content.decode("utf-8"))
                    if (isinstance(previous, dict) and previous.get("kind") == "contract"
                            and previous.get("id") == contract["id"] and previous.get("initiative_id") == contract["initiative_id"]
                            and record_digest(previous) == baseline): return []
                except (ValueError, UnicodeError, ReferenceFailure): continue
        return [self.error(contract["id"], "baseline_digest", "COMPATIBILITY_UNRESOLVED", "Supply a verified prior contract snapshot matching canonical baseline and identity")]

    def compatibility(self, contract_id):
        if not self.dataset.valid: return self.result([], list(self.dataset.diagnostics))
        contract = self.records.get(contract_id)
        if not contract or contract["kind"] != "contract":
            return self.result([], [self.error(contract_id, "contract", "CONTRACT_UNRESOLVED", "Supply the shared contract")])
        assessment = contract["compatibility"]
        ids = assessment["evidence_ids"]
        diagnostics = []
        if contract["illustrative"] and not self.approvals.allow_illustrative:
            diagnostics.append(self.error(contract_id, "illustrative", "ILLUSTRATIVE_ONLY", "Synthetic contract cannot satisfy production readiness"))
        if not contract["definition_refs"]:
            diagnostics.append(self.error(contract_id, "definition_refs", "CONTRACT_UNRESOLVED", "Supply authoritative definitions before approval"))
        if assessment["assessment"] == "unchanged" and contract["baseline_digest"] is None:
            diagnostics.append(self.error(contract_id, "compatibility.assessment", "COMPATIBILITY_UNRESOLVED", "First introduction cannot use unchanged as review"))
        if not ids:
            diagnostics.append(self.error(contract_id, "compatibility.evidence_ids", "COMPATIBILITY_UNRESOLVED", "Supply current reviewed compatibility evidence"))
        expected_baselines = [] if contract["baseline_digest"] is None else [contract["baseline_digest"]]
        evidence_records = []
        for identity in ids:
            diagnostics.extend(self.base(identity, "compatibility"))
            evidence = self.records.get(identity)
            if not evidence or evidence["kind"] != "evidence": continue
            evidence_records.append(evidence)
            diagnostics.extend(self.match(evidence, contract["definition_refs"], [], expected_baselines))
        diagnostics.extend(self._prior_baseline(contract, evidence_records))
        if assessment["assessment"] in ("breaking", "unknown"):
            resolution = self.resolution(assessment["resolution_ids"], contract["definition_refs"], [], expected_baselines)
            diagnostics.extend(resolution.diagnostics)
            ids = ids + resolution.evidence_ids
        return self.result(ids, diagnostics)

    def knowledge(self, knowledge_id):
        if not self.dataset.valid: return self.result([], list(self.dataset.diagnostics))
        knowledge = self.records.get(knowledge_id)
        if not knowledge or knowledge["kind"] != "knowledge":
            return self.result([], [self.error(knowledge_id, "knowledge", "KNOWLEDGE_UNRESOLVED", "Supply required knowledge")])
        diagnostics = self.approvals.owner_diagnostics(knowledge["owner"], knowledge_id)
        if knowledge["freshness"] != "current" or knowledge["provenance"]["review_status"] != "human_confirmed" or knowledge["status"] in ("superseded", "withdrawn"):
            diagnostics.append(self.error(knowledge_id, "freshness", "KNOWLEDGE_UNRESOLVED", "Knowledge must be current and human-reviewed"))
        if knowledge["illustrative"] and not self.approvals.allow_illustrative:
            diagnostics.append(self.error(knowledge_id, "illustrative", "ILLUSTRATIVE_ONLY", "Synthetic knowledge cannot satisfy production readiness"))
        diagnostics.extend(self.approvals.reference_diagnostics(knowledge, "knowledge"))
        if knowledge["stale_after"] is not None:
            if not valid_time(self.as_of):
                diagnostics.append(self.error(knowledge_id, "stale_after", "KNOWLEDGE_UNRESOLVED", "Supply an explicit timezone-qualified evaluation instant"))
            elif datetime.fromisoformat(self.as_of.replace("Z", "+00:00")) >= datetime.fromisoformat(knowledge["stale_after"].replace("Z", "+00:00")):
                diagnostics.append(self.error(knowledge_id, "stale_after", "KNOWLEDGE_UNRESOLVED", "Required knowledge has expired at the evaluated instant"))
        if any(g["gate"] == "knowledge" for g in self.initiative["policy"]["gates"]):
            diagnostics.extend(self.approvals.evaluate("knowledge", knowledge_id).diagnostics)
        return self.result([], diagnostics)

    def publication(self, knowledge_id):
        knowledge = self.records.get(knowledge_id)
        if not self.dataset.valid: return self.result([], list(self.dataset.diagnostics))
        if not knowledge or knowledge["kind"] != "knowledge":
            return self.result([], [self.error(knowledge_id, "knowledge", "KNOWLEDGE_UNRESOLVED", "Supply required knowledge")])
        publication = knowledge["publication"]
        if knowledge["illustrative"] and not self.approvals.allow_illustrative:
            return self.result([], [self.error(knowledge_id, "illustrative", "ILLUSTRATIVE_ONLY", "Synthetic publication disposition is not production evidence")])
        if publication["disposition"] == "pending":
            return self.result([], [self.error(knowledge_id, "publication", "PUBLICATION_PENDING", "Publish the reviewed outgoing update or obtain an applicable explicit decision")])
        if publication["disposition"] == "not_required":
            applicable = [d for d in self.initiative["decisions"] if knowledge_id in d["affected_ids"] or self.initiative["id"] in d["affected_ids"]]
            matched = [d for d in applicable if d["id"] == publication["reason"].strip() and d["status"] == "resolved" and "knowledge" in d["affected_gates"]]
            errors = []
            if not matched or any(d["status"] == "unresolved" and "knowledge" in d["affected_gates"] for d in applicable):
                errors.append(self.error(knowledge_id, "publication.reason", "POLICY_UNRESOLVED", "Name a resolved applicable publication decision; unresolved obligations cannot be waived"))
            for decision in matched:
                for src in decision["evidence"]:
                    errors.extend(self.resolver.resolve(src, self.dataset.files[self.initiative["id"]], self.initiative["id"], "decisions.evidence").diagnostics)
            return self.result([], errors)
        ids = publication["evidence_ids"]
        if not ids:
            return self.result([], [self.error(knowledge_id, "publication.evidence_ids", "EVIDENCE_MISSING", "Supply publication evidence for the exported payload")])
        errors = []
        expected_sources = knowledge["source_refs"] + knowledge["okf_refs"]
        for identity in ids:
            errors.extend(self.base(identity, "publication"))
            evidence = self.records.get(identity)
            if evidence and evidence["kind"] == "evidence":
                errors.extend(self.match(evidence, expected_sources, knowledge["contract_refs"]))
        return self.result(ids, errors)

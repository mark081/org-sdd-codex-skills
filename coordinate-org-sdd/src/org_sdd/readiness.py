"""Compose recorded organizational prerequisites; never authorize local execution.

ReadinessEvaluator(dataset,resolver,...).evaluate(handoff_id=None,stage=None,
candidate_tasks=None) -> ReadinessReport. Candidates MUST be the existing local
resolver's approved current-wave candidates. This module only intersects them;
the caller still runs its existing local specification/task validators and gates.
Trace matching verifies identifiers in pinned UTF-8 artifacts, not their entire
project-specific schema. No source commands or task mutations are performed.
Contract acceptance checks join integration's closure at their declared stage,
not initial contract approval. Non-applicable trace resolution pins the current
contract RecordRef plus its definition SourceRefs, with owner approval.
"""
from dataclasses import dataclass, field
import re

from .approvals import ApprovalEvaluator
from .diagnostics import sorted_diagnostics
from .evidence import EvidenceEvaluator, identity_set
from .graph import build_graph
from .records import STAGES
from .references import ReferenceFailure, record_digest, release_projection


@dataclass
class StageResult:
    record_id: str
    stage: str
    ready: bool
    diagnostics: list = field(default_factory=list)


@dataclass
class ReadinessReport:
    structural_valid: bool
    ready: bool
    scope: dict
    states: list
    diagnostics: list
    handoff_current: dict = field(default_factory=dict)
    eligible_tasks: list = field(default_factory=list)
    blocked_tasks: dict = field(default_factory=dict)
    local_gate_verification_required: bool = True
    release_scope: object = None


class ReadinessEvaluator:
    def __init__(self, dataset, resolver, allow_illustrative=False, as_of=None):
        self.dataset = dataset
        self.records = dataset.records
        self.initiative = dataset.initiative
        self.approvals = ApprovalEvaluator(dataset, resolver, allow_illustrative)
        self.evidence = EvidenceEvaluator(self.approvals, as_of)
        self.resolver = resolver
        self.graph = build_graph(dataset)
        self.memo = {}
        self.currency = {}
        self.selected_evidence = set()
        self.selected_knowledge = set()
        self.release_scope = None

    def error(self, identity, field_name, code, message):
        return self.approvals.diagnostic(identity, field_name, code, message)

    def _scope(self):
        errors = self.approvals.evaluate("scope", self.initiative["id"]).diagnostics
        if not self.initiative["participants"] or not self.initiative["required_handoffs"]:
            errors.append(self.error(self.initiative["id"], "scope", "POLICY_UNRESOLVED", "Supply nonempty participating delivery scope before readiness"))
        return errors

    def _local(self, handoff, candidate=None):
        errors, texts = [], {}
        for stage, filename in (("requirements", "REQUIREMENTS.md"), ("design", "DESIGN.md"), ("tasks", "TASKS.md")):
            source = handoff["local_artifacts"][stage]
            if source is None:
                errors.append(self.error(handoff["id"], "local_artifacts." + stage, "LOCAL_APPROVAL_MISSING", "Supply the approved local specification artifact")); continue
            if source["repository_id"] != handoff["repository_id"] or source["path"] != filename:
                errors.append(self.error(handoff["id"], "local_artifacts." + stage, "TRACE_UNRESOLVED", "Local artifact must identify its owning repository and root filename")); continue
            resolution = self.resolver.resolve(source, self.dataset.files[handoff["id"]], handoff["id"], "local_artifacts." + stage)
            errors.extend(resolution.diagnostics)
            if resolution.valid:
                try: texts[stage] = resolution.content.decode("utf-8")
                except UnicodeError: errors.append(self.error(handoff["id"], "local_artifacts." + stage, "TRACE_UNRESOLVED", "Local artifact must be readable UTF-8"))
            approval = self.approvals.evaluate(stage, handoff["id"], source=source)
            errors.extend(approval.diagnostics)
            if not approval.approved:
                errors.append(self.error(handoff["id"], "local_artifacts." + stage, "LOCAL_APPROVAL_MISSING", "Existing local artifact gate remains unsatisfied"))
        obligation_keys = {(r["initiative_id"], r["record_id"]): r for r in handoff["obligations"]}
        traces = {(t["obligation"]["initiative_id"], t["obligation"]["record_id"]): t for t in handoff["trace"]}
        if set(traces) != set(obligation_keys):
            errors.append(self.error(handoff["id"], "trace", "TRACE_UNRESOLVED", "Trace must cover exactly every handoff obligation"))
        for key, trace in traces.items():
            if key not in obligation_keys or trace["obligation"] != obligation_keys[key]:
                errors.append(self.error(handoff["id"], "trace.obligation", "TRACE_UNRESOLVED", "Trace pins must match handoff obligations")); continue
            if candidate is not None and trace["tasks"] and candidate not in trace["tasks"]: continue
            if trace["disposition"] == "not_applicable":
                contract = self.records[trace["obligation"]["record_id"]]
                errors.extend(self.evidence.resolution(trace["resolution_ids"], contract["definition_refs"], [trace["obligation"]]).diagnostics)
                continue
            if trace["disposition"] != "implemented":
                errors.append(self.error(handoff["id"], "trace.disposition", "TRACE_UNRESOLVED", "Resolve this obligation before affected work")); continue
            for mapping, artifact in (("requirements", "requirements"), ("design_elements", "design"), ("tasks", "tasks")):
                if not trace[mapping]:
                    errors.append(self.error(handoff["id"], "trace." + mapping, "TRACE_UNRESOLVED", "Supply local identifiers for this obligation"))
                for identifier in trace[mapping]:
                    if artifact == "tasks":
                        pattern = r"(?m)^\s*-\s+\[[ xX]\]\s+" + re.escape(identifier) + r"(?:\.(?:\s|$)|\s|$)"
                    else:
                        pattern = r"(?<![A-Za-z0-9_-])" + re.escape(identifier) + r"(?![A-Za-z0-9_-])"
                    if not re.search(pattern, texts.get(artifact, "")):
                        errors.append(self.error(handoff["id"], "trace." + mapping, "TRACE_UNRESOLVED", "Referenced identifier is absent from verified local artifact"))
        if candidate is not None:
            if not re.search(r"(?m)^\s*-\s+\[[ xX]\]\s+" + re.escape(candidate) + r"(?:\.(?:\s|$)|\s|$)", texts.get("tasks", "")):
                errors.append(self.error(handoff["id"], "candidate_tasks", "TRACE_UNRESOLVED", "Candidate must exist in the verified local task artifact"))
        return errors

    def _edge_applies(self, detail, handoff, candidate):
        if candidate is None or not detail["dependency"]["obligations"]: return True
        keys = {(r["initiative_id"], r["record_id"]) for r in detail["dependency"]["obligations"]}
        traces = [t for t in handoff["trace"] if (t["obligation"]["initiative_id"], t["obligation"]["record_id"]) in keys]
        # Unmapped obligations cannot be safely scoped away.
        if len(traces) != len(keys) or any(not t["tasks"] for t in traces): return True
        return any(candidate in trace["tasks"] for trace in traces)

    def _intrinsic(self, producer, consumer):
        record = self.records[consumer[0]]
        if producer[0] == consumer[0]:
            return (producer[1], consumer[1]) in (("planning", "execution"), ("execution", "local_complete"), ("integration", "release"))
        if record["kind"] == "handoff" and consumer[1] == "planning":
            return producer[1] == "contract_approved" and producer[0] in {r["record_id"] for r in record["obligations"]}
        return record["kind"] == "initiative" and consumer[1] == "integration"

    def _edge_errors(self, detail):
        handoff_id = detail["handoff_id"]
        dependency = detail["dependency"]
        errors = []
        for ref in dependency["obligations"]:
            if record_digest(self.records[ref["record_id"]]) != ref["digest"]:
                errors.append(self.error(handoff_id, detail["field"] + ".obligations", "DIGEST_MISMATCH", "Dependency obligation revision changed"))
        for identity in dependency["evidence_ids"]:
            evidence = self.records[identity]
            if evidence["check_id"] is not None:
                errors.extend(self.evidence.verification(evidence["check_id"], [identity]).diagnostics)
            else: errors.extend(self.evidence.base(identity))
            required = identity_set(dependency["obligations"], "contract")
            if not required <= identity_set(evidence["contract_refs"], "contract"):
                # Contract-embedded review evidence cannot hash its containing
                # contract; validate through that contract's exact review pins.
                covered = set()
                for ref in dependency["obligations"]:
                    contract = self.records[ref["record_id"]]
                    review_ids = contract["compatibility"]["evidence_ids"] + contract["compatibility"]["resolution_ids"]
                    if identity in review_ids and self.evidence.compatibility(contract["id"]).satisfied:
                        covered.add((ref["initiative_id"], ref["record_id"], ref["digest"]))
                if not required <= covered | identity_set(evidence["contract_refs"], "contract"):
                    errors.append(self.error(handoff_id, detail["field"] + ".evidence_ids", "EVIDENCE_STALE", "Dependency evidence is not bound to the required obligation baseline"))
        return errors

    def _currency(self, handoff):
        errors = []
        for identity in handoff["knowledge_ids"]:
            result = self.evidence.publication(identity)
            errors.extend(result.diagnostics)
            self.selected_evidence.update(result.evidence_ids)
        return errors

    def _integration(self):
        errors = self._scope()
        initiative = self.initiative
        for name in ("integration_owner", "rollout_owner", "rollback_owner"):
            errors.extend(self.approvals.owner_diagnostics(initiative[name], initiative["id"], name))
        for handoff_id in initiative["required_handoffs"]:
            currency_errors = self._currency(self.records[handoff_id])
            errors.extend(currency_errors)
            local = self.memo.get(((handoff_id, "local_complete"), None))
            self.currency[handoff_id] = bool(local and local.ready) and not currency_errors
        checks = set(initiative["integration_checks"])
        for contract_id in initiative["required_contracts"]:
            checks.update(self.records[contract_id]["acceptance_checks"])
        if not checks:
            errors.append(self.error(initiative["id"], "integration_checks", "EVIDENCE_MISSING", "Supply required integration acceptance checks"))
        check_map = {c["id"]: c for c in initiative["checks"]}
        local_ids = {identity for hid in initiative["required_handoffs"] for identity in self.records[hid]["completion_evidence_ids"]}
        for check_id in sorted(checks):
            check = check_map[check_id]
            candidates = [r["id"] for r in self.records.values() if r["kind"] == "evidence" and r["purpose"] == "verification"
                          and r["check_id"] == check_id and r["status"] not in ("superseded", "withdrawn")
                          and (check["stage"] == "integration" or r["id"] in local_ids)]
            result = self.evidence.verification(check_id, candidates)
            errors.extend(result.diagnostics); self.selected_evidence.update(result.evidence_ids)
            if check["stage"] == "integration":
                for identity in candidates:
                    errors.extend(self.approvals.evaluate("integration", identity).diagnostics)
        return errors

    def _node(self, node, candidate=None):
        cache_key = (node, candidate)
        if cache_key in self.memo: return self.memo[cache_key]
        identity, stage = node
        record = self.records[identity]
        errors = []
        if node in self.graph.blocked_nodes:
            errors = [self.error(identity, "dependencies", "DEPENDENCY_CYCLE", "Resolve the stage cycle and affected prerequisites")]
            result = StageResult(identity, stage, False, errors); self.memo[cache_key] = result; return result
        # Stage graph is acyclic here, and recursive calls follow predecessors.
        for producer in sorted(self.graph.prerequisites[node]):
            details = self.graph.dependency_details.get((producer, node), [])
            relevant = [d for d in details if self._edge_applies(d, record, candidate)]
            if details and not relevant and not self._intrinsic(producer, node): continue
            upstream_candidate = candidate if producer[0] == identity else None
            prerequisite = self._node(producer, upstream_candidate)
            if not prerequisite.ready:
                errors.extend(prerequisite.diagnostics)
                errors.append(self.error(identity, "dependencies", "DEPENDENCY_UNMET", "Required stage is not ready: " + producer[0] + "/" + producer[1]))
            for detail in relevant: errors.extend(self._edge_errors(detail))
        if stage == "contract_approved":
            errors.extend(self._scope())
            compatibility = self.evidence.compatibility(identity)
            errors.extend(compatibility.diagnostics)
            errors.extend(self.approvals.evaluate("contract", identity, prerequisite_diagnostics=compatibility.diagnostics).diagnostics)
        elif stage == "planning":
            errors.extend(self._scope())
            for name in ("owner", "supplying_owner", "receiving_owner"):
                errors.extend(self.approvals.owner_diagnostics(record[name], identity, name))
            if record["status"] in ("superseded", "withdrawn"):
                errors.append(self.error(identity, "status", "APPROVAL_STALE", "Historical handoff cannot be ready"))
            if record["illustrative"] and not self.approvals.allow_illustrative:
                errors.append(self.error(identity, "illustrative", "ILLUSTRATIVE_ONLY", "Synthetic handoff cannot authorize production"))
            errors.extend(self.approvals.reference_diagnostics(record, "planning"))
        elif stage == "execution": errors.extend(self._local(record, candidate))
        elif stage == "local_complete":
            for check_id in record["acceptance_checks"]:
                candidates = [eid for eid in record["completion_evidence_ids"] if self.records[eid]["check_id"] == check_id]
                result = self.evidence.verification(check_id, candidates)
                errors.extend(result.diagnostics); self.selected_evidence.update(result.evidence_ids)
            for knowledge_id in record["knowledge_ids"]:
                errors.extend(self.evidence.knowledge(knowledge_id).diagnostics)
                self.selected_knowledge.add(knowledge_id)
            # Report currency separately, without making publication a local
            # implementation-completion prerequisite.
            publication_errors = self._currency(record)
            self.currency[identity] = not errors and not publication_errors
        elif stage == "integration": errors.extend(self._integration())
        elif stage == "release":
            if not errors:
                try:
                    self.release_scope = release_projection(self.initiative,
                        [self.records[i] for i in self.initiative["required_contracts"]],
                        [self.records[i] for i in self.initiative["required_handoffs"]],
                        [self.records[i] for i in sorted(self.selected_evidence)],
                        [self.records[i] for i in sorted(self.selected_knowledge)])
                    errors.extend(self.approvals.evaluate("release", identity, release_scope=self.release_scope).diagnostics)
                except ReferenceFailure as exc: errors.append(exc.diagnostic)
        result = StageResult(identity, stage, not errors, sorted_diagnostics(errors))
        self.memo[cache_key] = result
        return result

    def evaluate(self, handoff_id=None, stage=None, candidate_tasks=None):
        self.memo = {}; self.currency = {}; self.selected_evidence = set(); self.selected_knowledge = set(); self.release_scope = None
        scope = dict(handoff_id=handoff_id, stage=stage)
        if not self.graph.structural_valid:
            return ReadinessReport(False, False, scope, [], self.graph.diagnostics)
        if stage not in (None, *STAGES, "integration", "release"):
            raise ValueError("Unknown readiness stage")
        if handoff_id is not None and (handoff_id not in self.records or self.records[handoff_id]["kind"] != "handoff" or stage in ("integration", "release")):
            raise ValueError("Invalid handoff readiness selector")
        if candidate_tasks is not None and (handoff_id is None or stage != "execution"):
            raise ValueError("Candidates require a handoff execution scope")
        if candidate_tasks is not None and (not all(isinstance(i, str) and i.strip() for i in candidate_tasks) or len(set(candidate_tasks)) != len(candidate_tasks)):
            raise ValueError("Candidate identities must be unique nonempty strings")
        handoffs = [handoff_id] if handoff_id else self.initiative["required_handoffs"]
        nodes = []
        for selected_stage in ([stage] if stage else list(STAGES) + ([] if handoff_id else ["integration", "release"])):
            if selected_stage in STAGES: nodes.extend((identity, selected_stage) for identity in handoffs)
            else: nodes.append((self.initiative["id"], selected_stage))
        needed = set(nodes)
        for node in nodes: needed.update(self.graph.ancestors(node))
        # Seed memo in prerequisite order; long acyclic chains do not recurse.
        for node in self.graph.order:
            if node in needed: self._node(node)
        states = [self._node(node) for node in sorted(nodes)]
        errors = [d for state in states for d in state.diagnostics]
        if not nodes: errors.extend(self._scope())
        eligible, blocked = [], {}
        for candidate in candidate_tasks or []:
            result = self._node((handoff_id, "execution"), candidate)
            if result.ready: eligible.append(candidate)
            else: blocked[candidate] = result.diagnostics
        return ReadinessReport(True, bool(states) and not errors, scope, states, sorted_diagnostics(errors),
                               dict(self.currency), eligible, blocked, True, self.release_scope)

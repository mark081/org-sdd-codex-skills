"""Synthetic foundation fixtures shared by downstream tests.

draft() returns an independent structurally valid unresolved initiative.
record(kind, id) returns a standalone shaped record; bundle() returns all six
kinds with valid internal identity links but intentionally unverified digests.
write_bundle(root, records) writes fixtures only; use deepcopy before mutation.
These fixtures are illustrative and never production approvals/readiness.
Import tests.org_helpers BEFORE org_sdd modules in every downstream test module.
This loads tests/__init__.py under both named and discovery unittest invocation.
"""
import json
from copy import deepcopy
from pathlib import Path

from org_sdd.records import DIRECTORIES

DIGEST = "sha256:" + "a" * 64
TIME = "2026-09-07T12:00:00Z"


def owner(): return {"unresolved": "assign"}


def source(path="source.txt", repository_id="coordination"):
    return dict(repository_id=repository_id, path=path, revision=None, digest=DIGEST, basis="snapshot", note="Synthetic source")


def ref(identity="api"):
    return dict(initiative_id="demo", record_id=identity, digest=DIGEST)


def record(kind, identity=None):
    identity = identity or {"initiative": "demo", "contract": "api", "handoff": "work", "approval": "review", "evidence": "result", "knowledge": "context"}[kind]
    base = dict(format_version="1.0", kind=kind, id=identity, initiative_id="demo", owner=owner(), status="draft",
                provenance=dict(sources=[], observed_at=TIME, review_status="unreviewed", note="Synthetic fixture"), illustrative=True)
    payload = {
        "initiative": dict(purpose="Demo", scope="Synthetic", participants=[], integration_owner=owner(), rollout_owner=owner(), rollback_owner=owner(),
                           policy=dict(role_assignments=[], gates=[], disclosure=dict(status="unresolved", decision_id="assign")),
                           decisions=[dict(id="assign", question="Assign owners", owner_role="owner", affected_ids=["demo"], affected_gates=["scope"], status="unresolved", resolution=None, evidence=[])],
                           required_contracts=[], required_handoffs=[], checks=[], integration_checks=[]),
        "contract": dict(category="api", provider="team", consumers=[], definition_refs=[], display_version="1", baseline_digest=None, acceptance_checks=[],
                         compatibility=dict(assessment="unknown", rationale="Await review", evidence_ids=[], resolution_ids=[])),
        "handoff": dict(supplying_owner=owner(), receiving_owner=owner(), repository_id="team", scope="Synthetic work", obligations=[ref()],
                        local_artifacts=dict(requirements=None, design=None, tasks=None), trace=[], dependencies=[], acceptance_checks=[], completion_evidence_ids=[], knowledge_ids=[]),
        "approval": dict(actor="reviewer", role="owner", gate="contract", decision="approved", timestamp=TIME,
                         target=dict(**ref(), type="record"), policy_digest=DIGEST),
        "evidence": dict(check_id=None, purpose="compatibility", outcome="not_run", procedure="Review only", timestamp=TIME,
                         source_refs=[], contract_refs=[], baseline_digests=[], attachments=[]),
        "knowledge": dict(source_refs=[], contract_refs=[], affected_participants=[], freshness="unresolved", stale_after=None, okf_refs=[],
                          publication=dict(disposition="pending", evidence_ids=[], reason="Await review")),
    }[kind]
    return deepcopy(dict(base, **payload))


def draft(): return record("initiative")


def bundle():
    records = [record(k) for k in ("initiative", "contract", "handoff", "approval", "evidence", "knowledge")]
    records[0]["participants"] = [dict(repository_id="team", locator=dict(type="git", url="https://example.invalid/team.git", path="."), owner=owner())]
    records[0]["required_contracts"] = ["api"]
    records[0]["required_handoffs"] = ["work"]
    return records


def write_bundle(root, records):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for item in records:
        path = root / "initiative.json" if item["kind"] == "initiative" else root / DIRECTORIES[item["kind"]] / (item["id"] + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(item), encoding="utf-8")
    return root

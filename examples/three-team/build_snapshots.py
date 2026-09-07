#!/usr/bin/env python3
"""Generate deterministic illustrative snapshots from explicit synthetic facts.

No test-module imports, network, dispatch, actual approvals or artifact commands.
Only sources/, snapshots/ and manifest.json beneath --output are generated.
Existing differing files require explicit --overwrite-generated.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

TIME = "2026-09-07T12:00:00Z"
TEAMS = ("catalog", "checkout", "analytics")
OWNER = {"actor": "synthetic-owner", "role": "example-reviewer"}
STAGES = (
    ("01-draft", "v1", "planning", None, 2, ["POLICY_UNRESOLVED"]),
    ("02-approved-contract", "v1", "planning", None, 0, []),
    ("03-blocked-execution", "v1", "execution", "checkout-work", 2, ["DEPENDENCY_UNMET"]),
    ("04-local-complete", "v1", "local_complete", None, 0, []),
    ("05-breaking-change", "v2", "planning", "checkout-work", 2, ["COMPATIBILITY_UNRESOLVED", "DIGEST_MISMATCH"]),
    ("06-migration-resolution", "v2", "execution", None, 0, []),
    ("07-integration", "v2", "integration", None, 0, []),
    ("08-release", "v2", "release", None, 0, []),
    ("09-refreshed-knowledge", "v2", "release", None, 0, []),
)


def record(kind, identity):
    return dict(format_version="1.0", kind=kind, id=identity, initiative_id="catalog-expansion", owner=deepcopy(OWNER),
                status="approved", provenance=dict(sources=[], observed_at=TIME, review_status="human_confirmed",
                note="ILLUSTRATIVE synthetic scenario; no real human approval or operational result."), illustrative=True)


def local_documents(team, version, obligation):
    requirement = team.upper() + "-ORG-001"
    metadata = ("---\ntitle: Synthetic " + team + " catalog change\ndocument_id: EXAMPLE-" + team.upper() + "\nversion: " + version[1:] + ".0.0\nstatus: approved\ncreated: 2026-09-07\nupdated: 2026-09-07\nowner: synthetic-owner\nintended_users: Synthetic tutorial teams\nintended_region: Example only\nnotation: EARS\nreviewers: []\napprovals: []\nillustrative: true\n---\n")
    trace = ("\n## Organizational traceability\nInitiative: catalog-expansion. Handoff: " + team + "-work.\nExact obligation RecordRef:\n```json\n" + json.dumps(obligation, sort_keys=True) + "\n```\nMapping: " + requirement + " -> DESIGN-1 -> task 1. Disposition: implemented (allocated, not completed).\nCurrent initiative/handoff digests are held separately to avoid content-hash cycles.\n")
    requirements = metadata + "# Requirements: Synthetic " + team + "\n\n## Purpose and boundary\nDemonstrate one local SDD handoff; not production software or real approval.\n\n## Problem statement\nThis team must agree on the shared catalog interface.\n\n## Goals and success measures\nOne obligation maps to one design property and one leaf task, with exact-baseline evidence.\n\n## Non-goals\nNo real deployment, payment, event broker or organization policy.\n\n## Stakeholders\nSynthetic Catalog provider, Checkout purchaser and Analytics reporting consumer.\n\n## Scope and workflow\nReview requirements, then design, then task plan with three separate actual adopter gates.\n\n## EARS conventions\nShall is mandatory; When introduces a trigger.\n\n## Requirements\n**" + requirement + " — Shared catalog boundary**\nWhen a catalog item is supplied, the " + team + " component shall preserve item_id and price" + (" and required currency" if version == "v2" else "") + " under the pinned shared contract.\nPriority: P1. Verification: owner-run boundary check with attached source and contract identities. Acceptance: all required fields are preserved; missing required fields are rejected.\n\n## Security, privacy and quality\nUse synthetic data only. Preserve identity and do not infer deployment authority.\n\n## Data and provenance\nPin the supplied interface definition and tested local snapshot bytes.\n\n## User story\nAs this team's owner, I can verify my contribution without taking control of another repository.\n\n## Validation and release gates\nThis fixture's approved status is illustrative. Real requirements/design/tasks each need their own supplied approval; local completion is not release.\n\n## Decisions and remaining open questions\nNo production policy is resolved by this example. Adopter owner supplies real authority before use.\n\n## Glossary\nBoundary: the pinned catalog item interface shared by the three synthetic teams.\n\n## Assumptions and change control\nThis is a preserved synthetic approved-plan snapshot. Material changes return to review.\n" + trace
    design = metadata + "# Design Document: Synthetic " + team + "\n\n## Overview\nImplement " + requirement + " through one explicit boundary adapter.\n\n### Key Design Decisions\nReuse the shared schema; do not infer approval from a version label.\n\n## Architecture\n```mermaid\nflowchart LR\n  Catalog -->|API| Checkout\n  Catalog -->|catalog.item.changed| Analytics\n```\n\n### Component Interaction Flow\nCatalog serves Checkout through the API and emits versioned catalog.item.changed events to Analytics. Both representations use the pinned boundary definition.\n\n## Components and Interfaces\n### DESIGN-1\nThe local adapter preserves required catalog fields and rejects missing required fields.\n\n## Data Models\nitem_id and price" + (" plus required currency" if version == "v2" else "") + "; the authoritative definition specifies the derived event name, version, payload and semantics as part of the primary API boundary contract.\n\n## Correctness Properties\nFor every accepted item, all fields required by the pinned definition survive the adapter; invalid input is rejected (" + requirement + ").\n\n## Error Handling\nReject missing required fields and report the owner-check failure; no silent migration.\n\n## Testing Strategy\nUnit: required-field preservation and rejection. Integration: Catalog/Checkout/Analytics check at matching revisions. Smoke: local validators and wave resolver. Synthetic result attachments are illustrative, not actual execution claims.\n" + trace
    tasks = metadata + "# Implementation Plan: Synthetic " + team + "\n\n## Overview\nOne bounded local contribution to the shared catalog change.\n\n## Execution Contract\nRoot integration owner alone edits task status. Implement only the assigned leaf after real local approval; preserve unrelated work and all knowledge-review gates.\n\n## Tasks\n- [ ] 1. Implement the approved catalog boundary\n  - Owner/surfaces: synthetic " + team + " owner; implementation.txt synthetic source only.\n  - Acceptance: preserve required shared fields; reject missing fields; record exact source and contract baseline.\n  - Verification: owner-run boundary check and integration evidence; this sample records simulated outcomes only.\n  - _Requirements: " + requirement + "_; design property DESIGN-1.\n\n## Integration and Governance Checkpoints\nObtain actual local approvals before execution; check provider local completion before consumer work; integration and release remain distinct.\n\n## Notes\nNo optional tasks. This approved snapshot intentionally retains unchecked tasks; live progress belongs to a separate working TASKS.md. Never treat this synthetic status as real authority.\n\n## Task Dependency Graph\n```json\n{\"waves\":[{\"id\":0,\"tasks\":[\"1\"]}]}\n```\n" + trace
    return dict(requirements=requirements, design=design, tasks=tasks)


class Builder:
    def __init__(self, output, overwrite=False):
        if Path(output).is_symlink(): raise ValueError("Output root must not be a symlink")
        self.output = Path(output).resolve()
        self.overwrite = overwrite

    def write(self, path, content):
        relative = Path(path)
        if relative.is_absolute() or any(part in (".", "..") for part in relative.parts): raise ValueError("Generated path must be relative")
        path = self.output / relative
        current = self.output
        for part in relative.parts:
            current = current / part
            if current.is_symlink(): raise ValueError("Generated targets and parents must not be symlinks")
        if not path.resolve().is_relative_to(self.output): raise ValueError("Generated target escapes output root")
        if path.exists() and not path.is_file(): raise ValueError("Generated target must be a regular file")
        if isinstance(content, str): content = content.encode("utf-8")
        if path.exists() and path.read_bytes() != content and not self.overwrite:
            raise ValueError("Generated file differs; inspect before --overwrite-generated: " + path.relative_to(self.output).as_posix())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return content

    def json(self, path, value):
        return self.write(path, json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")

    def source(self, path, content, repository_id="coordination", relative=None):
        content = self.write(path, content)
        return dict(repository_id=repository_id, path=relative or path, revision=None, digest=byte_digest(content), basis="snapshot",
                    note="Synthetic preserved snapshot; not a live repository or remote-current claim.")

    def approval(self, identity, gate, target, initiative, scope=None, source=None, supersedes=None):
        approval = record("approval", identity)
        target_ref = dict(initiative_id=initiative["id"], record_id=target["id"], type="record", digest=record_digest(target))
        if source is not None: target_ref.update(type="source", digest=source["digest"], source=source)
        if scope is not None: target_ref.update(type="release_scope", digest=byte_digest(canonical_bytes(scope)))
        approval.update(actor=OWNER["actor"], role=OWNER["role"], gate=gate, decision="approved", timestamp=TIME,
                        target=target_ref, policy_digest=policy_digest(initiative))
        if supersedes: approval["supersedes"] = supersedes
        return approval

    def evidence(self, identity, purpose, sources, attachments, contracts=(), check=None, outcome="passed", baselines=()):
        item = record("evidence", identity)
        item.update(check_id=check, purpose=purpose, outcome=outcome, procedure="Synthetic owner-reviewed procedure; runner never executes this text.",
                    timestamp=TIME, source_refs=list(sources), contract_refs=list(contracts), baseline_digests=list(baselines), attachments=list(attachments))
        return item

    def build(self):
        decision = self.source("sources/scope-decision.txt", "ILLUSTRATIVE: one provider, two consumers; example roles and disclosure only.\n")
        output = self.source("sources/check-output.txt", "ILLUSTRATIVE synthetic passing test and review attachment, not real execution.\n")
        definitions, contracts, compatibility = {}, {}, {}
        for version in ("v1", "v2"):
            schema = {"operation": "GET /catalog/items", "fields": ["item_id", "price"] + (["currency"] if version == "v2" else []),
                "change": "initial" if version == "v1" else "required currency field; consumers must migrate",
                "derived_event": {"name": "catalog.item.changed", "version": version,
                    "producer": "catalog", "consumer": "analytics", "payload_fields": ["item_id", "price"] + (["currency"] if version == "v2" else []),
                    "semantics": "Synthetic item-update notification; Analytics rejects missing required fields and groups accepted values for reporting."},
                "boundary": "One reviewed boundary covers the Catalog API and its derived item event; primary category is API.", "illustrative": True}
            definitions[version] = self.source("sources/" + version + "/catalog-api.json", json.dumps(schema, sort_keys=True, indent=2) + "\n")
            contract = record("contract", "catalog-api")
            baseline = None if version == "v1" else record_digest(contracts["v1"])
            compatibility[version] = self.evidence("compatibility-" + version, "compatibility", [definitions[version]], [output], baselines=[] if baseline is None else [baseline])
            if baseline:
                prior_raw = json.dumps(contracts["v1"], sort_keys=True, indent=2) + "\n"
                prior = self.source("sources/prior-catalog-contract.json", prior_raw)
                compatibility[version]["attachments"].append(prior)
            contract.update(category="api", provider="catalog", consumers=["checkout", "analytics"], definition_refs=[definitions[version]],
                display_version="1.0.0" if version == "v1" else "2.0.0", baseline_digest=baseline,
                acceptance_checks=["catalog-check", "checkout-check", "analytics-check", "end-to-end"],
                compatibility=dict(assessment="compatible" if version == "v1" else "breaking", rationale="Synthetic reviewed initial interface" if version == "v1" else "New required field requires consumer migration",
                                   evidence_ids=["compatibility-" + version], resolution_ids=[] if version == "v1" else ["currency-migration"]))
            contracts[version] = contract
        self.contracts = contracts
        release_approval = None
        manifest = dict(format_version="1.0", illustrative=True, initiative_id="catalog-expansion", snapshots=[])
        for number, (name, version, requested_stage, handoff_selector, expected_code, expected_codes) in enumerate(STAGES, 1):
            contract = deepcopy(contracts[version])
            if number == 5: contract["compatibility"]["resolution_ids"] = []
            current_ref = dict(initiative_id="catalog-expansion", record_id="catalog-api", digest=record_digest(contract))
            intended_ref = dict(initiative_id="catalog-expansion", record_id="catalog-api", digest=record_digest(contracts[version]))
            received_ref = dict(initiative_id="catalog-expansion", record_id="catalog-api", digest=record_digest(contracts["v1"])) if number == 5 else current_ref
            initiative = record("initiative", "catalog-expansion")
            initiative.update(purpose="Synthetic three-team catalog currency rollout", scope="Catalog provides API and derived item events; Checkout purchases items; Analytics consumes catalog.item.changed events.",
                participants=[dict(repository_id=t, locator=dict(type="git", url="https://example.invalid/" + t, path="."), owner=deepcopy(OWNER)) for t in TEAMS],
                integration_owner=deepcopy(OWNER), rollout_owner=deepcopy(OWNER), rollback_owner=deepcopy(OWNER),
                policy=dict(role_assignments=[dict(role=OWNER["role"], actors=[OWNER["actor"]])],
                            gates=[dict(gate=g, required_roles=[OWNER["role"]]) for g in ("scope", "contract", "requirements", "design", "tasks", "knowledge", "integration", "release", "resolution")],
                            disclosure=dict(status="resolved", decision_id="example-scope")),
                decisions=[dict(id="example-scope", question="Synthetic scope, ownership and disclosure?", owner_role=OWNER["role"], affected_ids=["catalog-expansion"], affected_gates=["scope"], status="resolved", resolution="Illustrative scenario only; no adopter policy", evidence=[decision])],
                required_contracts=["catalog-api"], required_handoffs=[t + "-work" for t in TEAMS], checks=[], integration_checks=["end-to-end"])
            items = [initiative, contract, deepcopy(compatibility[version])]
            migration = None
            if version == "v2" and number != 5:
                migration = self.evidence("currency-migration", "resolution", [definitions[version]], [output], baselines=[contract["baseline_digest"]])
                migration["procedure"] = "ILLUSTRATIVE: Catalog adds currency; Checkout prices by currency; Analytics groups amounts by currency."
                items.append(migration)
            handoffs, knowledge_records, local_results, publication_results = [], [], [], []
            local_sources = []
            for team in TEAMS:
                code = self.source("sources/" + version + "/" + team + "/implementation.txt", "ILLUSTRATIVE " + team + " implementation " + version + "\n", team, "implementation.txt")
                local_sources.append(code)
                docs = local_documents(team, version, intended_ref)
                artifacts = {stage: self.source("sources/" + version + "/" + team + "/" + stage.upper() + ".md", text, team, stage.upper() + ".md") for stage, text in docs.items()}
                handoff = record("handoff", team + "-work")
                dependencies = [] if team == "catalog" else [dict(id="catalog-implemented", consumer_stage="execution", producer_id="catalog-work", required_stage="local_complete", obligations=[received_ref], evidence_ids=[])]
                handoff.update(supplying_owner=deepcopy(OWNER), receiving_owner=deepcopy(OWNER), repository_id=team,
                    scope="Synthetic " + team + " contribution", obligations=[received_ref], local_artifacts=artifacts if number >= 3 else {stage: None for stage in artifacts},
                    trace=[dict(obligation=received_ref, disposition="implemented", requirements=[team.upper() + "-ORG-001"], design_elements=["DESIGN-1"], tasks=["1"], resolution_ids=[])] if number >= 3 else [],
                    dependencies=dependencies, acceptance_checks=[team + "-check"], completion_evidence_ids=[team + "-result"] if number >= 3 else [], knowledge_ids=[team + "-knowledge"] if number >= 4 else [])
                handoffs.append(handoff); items.append(handoff)
                initiative["checks"].append(dict(id=team + "-check", owner=deepcopy(OWNER), stage="local_complete", procedure="Synthetic " + team + " boundary verification", expected="pass", required_sources=[code], required_contracts=[current_ref]))
                if number >= 3:
                    passed = number in (4, 7, 8, 9) or (number == 6 and team == "catalog")
                    result = self.evidence(team + "-result", "verification", [code], [output] if passed else [], [current_ref], team + "-check", "passed" if passed else "not_run")
                    items.append(result); local_results.append(result)
                if number >= 4:
                    boundary_path = "boundary-refreshed.md" if number == 9 else "boundary.md"
                    text = "# Synthetic reviewed boundary\n" + team + " uses catalog " + version + ("; refreshed owner observation and currency semantics" if number == 9 else "") + "\n"
                    boundary = self.source("sources/" + version + "/" + team + "/" + boundary_path, text, team, boundary_path)
                    knowledge = record("knowledge", team + "-knowledge")
                    knowledge.update(source_refs=[code], contract_refs=[current_ref], affected_participants=[team], freshness="current", stale_after=None, okf_refs=[boundary],
                        publication=dict(disposition="published" if number >= 7 else "pending", evidence_ids=[team + "-publication"] if number >= 7 else [], reason="Synthetic reviewed publication evidence" if number >= 7 else "Synthetic outgoing update awaits publication"))
                    items.append(knowledge); knowledge_records.append(knowledge)
                    if number >= 7:
                        publication = self.evidence(team + "-publication", "publication", [code, boundary], [output], [current_ref])
                        items.append(publication); publication_results.append(publication)
            initiative["checks"].append(dict(id="end-to-end", owner=deepcopy(OWNER), stage="integration", procedure="Synthetic Catalog + Checkout + Analytics integration", expected="pass", required_sources=local_sources, required_contracts=[current_ref]))
            integration = None
            if number >= 7:
                integration = self.evidence("integration-result", "verification", local_sources, [output], [current_ref], "end-to-end")
                items.append(integration)
            if number == 1:
                initiative["status"] = "draft"
                initiative["policy"]["disclosure"]["status"] = "unresolved"
                initiative["decisions"][0].update(status="unresolved", resolution=None, evidence=[])
                for item in items:
                    item["status"] = "draft"; item["provenance"]["review_status"] = "unreviewed"
            else:
                items.append(self.approval("scope-approval", "scope", initiative, initiative))
                if number != 5: items.append(self.approval("contract-approval", "contract", contract, initiative))
                if migration: items.append(self.approval("migration-approval", "resolution", migration, initiative))
                if number >= 3:
                    for handoff in handoffs:
                        for stage, src in handoff["local_artifacts"].items():
                            items.append(self.approval(handoff["repository_id"] + "-" + stage + "-approval", stage, handoff, initiative, source=src))
                    for knowledge in knowledge_records:
                        items.append(self.approval(knowledge["id"] + "-approval", "knowledge", knowledge, initiative))
                if integration: items.append(self.approval("integration-approval", "integration", integration, initiative))
                if number >= 8:
                    projection = release_projection(initiative, [contract], handoffs, local_results + publication_results + [integration], knowledge_records)
                    if number == 9:
                        items.append(deepcopy(release_approval))
                        items.append(self.approval("release-refreshed-approval", "release", initiative, initiative, scope=projection, supersedes="release-approval"))
                    else:
                        release_approval = self.approval("release-approval", "release", initiative, initiative, scope=projection)
                        items.append(release_approval)
            for item in items:
                directory = {"contract": "contracts", "handoff": "handoffs", "approval": "approvals", "evidence": "evidence", "knowledge": "knowledge"}.get(item["kind"])
                path = "initiative.json" if item["kind"] == "initiative" else directory + "/" + item["id"] + ".json"
                self.json("snapshots/" + name + "/" + path, item)
            manifest["snapshots"].append(dict(id=name, source_version=version, stage=requested_stage, handoff=handoff_selector,
                                             structure_exit=0, illustrative_readiness_exit=expected_code, production_readiness_exit=2,
                                             expected_codes=expected_codes,
                                             command="python examples/three-team/run_example.py --snapshot " + name + " --coordinator-skill coordinate-org-sdd --allow-illustrative --format json"))
        self.json("manifest.json", manifest)
        return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coordinator-skill", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--overwrite-generated", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(args.coordinator_skill.resolve() / "src"))
    global byte_digest, canonical_bytes, record_digest, policy_digest, release_projection
    from org_sdd.references import byte_digest, canonical_bytes, record_digest, policy_digest, release_projection
    manifest = Builder(args.output, args.overwrite_generated).build()
    print("Generated " + str(len(manifest["snapshots"])) + " illustrative snapshots; no production approval.")


if __name__ == "__main__": main()

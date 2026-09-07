# Organizational records — format 1.0

Normative data contract for ORG-CORE-002/003/004, ORG-CON-001 and ORG-SEC-001/002. Read [references.md](references.md) for identity, hashing, source resolution and participation. Gate algorithms and CLI behavior belong to task 2, not this document. These contracts define reference tooling, not adopter policy or authenticated authority.

## Common types and structure

Records are UTF-8 strict JSON objects. Reject duplicate keys, nonfinite numbers, unknown fields, wrong types, unknown kinds and unsupported versions; do not coerce strings to booleans or numbers. Version 1.0 uses strings, booleans, null, arrays and objects only; no numeric fields are defined. Every listed field is required unless explicitly optional. Arrays preserve authored order for hashing. ID arrays and reference arrays must not repeat the same identity. Empty arrays represent no declared items, not proof that no obligations exist.

- `ID`: string matching `[a-z][a-z0-9-]{0,63}`. IDs are unique across all six record kinds within an initiative. Actor, role and repository IDs are separate namespaces.
- `Text`: nonempty string; whitespace-only strings are invalid.
- `Time`: ISO 8601 datetime with seconds and a timezone, e.g. `2026-09-07T12:00:00Z` or `2026-09-07T05:00:00-07:00`.
- `Digest`: `sha256:` followed by 64 lowercase hexadecimal characters.
- `Owner`: `{"actor":"<ID>","role":"<ID>"}` or `{"unresolved":"<decision-ID>"}`. Null or empty string is not an owner. Resolved owners must match an initiative role assignment. An unresolved owner never satisfies ownership readiness.
- `Review`: `unreviewed`, `human_confirmed`, `stale`, or `conflicted`. This is an authored claim, not approval evidence.
- `RecordRef`, `SourceRef`, and `Locator`: defined in references.md.

Each record contains this envelope plus its kind-specific fields:

| Field | Type / rule |
| --- | --- |
| `format_version` | Exactly `"1.0"` |
| `kind` | `initiative`, `contract`, `handoff`, `approval`, `evidence`, `knowledge` |
| `id` | ID; filename stem must match except the initiative uses `initiative.json` |
| `initiative_id` | ID; matches the containing initiative's ID |
| `owner` | Owner |
| `status` | `draft`, `proposed`, `approved`, `superseded`, `withdrawn`; authored lifecycle claim only |
| `provenance` | `{sources: SourceRef[], observed_at: Time, review_status: Review, note: Text}` |
| `illustrative` | Boolean; true for every synthetic example or fixture |

`provenance.sources` may be empty for a newly authored proposal if `note` states its human-supplied basis or unresolved origin; never synthesize a self-reference to satisfy provenance. External factual claims need source evidence for readiness. `status: approved` does not create effective approval. Historical superseded/withdrawn records remain available for audit, never silently satisfy current obligations.

Only these control files are loaded: `initiative.json`, `contracts/*.json`, `handoffs/*.json`, `approvals/*.json`, `evidence/*.json`, `knowledge/*.json`. Kind must match directory. Directories may be absent for a draft initiative. `snapshots/` stores referenced attachments, not automatically loaded records. Approval files are append-only by new ID; modifications to existing approval history require explicit owner correction and must remain visible in Git history.

## Initiative

Additional fields:

| Field | Type / rule |
| --- | --- |
| `purpose`, `scope` | Text each |
| `participants` | Array of `{repository_id: ID, locator: Locator, owner: Owner}`; repository IDs unique |
| `integration_owner`, `rollout_owner`, `rollback_owner` | Owner each |
| `policy` | Policy object below |
| `decisions` | Decision[] below; IDs unique |
| `required_contracts`, `required_handoffs` | ID[] referring to records of the corresponding kind |
| `checks` | Check[] below; check IDs unique in a separate namespace |
| `integration_checks` | ID[] referring to `checks` |

Policy has `role_assignments` (array of `{role: ID, actors: ID[]}`), `gates` (array of `{gate: Gate, required_roles: ID[]}`), and `disclosure` (object with `status: unresolved|resolved`, `decision_id: ID`). Gate is `scope`, `contract`, `requirements`, `design`, `tasks`, `knowledge`, `integration`, `release`, or `resolution`. Empty/absent effective role coverage is unresolved, not a zero-approver authorization. Role names and actors come from the adopter; there are no default governance roles. Gate entries and role entries are unique by name.

Decision: `{id: ID, question: Text, owner_role: ID, affected_ids: ID[], affected_gates: Gate[], status: unresolved|resolved, resolution: Text|null, evidence: SourceRef[]}`. An unresolved decision requires null resolution; a resolved decision requires nonempty resolution and human-supplied source evidence. `owner_role` names accountability for resolution even when no actor is assigned. References to missing decisions fail structural reference checks. Disclosure may be resolved only by a matching resolved decision; the validator does not decide disclosure policy.

Check: `{id: ID, owner: Owner, stage: local_complete|integration, procedure: Text, expected: Text, required_sources: SourceRef[], required_contracts: RecordRef[]}`. Procedures are inert descriptions, never commands to run during validation. Integration checks must have stage `integration`; handoff acceptance checks must have stage `local_complete`.

## Contract

| Field | Type / rule |
| --- | --- |
| `category` | `api`, `event`, `data`, `nfr` |
| `provider` | Registered repository ID |
| `consumers` | Registered repository ID[], unique |
| `definition_refs` | SourceRef[]; draft may be empty, approved readiness requires authoritative definition evidence |
| `display_version` | Text; no semantic compatibility inferred |
| `baseline_digest` | Digest or null for first introduction |
| `acceptance_checks` | Registered check ID[] |
| `compatibility` | `{assessment: unchanged|compatible|breaking|unknown, rationale: Text, evidence_ids: ID[], resolution_ids: ID[]}` |

Evidence and resolution IDs refer to evidence records. `baseline_digest` identifies the previous whole contract record, not the new record; previous content must be supplied as an authorized snapshot if comparison is required. Evidence references current definitions and the previous baseline, not the whole current contract that contains its ID. For first introduction, `unknown` is an explicit pending assessment; `unchanged` cannot stand in for reviewing a new interface. Compatibility acceptance and migration gates are specified separately in readiness rules.

## Handoff

| Field | Type / rule |
| --- | --- |
| `supplying_owner`, `receiving_owner` | Owner each |
| `repository_id` | Registered receiving repository ID |
| `scope` | Text describing bounded work |
| `obligations` | RecordRef[] targeting contracts |
| `local_artifacts` | `{requirements: SourceRef|null, design: SourceRef|null, tasks: SourceRef|null}`; null means not yet produced |
| `trace` | Trace[] below |
| `dependencies` | Dependency[] below |
| `acceptance_checks` | Registered local-complete check ID[] |
| `completion_evidence_ids`, `knowledge_ids` | ID[] targeting evidence and knowledge records respectively |

Trace: `{obligation: RecordRef, disposition: implemented|not_applicable|unresolved, requirements: Text[], design_elements: Text[], tasks: Text[], resolution_ids: ID[]}`. Local task IDs remain strings in their existing notation. Requirements/design/tasks arrays refer to local artifact identifiers; local source validation must verify existence. `not_applicable` needs matching owner-reviewed resolution evidence, not a free pass. `unresolved` cannot satisfy the affected gate. One trace entry per obligation identity; no silently omitted obligations.

Dependency: `{id: ID, consumer_stage: planning|execution|local_complete, producer_id: ID, required_stage: contract_approved|planning|execution|local_complete|integration|release, obligations: RecordRef[], evidence_ids: ID[]}`. Dependency IDs are unique within a handoff. The producer must be a kind supporting the required stage: contract for `contract_approved`, handoff for its three stages, initiative for `integration`/`release`. An edge referencing an existing but wrong-kind producer is invalid. Internal stage ordering and cycles are evaluated by task 2's rules.

## Approval

| Field | Type / rule |
| --- | --- |
| `actor`, `role` | Human-supplied ID each; match configured role assignment for an effective decision |
| `gate` | Gate |
| `decision` | `approved`, `rejected`, `revoked` |
| `timestamp` | Time |
| `target` | ApprovalTarget defined in references.md |
| `policy_digest` | Digest of exact policy projection defined in references.md |
| `supersedes` | Optional approval ID; same initiative, actor, role, gate and target identity |

An approval record's envelope status should be `proposed` until its recording is confirmed; `approved` means the record's capture was confirmed, not that its `decision` necessarily approves its target. Rejected/revoked decisions can therefore be faithfully recorded with envelope status `approved`. Do not create a decision record when the actor's decision is unknown; use an initiative decision instead. No validator authenticates the actor, grants authority, or auto-resolves conflicting effective decisions. Supersession must be acyclic; editing timestamps does not resolve conflicts.

## Evidence

| Field | Type / rule |
| --- | --- |
| `check_id` | Registered check ID, or null for compatibility/resolution/publication evidence |
| `purpose` | `verification`, `compatibility`, `resolution`, `publication` |
| `outcome` | `passed`, `failed`, `not_run` |
| `procedure` | Text, inert |
| `timestamp` | Time |
| `source_refs` | SourceRef[] for tested/reviewed content |
| `contract_refs` | RecordRef[] for contracts tested; see no-cycle rule below |
| `baseline_digests` | Digest[] for prior contract content when comparing versions |
| `attachments` | SourceRef[] for check output or owner review evidence |

Verification requires a non-null `check_id`; other purposes require null. Passing verification requires attachments and exact match to the check's declared source/contract baseline; a command string alone proves nothing. `not_run` may have empty attachments. Compatibility or resolution evidence embedded by ID in a contract has empty `contract_refs` for that same current contract and instead pins its `definition_refs` and previous `baseline_digest` in `source_refs`/`baseline_digests`. Verification evidence outside the contract can reference the complete approved contract normally.

Evidence owner and `provenance.review_status` carry accountability and review state; neither is an approval. An owner-approved resolution requires a separate effective resolution approval of that evidence record. Illustrative flags apply to all records, not just evidence, so fixtures cannot hide simulated authority in approval files.

## Knowledge

| Field | Type / rule |
| --- | --- |
| `source_refs` | SourceRef[]; individual digests serve as source fingerprints |
| `contract_refs` | RecordRef[] |
| `affected_participants` | Registered repository ID[] |
| `freshness` | `current`, `stale`, `conflicted`, `unresolved` |
| `stale_after` | Time or null when no time-based expiry is supplied |
| `okf_refs` | SourceRef[] to local knowledge concepts |
| `publication` | `{disposition: not_required|pending|published, evidence_ids: ID[], reason: Text}` |

Knowledge review uses the common provenance review field. `published` requires publication evidence; `pending` never means synchronized. `not_required` must cite the adopted decision in its reason and is checked against actual required obligations. Publication evidence pins the exported source payload/attachment, not this knowledge record containing its ID. Private source and OKF content need not be copied centrally; missing access is explicit unresolved evidence, not automatic currency.

## Illustrative draft and approval examples

These examples illustrate record shapes, not deployable policy. They carry no production authority. This complete draft initiative has no participants and deliberately unresolved disclosure/ownership; structure can be valid but readiness is blocked.

```json
{
  "format_version": "1.0",
  "kind": "initiative",
  "id": "demo",
  "initiative_id": "demo",
  "owner": {"unresolved": "assign-owners"},
  "status": "draft",
  "provenance": {"sources": [], "observed_at": "2026-09-07T12:00:00Z", "review_status": "unreviewed", "note": "Synthetic draft for format explanation only."},
  "illustrative": true,
  "purpose": "Illustrate coordinated delivery",
  "scope": "Synthetic initiative; no real repositories",
  "participants": [],
  "integration_owner": {"unresolved": "assign-owners"},
  "rollout_owner": {"unresolved": "assign-owners"},
  "rollback_owner": {"unresolved": "assign-owners"},
  "policy": {"role_assignments": [], "gates": [], "disclosure": {"status": "unresolved", "decision_id": "assign-owners"}},
  "decisions": [{"id": "assign-owners", "question": "Who owns and may share this initiative?", "owner_role": "initiative-owner", "affected_ids": ["demo"], "affected_gates": ["scope"], "status": "unresolved", "resolution": null, "evidence": []}],
  "required_contracts": [],
  "required_handoffs": [],
  "checks": [],
  "integration_checks": []
}
```

The following complete approval-shaped record demonstrates a recorded approved decision. Repeated hex digits are syntactically valid illustrative digests, not verified hashes: it MUST NOT pass reference/readiness checks as presented. A working example must replace them with computed target/policy digests, include the target and adopter-supplied role assignments, and retain `illustrative: true`. Task 16 provides executable synthetic snapshots.

```json
{
  "format_version": "1.0",
  "kind": "approval",
  "id": "demo-approval",
  "initiative_id": "demo",
  "owner": {"actor": "sample-reviewer", "role": "contract-owner"},
  "status": "approved",
  "provenance": {"sources": [], "observed_at": "2026-09-07T12:00:00Z", "review_status": "human_confirmed", "note": "Simulated decision, not actual human approval."},
  "illustrative": true,
  "actor": "sample-reviewer",
  "role": "contract-owner",
  "gate": "contract",
  "decision": "approved",
  "timestamp": "2026-09-07T12:00:00Z",
  "target": {"initiative_id": "demo", "record_id": "catalog-api", "type": "record", "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
  "policy_digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
}
```

For any proposed contract/handoff/knowledge record, changing envelope status to approved is insufficient: finalize its content, compute its digest, then record the required real decision separately. Evidence of approval capture must be human supplied; these simulated values must never be promoted into adopter templates.

## Diagnostics and field review

`VERSION_UNSUPPORTED` covers unsupported `format_version`; `FORMAT_INVALID` covers missing/unknown fields, types, duplicate keys, invalid enums/times/digests and wrong-kind relationships; `ID_DUPLICATE` covers record IDs; `REFERENCE_UNRESOLVED` covers missing targets; `OWNER_UNRESOLVED` and `POLICY_UNRESOLVED` express readiness gaps for explicit valid unresolved decisions. Each diagnostic names the file, record ID and field, never its potentially sensitive value. Actual CLI exit mapping is task 2's responsibility.

Task 1 field review against DESIGN.md Data Models: the envelope supplies version, identity, owner, status and provenance; Initiative supplies participant/role/policy/check/rollout ownership; Contract supplies definitions, consumers, versions and change evidence; Handoff supplies local trace, stage dependencies and completion references; Approval supplies actor, scope, time, policy/target identity and supersession; Evidence supplies tested revisions, commands, results and attachments; Knowledge supplies source fingerprints, contract/OKF links, freshness/review and publication. Participation, repo map and hashing details are in references.md. No seventh record kind is introduced: ownership and repository registrations are fields of Initiative, as in the approved design.

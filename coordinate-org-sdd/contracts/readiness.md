# Readiness and dependency gates — format 1.0

Normative companion to [records.md](records.md), [references.md](references.md), and [cli.md](cli.md). Implements ORG-CORE-004/005, ORG-CON-002/003/004/005/006 and ORG-VAL-001/002. Readiness establishes recorded prerequisites at an explicitly evaluated baseline, never actor authentication, repository permission, or permission to dispatch or release.

## Structure, evidence and scope

Parse every control record before evaluating a selected scope. Wrong fields/types/kinds, unsupported versions, duplicate identities, wrong-kind or dangling record links, unsafe paths, and impossible supersession/hash cycles are structural errors. No actionable readiness may be derived from a structurally corrupt initiative. A missing external source, mismatched digest, unmet stage, unresolved owner/policy, or absent approval is a readiness blocker, not malformed JSON. Valid drafts therefore pass structure while remaining blocked.

For each gate, evaluate only its dependency closure after global structural integrity checks. Report independent nodes separately; a blocked sibling does not become an implicit prerequisite. Each blocker names the file, record ID, field, code, affected node(s), and an actionable resolution without quoting sensitive values. Missing source access is `REFERENCE_UNRESOLVED`; known unequal content is `DIGEST_MISMATCH`. Neither network access nor a newer remote baseline may be inferred.

An active record has status other than `superseded` or `withdrawn`. Status alone never satisfies a gate. All required external sources and pinned RecordRefs in the evaluated closure must resolve under references.md. Sources in provenance are checked as well as domain references. Required records with `illustrative: true` block production readiness with `ILLUSTRATIVE_ONLY`; explicit example mode labels every result illustrative, including mixed fixtures.

## Effective approvals

For a target and gate:

1. Resolve its accountable owners and relevant policy decisions. A resolved owner must match a configured role assignment. Missing assignments yield `OWNER_UNRESOLVED`; missing/empty required gate roles, unresolved applicable decisions, or unresolved disclosure for sharing yield `POLICY_UNRESOLVED`. Do not impose example role names or infer authority from repository access.
2. Compute the exact target and policy digests using references.md. Source approvals match the handoff's particular local artifact SourceRef. Target record approvals hash the whole record. Release approvals hash the specified release projection. No target or policy digest includes approvals themselves.
3. Build supersession chains by explicit `supersedes`, never time order. A successor must have the same initiative, actor, role, gate, target type and target identity; the target digest may differ to record a new revision. Cycles, missing predecessors and identity-changing links are invalid (`FORMAT_INVALID` or `REFERENCE_UNRESOLVED`). Only confirmed, human-reviewed captured successors can replace a prior effective decision; an unconfirmed draft cannot suppress a rejection. Superseded historical records do not grant current approval.
4. Consider the unsuperseded confirmed records: envelope status `approved`, provenance review `human_confirmed`, supplied actor assigned to its role. Require matching target digest, policy digest, and current transitive prerequisite baseline. Stale records yield `APPROVAL_STALE` and do not cover a role. Unconfirmed records yield `APPROVAL_MISSING` where coverage is needed. This is record consistency, not proof of human identity.
5. Every configured required role needs an effective approving decision. Only roles configured for this gate count as effective gate decisions; assignment to another role does not grant authority here. Contradictory unsuperseded current decisions for the same role/target/gate yield `APPROVAL_CONFLICT`; multiple agreeing decisions need not conflict. An effective rejection or revocation blocks with `APPROVAL_REJECTED` or `APPROVAL_REVOKED` even if another actor approves. Actor-specific supersession does not erase another actor's decision; owner resolution must preserve each decision's history. Stale historical approvals are reported separately and cannot satisfy role coverage or veto valid current coverage. Required approval-provenance sources must resolve before acceptance or supersession.

Changing a policy or dependency does not rewrite old approval records. The report identifies invalidated approvals and gates requiring review. An old approval's unchanged target bytes do not conceal an altered ID-linked prerequisite. Effective approval requires both content identity and current prerequisite validity.

Prerequisite validity is stage-scoped, not a demand that every linked future stage has completed. Scope approval verifies initiative scope/policy/ownership content and structural links, not handoff completion. Contract review verifies definitions and compatibility evidence, not implementation checks. Local source approvals bind their artifact and upstream approved obligations, not future completion or integration evidence. ID links to future records do not introduce approval edges or self-referential hashes. Adding future result records does not alter an existing target digest; editing the target itself still legitimately requires renewed approval.

## Stage graph

Nodes are `(record ID, stage)`. Contract nodes support `contract_approved`; handoffs support `planning`, `execution`, `local_complete`; the initiative supports `integration`, `release`. Graph arrows point from prerequisite to dependent. An authored dependency adds `(producer_id, required_stage) -> (containing handoff, consumer_stage)`, retaining its pinned obligations and evidence IDs.

Intrinsic edges are:

- Each handoff: `planning -> execution -> local_complete`.
- Each obligation contract's `contract_approved -> handoff planning`.
- Each initiative-required handoff's `local_complete -> initiative integration`.
- Each initiative-required contract's `contract_approved -> initiative integration`.
- Initiative `integration -> release`.

Include intrinsic and authored edges in cycle detection and topological traversal. A strongly connected component with multiple nodes or a self-edge yields `DEPENDENCY_CYCLE`; its dependent closure is blocked. Deterministically list involved stage/record IDs. A missing producer is `REFERENCE_UNRESOLVED`; wrong-kind stage is `FORMAT_INVALID`. An existing but unsatisfied producer yields `DEPENDENCY_UNMET`; conflicting pinned obligations yield `DIGEST_MISMATCH`. All edge evidence must satisfy the evidence predicate below. Contract approval never substitutes for implementation completion. No extra edge from provider implementation to consumer planning is inferred.

## Gate predicates

All predicates require structurally valid input and the relevant active, nonillustrative (unless explicitly in example mode), resolved baseline. Conditions below are cumulative; list every actionable failure without claiming missing decisions were resolved.

| Predicate | Required inputs and conditions | Additional failure codes |
| --- | --- | --- |
| Scope agreed | Initiative owner and participating owners resolved; relevant decisions/disclosure resolved; effective `scope` approval of initiative | `OWNER_UNRESOLVED`, `POLICY_UNRESOLVED`, approval codes |
| Contract approved | Scope agreed; contract/provider/consumer owners resolved; nonempty verified definition refs; effective `contract` approval; compatibility predicate passes | `CONTRACT_UNRESOLVED`, `COMPATIBILITY_UNRESOLVED`, approval codes |
| Planning ready | Scope agreed; handoff and supplying/receiving owners resolved; all obligation contracts approved; incoming planning edges satisfied | `DEPENDENCY_UNMET`, `OWNER_UNRESOLVED` |
| Execution ready | Planning ready; incoming execution edges; all three local artifact refs present, resolved and effectively approved at gates `requirements`, `design`, `tasks`; complete trace coverage for every obligation | `LOCAL_APPROVAL_MISSING`, `TRACE_UNRESOLVED`, `DEPENDENCY_UNMET` |
| Locally complete | Execution ready; incoming local-complete edges; each handoff acceptance check has selected current passing completion evidence; all required knowledge is current and reviewed | `EVIDENCE_MISSING`, `EVIDENCE_FAILED`, `EVIDENCE_STALE`, `KNOWLEDGE_UNRESOLVED` |
| Handoff current | Locally complete plus required outgoing knowledge publication satisfied | `PUBLICATION_PENDING`, `EVIDENCE_MISSING` |
| Integration verified | Every required contract approved; every required handoff locally complete and current; integration/check owners resolved; all required integration checks pass at exact declared baseline; effective `integration` approvals of their evidence; rollout/rollback owners resolved | Evidence/approval codes, `OWNER_UNRESOLVED`, `PUBLICATION_PENDING` |
| Release approved | Integration verified; exact release-scope projection resolves; effective `release` approval of that projection under current policy | Approval codes, `EVIDENCE_CONFLICT` |

Local artifact approval checking augments, never replaces, each skill's existing frontmatter, explicit user gate and task-plan validation. The validator cannot infer local artifact approval from organization scope approval. Before local requirements approval, inspect handoff obligations and unresolved trace; do not require completed implementation trace just to begin drafting. For execution, `implemented` trace entries identify existing local requirement/design/task IDs; `not_applicable` entries need matching current resolution evidence and effective `resolution` approval; `unresolved` or omitted entries block the affected work. A changed local artifact must be reapproved under its existing local lifecycle.

Completion does not require future integration success. `handoff_current` is a distinct report condition, not another stored stage. Thus a pending export can leave local implementation verified while integration/release or an organizational currency claim remains blocked. Empty checks do not invent evidence obligations, but unresolved scope/policy cannot use empty arrays as implicit authorization to omit them. Required contracts' acceptance checks join the integration check closure at their declared stage: local-complete checks need selected local completion evidence, and integration checks need integration evidence/approval. They do not gate initial contract approval. A non-applicable trace resolution pins the current obligation RecordRef and its definition SourceRefs, so an unrelated resolution cannot waive that obligation.

## Evidence, compatibility and knowledge

For a check, selected evidence must have purpose `verification`, matching check ID, resolved owner, outcome `passed`, provenance review `human_confirmed`, nonempty resolved attachments, and exact equality of tested source and contract identity sets to the check's declared baseline. A nonempty inert procedure describes the check but is never run. Missing evidence yields `EVIDENCE_MISSING`; `failed`/`not_run` yields `EVIDENCE_FAILED`; mismatched or inaccessible baseline yields `EVIDENCE_STALE` plus the underlying reference diagnostic. Competing nonidentical effective integration results yield `EVIDENCE_CONFLICT`; timestamps never select a winner. Preserve resolved prior results as historical `superseded`/`withdrawn` records. Handoff completion uses its explicit completion evidence links.

Contract compatibility uses definition bytes and pinned previous baseline, not `display_version`. A first introduction requires current owner review, authoritative definitions and assessment evidence; `unchanged` with null baseline cannot bypass that review. For a changed contract, require prior baseline attachment when comparison is asserted and current compatibility evidence with purpose `compatibility`, passed outcome, reviewed attachments, exact current definition SourceRefs and previous digest in `baseline_digests`. `unchanged` still requires evidence demonstrating the relevant obligation did not change. `compatible` requires supporting evidence, not only an assertion. `breaking` and `unknown` additionally require current passed resolution/migration evidence, effective `resolution` approval, and recorded affected consumers before their affected gates pass. Missing assessment/resolution is `COMPATIBILITY_UNRESOLVED`. The validator checks identity and records, not semantic truth or adequacy of a migration strategy.

A first introduction with null baseline can pass as `compatible` with reviewed assessment evidence (empty previous-baseline list) and contract approval, or as `unknown` with explicit approved resolution. It requires no nonexistent previous contract and no provider implementation result. This is a bootstrap path, not inferred semantic compatibility.

Required knowledge must resolve its source/OKF/contract refs, declare `freshness: current`, have `human_confirmed` review, and effective `knowledge` approval where supplied policy requires that gate. `stale`, `conflicted`, or `unresolved` yields `KNOWLEDGE_UNRESOLVED`; missing required review is not inferred. Where `stale_after` is non-null, compare with the explicit evaluation instant; an omitted instant cannot prove unexpired knowledge. Review and approval never substitute for source digest verification.

Publication `pending` yields `PUBLICATION_PENDING` for currency. `published` requires linked passed reviewed `publication` evidence with resolved payload/attachment identities matching the outgoing metadata. `not_required` must name a resolved adopter decision applicable to that knowledge and must not conflict with required sharing obligations. This is a supplied disposition, never a default. The validator neither pushes Git nor treats report capture as publication.

## Impact and local-task eligibility

Starting from changed records, sources, policies or failed gates, follow reverse pinned references, linked evidence/check obligations and stage edges to report affected contracts, participants, handoffs, approvals and downstream stages. Revalidate ID-linked content independently even if a parent's bytes did not change. A changed contract invalidates an old handoff pin until deliberately reconciled; changing the pin then changes the handoff digest and release scope. Old pinned historical snapshots may remain verifiable, but they do not establish current remote state.

For candidate tasks supplied by the existing local wave resolver, intersect candidates with organizational eligibility only. Never add a task, skip to a later wave, mark TASKS.md, or authorize dispatch. An edge with obligations maps to tasks through handoff trace; a dependency without obligations applies to the whole consumer stage. Missing/ambiguous mapping conservatively blocks affected candidates with `TRACE_UNRESOLVED`. Unrelated same-wave candidates remain visible only when all their local gates and scoped organizational prerequisites pass. A handoff's overall execution stage can remain blocked while independently eligible candidates are reported. Global structural corruption admits no candidates.

## Four manual contract checks

These are reasoning checks of this contract, not executed runtime tests or real approvals.

1. **Stage cycle:** Handoff A execution requires B local completion; B planning requires A execution. Intrinsic B planning -> execution -> local_complete closes the cycle. Expected `DEPENDENCY_CYCLE` naming all involved stages; neither cycle nor descendants ready. Independent C planning remains reportable. A one-way contract-approved edge without these back edges would allow consumer planning before provider implementation.
2. **Conflicting approval:** Two confirmed current decisions for one required role and target approve and reject, with different timestamps and no supersession. Expected `APPROVAL_CONFLICT` and rejection blocker; newer timestamp does not win. Explicit valid actor-specific supersession can resolve that actor's history, not delete another actor's rejection.
3. **Inaccessible source:** A required source has valid shape and pinned digest but no authorized local mapping. Structure is valid; expected `REFERENCE_UNRESOLVED`, readiness exit 2 for its dependent scope. No network request. Adding an authorized matching snapshot establishes only the stated historical baseline, not remote HEAD currency.
4. **Changed contract:** Current contract definitions change from baseline d1 to d2 while the handoff/approval still pin d1. Expected `DIGEST_MISMATCH`, `APPROVAL_STALE` for affected approval closure and blocked dependent execution/integration/release. Updating only `display_version` cannot resolve compatibility. Matching reviewed assessment, approved migration for breaking/unknown changes, revised handoff pins and affected approvals are required. Unrelated participants remain distinguishable.

## Contract review checkpoint

These predicates preserve DESIGN.md's staged planning, separate completion states, authority boundaries and read-only validation. Root reviewed two interface details: retain the release projection from references.md and independently enforce transitive compatibility/resolution validity; do not silently add approval/evidence records to that digest projection. The explicit CLI evaluation instant and supplied-wave candidate flags concretize interfaces not spelled out in DESIGN.md and introduce no new autonomous actions or policy defaults. Bootstrap review confirms first-contract review precedes implementation and scope/local approval checks do not depend on future completion evidence.

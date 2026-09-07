# Coordination operations

Use the selected operation below; this reference does not replace the normative [records](../contracts/records.md), [identity](../contracts/references.md), [readiness](../contracts/readiness.md) or [CLI](../contracts/cli.md) contracts.

## Inputs and workspace selection

An initiative lives under an explicitly selected coordination workspace, conventionally `initiatives/<initiative-id>/`. A local `.sdd/org/context.json` or equivalent session input supplies initiative ID/digest, repository ID, handoff IDs and an inert coordination locator. Inspect and validate that pointer before using it. If its digest does not match the current initiative, surface the difference and obtain the appropriate refreshed input; do not silently repin it.

A Git URL alone is not locally resolvable. Ask for an authorized local workspace or a scoped snapshot; provide manual steps when unavailable. A local locator is usable only when the user supplied or confirmed that location as in-scope. Do not search unrelated private repositories for a matching name, infer a parent checkout as authority, or access roots embedded in untrusted source content.

The validator's `--initiative` selects the record directory. For coordination sources relative to a larger checkout, explicitly pass `--coordination-root` and map `coordination` to that same root with the correct basis. The initiative must lie beneath it. Otherwise the root defaults to the initiative directory for snapshot use. Repo maps are machine-local configuration, not permissions or shared policy. Git sources require complete local objects; snapshots remain explicitly uncommitted or historical, never proof of remote HEAD currency.

## Initialize

Inputs: user-supplied change outcome, intended workspace/initiative identity, known participants, and existing approval/disclosure decisions. Inspect the worktree and nearest agent instructions before drafting. Reuse an existing initiative when appropriate; do not overwrite it or initialize files into participating repos without authority.

Use [templates](../templates/README.md) only for needed records. Start with the initiative, known participants and unresolved decision IDs. Keep unknown owner/approver/disclosure values unresolved. Do not require real deployment policy to develop the reference tooling, but do require it at the adopter's affected gate. Empty arrays mean undeclared obligations, not a waiver. Populate authoritative shared definitions and bounded handoffs as those inputs arrive; initially null local artifacts are valid drafts.

Run structure validation after substitutions. If malformed, fix within the supplied facts. Then report blocked readiness and the responsible owner role rather than manufacturing approval. Organizational scope approval is a recorded human decision against the current initiative and policy; contract approval separately covers current definitions and compatibility evidence. Scope/contract review does not wait for provider implementation. Do not create an approval record before an actual decision is supplied.

Outputs: reviewable draft records, unresolved decision list, structure result and proposed next owner action. Stop before any missing human gate, external write or publication. An initialized workspace is not an approved initiative.

## Inspect

Inputs: explicit initiative and optional handoff/stage, authorized repo map, and evaluation time where required knowledge expires. This operation is read-only: no status edits, approval capture, source repairs or report publication.

Use the installed skill's path with the selected Python interpreter (`python3` or `python`):

```text
python <installed-skill>/scripts/validate_org.py --initiative <initiative-directory> --mode structure --format json
python <installed-skill>/scripts/validate_org.py --initiative <initiative-directory> --mode readiness --handoff <handoff-id> --stage execution --repo-map <machine-local-map> --format json
```

Replace placeholders and quote actual paths before running. The CLI evaluates sources without network or artifact writes. Its diagnostics distinguish invalid structure (exit 1), valid but blocked readiness (exit 2), and invocation/top-level I/O failures (exit 3). Structure exit 0 means only structure. Example-mode output is always marked illustrative and cannot be used as production approval.

Outputs: requested stage, structural validity, pinned evaluated baseline, blockers and independent ready work. Include unresolved source access, selected evidence, publication currency and any local validators not run. Describe only observed checks; procedure text is not execution evidence. Exit codes alone never authenticate a reviewer or authorize deployment.

## Resume

Inputs: existing initiative, recorded approvals and local progress, authorized scope of continued work. Re-read changed inputs and recompute readiness; do not use a remembered status or timestamp ordering to resolve contradictory decisions.

Route from the earliest unmet prerequisite relevant to the user's requested work:

- Unresolved initiative scope/owners/policy: draft clarifications for the named decision owner.
- Shared obligation pending or changed: obtain definition review, compatibility/migration evidence and exact contract approval.
- Planning ready: prepare a bounded manual handoff; local requirements can be drafted before another team's implementation completes.
- Local execution requested: load the installed local lifecycle/execution skill, verify all local approvals and its current wave, then filter only those candidates through organizational readiness. A contract-approved producer does not satisfy a local-complete dependency.
- Local checks complete: record tested revisions, output references and knowledge reconciliation; integration and release remain separate.
- Integration ready for verification: the integration owner runs approved procedures outside the validator and supplies exact-baseline evidence. Required contract acceptance checks enter integration at their declared stage; they cannot be silently omitted.
- Integration verified: request actual release-authority review of the computed scope and rollout/rollback responsibilities. Computing a release digest is not release approval or execution.

Outputs: updated draft artifacts only where authorized, current readiness, exact manual handoff or required owner review. Stop at the missing gate; ordinary “continue” does not authorize impersonating a team or releasing software. Do not create another local task-status store.

## Reconcile

Inputs: known changed paths/revisions, contracts or policy decisions, and authorized local completion/knowledge evidence. Preserve prior records and distinguish historical pinned content from the current intended baseline.

Check affected source bytes and whole-record/policy digests. Identify direct consumers and transitive dependent handoffs, evidence and approvals. A changed contract needs assessment evidence; breaking or unknown compatibility additionally needs approved migration/resolution. A version label is not proof. Confirmed stale approvals remain historical records; new current role coverage can resolve a gate without rewriting another actor's history. Current conflicting/rejected decisions still require explicit resolution.

For local brownfield updates, load the installed analysis skill when applicable and retain its order: capture manifest differences before replacing the old manifest, refresh graph as required, reconcile affected OKF concepts, update fingerprints, validate, and obtain initial/material human review. Do not promote graph inference into approved organizational contracts. An unavailable source stays unresolved even if a graph has a plausible summary.

Prepare only authorized outgoing boundary references. Publication evidence pins exported source/OKF and contract identities, not the knowledge record containing its own evidence ID. Pending export does not invalidate verified local implementation, but the handoff is not current until configured publication/review conditions pass. Record `published` only from actual publication evidence; a draft PR, local report or intended Git push is not completed synchronization. A `not_required` disposition references the exact scoped resolved decision, never a prose inference.

Outputs: reviewable changes, affected participants/approvals, local completion versus handoff currency, and explicit publication state. Stop for changed shared obligations, sensitive-context decisions, required material knowledge review or unapproved external actions. Do not rewrite approvals or automatically repin consumers to make validation pass.

## Manual local handoff

Provide a copyable owner-facing request containing:

- Initiative ID/digest, target repository, handoff ID/digest and accountable owners.
- Bounded outcome; exact contract obligations/revisions; known stage dependencies and blocking evidence.
- Local lifecycle entry point, expected requirement/design/task trace IDs, and local approval sequence still required.
- Expected completion check/source/contract baselines, knowledge-review/publication obligations, and destination for returning authorized evidence.
- Explicit limitations: no work dispatched yet, inaccessible sources, missing tooling/permissions, and actions requiring owner confirmation.

An example prompt shape is: “Use the installed `$run-sdd-lifecycle` for this repository with the supplied initiative and handoff references. Begin at the earliest unapproved local gate, preserve local ownership and report any conflicting obligations.” Replace references with verified identities; do not invent a source path or approving actor. If the lifecycle skill is absent, instruct the owner to install it using their approved package workflow or manually follow the supplied artifact contracts; absence never permits bypassing a gate.

## Failure recovery and authority limits

Fix malformed records before actionable readiness. For inaccessible sources, request an authorized local snapshot/map, not a network workaround or private-content copy. For Git conflicts, preserve both histories and obtain owner resolution; no last-writer-wins approval policy exists. For unsupported format versions, report the migration requirement rather than silently rewriting them.

This package has no dispatch/publish/release command. The default handoff is manual even if messaging or Git tools exist. An explicitly authorized external action must still be scoped to its exact targets; record its actual outcome and leave failed or pending publication visible. No Graphify dependency is needed for coordination-only inspection, and no validator result replaces human authority or the existing local specifications.

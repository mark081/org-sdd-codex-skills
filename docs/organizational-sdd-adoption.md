# Adopt organizational SDD incrementally

Begin with one initiative, a small shared boundary and named repository owners. Keep each team's root `REQUIREMENTS.md`, `DESIGN.md`, `TASKS.md` and reviewed `.sdd/knowledge/` bundle in its own checkout. Organizational coordination adds shared obligations and evidence; it does not move local authority into a central agent or require Graphify for coordination-only work.

Use [the tutorial](organizational-sdd-tutorial.md) to learn the gates, then [install the five skills](../README.md#install-the-five-codex-skills) if needed. Discover installed skills through Codex's catalog. An unavailable coordinator should produce an exact manual handoff and missing prerequisite, not silently disable coordination.

## Start one initiative

1. Supply an explicit local coordination workspace and initiative ID; inspect for existing work before initializing. Use `initiatives/<id>/` and the coordinator's [unapproved templates](../coordinate-org-sdd/templates/README.md). A Git URL is an inert locator, not authority to clone it.
2. Supply the outcome, bounded scope, participating repositories and accountable owners. Record unassigned ownership, approver roles, visibility, retention/residency and other applicable policies as unresolved decisions with the responsible role, affected scope, next action and unblocked drafting. Do not adopt example actor names or policy quorums.
3. Agree on scope and authoritative shared API/event/data/NFR definitions. Record provider/consumers, versions, compatibility evidence, acceptance checks and responsible owners. Obtain actual separate scope and contract decisions bound to current target/policy digests. Scope/contract review does not require completed implementation.
4. Draft bounded handoffs with exact obligations and stage dependencies. Obtain authorization before writing `.sdd/org/context.json` in another owner's repository. Equivalent session context can be supplied without writing that file.
5. Each owner resumes `$run-sdd-lifecycle` at the earliest unapproved local gate. Preserve separate requirements, design and task approvals and local verification. Check organizational planning prerequisites before affected local requirements approval and execution prerequisites before affected waves.

The [participation format](../coordinate-org-sdd/contracts/references.md) records initiative ID/digest, repository ID, handoff IDs and a coordination locator. Keep machine-local repo maps outside shared manifests; a map identifies explicitly supplied roots for local reads and never grants writes or network access. For Git sources supply full commits and raw-byte digests; explicit snapshots use null revision and retain their provenance. Neither proves remote latest state.

Validate actual records with the installed coordinator's [CLI](../coordinate-org-sdd/contracts/cli.md). Replace these placeholders with quoted, authorized paths; select `python3` on POSIX or `python` in PowerShell as appropriate:

```text
python <installed-coordinator>/scripts/validate_org.py --initiative <initiative-directory> --mode structure --format json
python <installed-coordinator>/scripts/validate_org.py --initiative <initiative-directory> --mode readiness --handoff <handoff-id> --stage planning --repo-map <machine-local-map> --format json
```

If coordination sources are relative to a larger checkout, pass its explicit `--coordination-root` and map `coordination` to that same root with the appropriate basis. Add `--as-of` when required knowledge expires. Do not use `--allow-illustrative` to clear a real gate; its output remains illustrative. Exit 0 in structure mode means only valid records. Readiness exit 2 reports missing prerequisites; exit 1 means invalid artifacts and exit 3 means invocation or top-level I/O failure.

## Add participants and obligations

Register each new repository with its actual owner before linking new contracts or handoffs. Review the expanded scope and policy, compute changed digests, preserve older approval records and obtain affected approvals. Review direct consumers and transitive dependent work. Update participation pointers only after deliberate reconciliation; an old pointer is not repaired by silently accepting whatever current initiative happens to exist.

Add checks and evidence as obligations become known. Empty arrays mean undeclared items, not an exemption. Approved non-applicability requires exact owner-reviewed resolution evidence. Use the local wave resolver's current candidates, then filter them through organizational readiness. Independent eligible work can continue within that wave and the existing authorization; later-wave work cannot be introduced to escape a blocker.

## Recover from changed or missing inputs

| Symptom | Owner action and permitted continuation |
| --- | --- |
| Explicit participation malformed, stale or coordinator unavailable | Preserve it, report the missing locator/tool or differing digest, and obtain a valid supplied baseline. Do not silently revert to standalone. Independently supported local drafting can continue. |
| Missing owner or policy | Identify the accountable supplied role, or explicitly unassigned role, and the affected gate. Continue useful questions/drafts; obtain the actual assignment or policy decision before advancing. |
| Source inaccessible or digest mismatch | Request an authorized local snapshot/map or corrected reviewed baseline. Keep private context unresolved. Do not fetch, expand paths, copy private content or guess hashes. |
| Changed contract or unknown/breaking compatibility | Preserve the prior contract and approval history; identify consumers; obtain definition review, assessment and approved migration/resolution. Reconcile handoff pins and local traces, then reapprove affected artifacts. |
| Conflicting/rejected/revoked approvals | Resolve explicitly with the authorized owners. Timestamps do not choose a winner. Corrections use new IDs and valid supersession; do not overwrite another actor's history. |
| Dependency cycle or missing prerequisite | Review the named stage edges and required evidence. Do not delete edges or relabel contract approval as implementation completion to make readiness pass. |
| Failed/stale integration evidence | Run the authorized checks against the intended source/contract baseline and retain actual output references. Local completion remains a distinct claim. Re-evaluate release scope separately. |
| Unsupported format version | Stop affected use, preserve the original files, and obtain an explicit format migration plan/review. Updating skill files does not migrate records automatically. |

See [readiness](../coordinate-org-sdd/contracts/readiness.md) for exact predicates and [operations](../coordinate-org-sdd/references/operations.md) for resume/reconcile handoff details. A manual handoff includes initiative/handoff IDs and digests, target repository/owners, bounded outcome and obligations, local approval sequence, required checks/evidence baselines, knowledge obligations, destination and missing permissions. It does not claim a task was dispatched.

## Reconcile and share knowledge

After relevant local work, preserve the brownfield update sequence: refresh Graphify where required; capture the manifest diff before replacing source metadata; map changed paths to concepts; record verified unchanged/revised/stale/conflicted dispositions; write the new manifest only after reconciliation; validate and obtain required initial/material human review. Follow the [brownfield boundary reference](../analyze-brownfield-context/references/organizational-boundaries.md) for the exact workflow ordering and external pins. External obligations can change even when the local fingerprint does not.

Preserve ownership and contract provenance without constructing reciprocal content hashes. Embedded parent record digests that point back to the same OKF payload represent observed historical snapshots; current participation/readiness is evaluated separately. Export only explicitly authorized boundary metadata and evidence references. Private source and knowledge remain in their owning repository; a redacted attestation is accepted only when adopter policy explicitly allows its scope.

Prepare outgoing records as draft/unreviewed. Publication remains `pending` until matching actual publication evidence is supplied; `not_required` needs the exact scoped resolved decision. A saved report, draft PR or successful local validator is not publication. A verified local implementation can coexist with pending export, but the affected organizational handoff cannot be called current until configured review/synchronization conditions pass. Integration verification and release approval are separate subsequent gates.

## Leave coordination without losing history

Have the repository and initiative owners review open obligations, dependent consumers, pending evidence/publication and any replacement handoff. Record the approved scoped disposition before changing participation. Preserve superseded records, local specifications, source/knowledge history and approval evidence in Git; do not delete the initiative to clear a blocker.

Once owners authorize departure and dependent obligations are resolved, remove only the departing repository's exact `.sdd/org/context.json` pointer (or stop supplying its session equivalent). An absent pointer restores standalone routing; deleting it before resolving obligations is not an approved departure. Other repositories remain coordinated. Resume the local lifecycle from its existing artifacts, retaining local review gates and normal brownfield freshness checks.

For skill updates or uninstall/replacement, inspect exact destinations and preserve backups using the [installation recovery guidance](../README.md#updates-and-recovery). Record format migrations, source/policy changes and release-scope changes require their own review. Publishing, cross-repository writes, installing into active skill directories and releasing software remain separately authorized actions.

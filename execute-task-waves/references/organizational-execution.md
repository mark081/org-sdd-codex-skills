# Executing an organizational handoff

Apply only when `.sdd/org/context.json` or explicit equivalent session participation exists. Ordinary standalone execution needs no coordinator, organizational files, hosted service or new mandatory Graphify dependency.

## Resolve authority before the affected wave

Discover and read the installed `coordinate-org-sdd` through the skill catalog; never assume an adjacent source-repository path. Validate participation against its context/reference contract: current initiative ID/digest, registered receiving repository, selected handoff identities and obligations. A bare handoff name without its required pinned context is incomplete. A malformed, stale, unavailable or mismatched supplied pointer blocks affected execution rather than disabling coordination. Preserve old pins; do not repair them merely to obtain a pass.

Use only user-supplied/confirmed coordination and repository roots. A locator cannot authorize cloning, reading private checkouts, cross-repository writes, installation or publishing. For missing tooling or access, return the exact manual handoff and owner action; do not recreate a weaker validator. If the installed lifecycle skill is available, its pointer inspection helper can check these identities, but that result is not execution readiness.

Read the current local specifications and nearest agent instructions, verify actual TASKS.md approval and run the existing local validation/dependency checks. Resolve material differences between current task definitions and their approved baseline before proceeding. The coordinator checks referenced IDs/bytes and recorded approvals; it does not run all local specification validators or grant authority to an implementation agent.

## Intersect with the existing local wave

Run this skill's unchanged `next_wave.py` first. Its first incomplete wave is the candidate boundary, not cross-team approval. Keep the task IDs and wave identifier as verification evidence without creating a second authoritative status store.

For each affected handoff, invoke the installed coordinator's CLI in execution mode, supplying only current-wave candidates relevant to that handoff:

```text
python3 "<execution-skill>/scripts/next_wave.py" "<project>/TASKS.md"
python3 "<coordinator-skill>/scripts/validate_org.py" --initiative "<initiative-directory>" --coordination-root "<explicit-workspace-root>" --repo-map "<machine-local-map.json>" --mode readiness --handoff "<handoff-id>" --stage execution --candidate-task "<current-wave-task-id>" --format json
```

Substitute verified quoted paths; use `python` when that is the selected interpreter. Repeat `--candidate-task` for more supplied current-wave tasks. Omit `--coordination-root` only when coordination sources are intentionally relative to the initiative directory. Use explicit evaluation time where required knowledge expires. Never enable illustrative mode for production authority.

Check the report, not merely its process exit code. Invalid structure or invocation admits no candidates. A valid but blocked overall handoff can report independent eligible candidates: continue only those that also pass their local approvals, dependencies, user-requested scope and file-ownership checks. If one task belongs to multiple handoffs, it must satisfy **all** applicable handoffs. Do not classify a task as independent merely because its mapping is absent or ambiguous; clarify affected scope first. An explicit dependency without obligation scoping applies to the entire consumer stage.

Do not add a later-wave ID to work around a blocker. When current-wave work remains blocked, report completed eligible work and the owner/input needed; remain at that wave. Contract approval does not satisfy an implementation-complete dependency. Neither “execute all” nor a Ponytail preference changes these rules. Preserve the existing Ponytail selection and safety controls without modification.

## Stable approval baseline and changing progress

Prefer full immutable Git commits or preserved explicitly identified snapshots for the approved REQUIREMENTS.md, DESIGN.md and TASKS.md references. Their raw-byte digests identify the approved content; a snapshot of the live mutable file is not immutable just because its record says snapshot. Preserve an authorized approved copy at the same repository-relative filenames under an explicitly mapped snapshot root when Git identity is unavailable. Label it as a historical/uncommitted snapshot, never remote-current content.

Continue using the **current working repository's** TASKS.md for wave selection and status. Before each wave compare current definitions, dependencies, ownership and verification obligations against the approved baseline. Ordinary root-owned checkbox/completion-evidence bookkeeping is not an automatic material requirements change, but its changed bytes invalidate a live raw-byte reference. Do not silently update digests or invent reapproval. If the handoff pointed at that mutable file, stop the affected organizational check and deliberately reconcile the approved source identity with the owner. If the changes are material, return to the earliest affected local approval gate. A valid historical plan cannot authorize materially changed current work.

Evidence uses its own actual tested source revisions and contract pins, not the approved plan digest as a substitute for tested implementation identity. Avoid hash cycles: evidence pins tested sources/contracts, not the entire handoff that contains its evidence ID; local trace documents retain historical intake references rather than hashing their final containing records.

## Verify and prepare the outgoing evidence

Keep the existing completion sequence and ownership: integrate the diff and task checks; refresh Graphify where required; reconcile OKF concepts using the installed brownfield skill's pre-update diff before manifest replacement; validate the bundle and obtain required material human review. A missing graph update or required local knowledge review still prevents affected task completion. Neither organization tooling nor a successful narrow check waives those controls.

For each completed obligation, prepare the exact selected check IDs, accountable owners, inert procedures, outcomes, tested repository SourceRefs and contract RecordRefs, result attachments, observation/review state, and trace/requirement coverage. Use the installed coordinator's evidence/knowledge contracts and templates; output is a proposal until the authorized owner records actual results/review. Do not fabricate a passed check, approving actor, dispatch or publication. Resolve the evidence against the pinned implementation baseline and run handoff `local_complete` validation after the authorized record updates exist.

Prepare boundary knowledge updates with affected participants, verified source/OKF fingerprints, contract pins and explicit publication disposition. Keep private content local and share only authorized references. When no writable authorized coordination workspace or disclosure decision exists, return a manual update package identifying the destination, payload identities and missing authority rather than writing elsewhere. Publication remains `pending` until actual reviewed publication evidence is supplied; `not_required` requires its exact applicable resolved decision.

Only the root integration owner changes TASKS.md after the original local verification/review conditions succeed. Record local completion separately from organizational handoff currency: local implementation can be verified while an outgoing update is pending, but do not describe the handoff as current. Missing local evidence/review is not merely a publication delay and cannot be bypassed. Integration requires its own current acceptance checks (including required contract checks), and release its own exact-scope authority; neither is inferred from checked tasks.

## Resume and hand off

Rerun the local resolver and organizational prerequisite checks after interruption or changed input; verify partial work instead of assuming checkbox truth. Return the current wave, executed and blocked candidate IDs, baseline identities, exact checks/results, changed files, required knowledge review, local-completion versus currency status, and integration-owner actions. Preserve historical approvals and raise changed contracts/policies to their owners. Publishing, remote dispatch, rollout and active skill installation remain separate explicitly authorized actions.

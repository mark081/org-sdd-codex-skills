# Planning from an organizational handoff

Use this reference only for `.sdd/org/context.json` or explicit session-supplied participation. Local `REQUIREMENTS.md`, `DESIGN.md`, and `TASKS.md` remain authoritative in the project root. This skill drafts local specifications, not cross-repository edits, dispatch, or policy decisions.

## Resolve the input before the affected gate

1. Discover `coordinate-org-sdd` through the installed skill catalog and read its entrypoint, `contracts/references.md`, `contracts/records.md`, and applicable readiness/CLI guidance. Do not assume this source repository or a sibling installation exists. If unavailable, give the installation/manual handoff needed and pause affected work; do not recreate a weaker readiness check. Unrelated local drafting may continue within existing authority.
2. Validate the participation object against the coordinator's context contract. A supplied bare handoff still needs the same initiative, repository, locator, initiative digest, and handoff IDs for the session; do not silently infer missing values. Check the exact initiative ID/digest, participant repository, and ownership of every selected handoff. A missing pointer with no explicit handoff means standalone. A malformed, unreadable, mismatched, or unavailable supplied pointer means blocked coordinated work, not opt-out.
3. Have the user supply or confirm the in-scope coordination workspace and local repository map. Locators are data, not authority to fetch or access another checkout. Read only authorized sources. Do not copy private OKF/source material into shared artifacts as part of local planning.
4. Run the installed coordinator's read-only validator for structure, then planning for every selected handoff. Compare its evaluated initiative baseline with `initiative_digest`; compare the obligation pins with those already recorded locally and inspect any handoff changes since intake. Use the digest helper when preserving the intake handoff snapshot's canonical digest. A passing report describes only the supplied baseline, not remote latest state.

Commands below use explicit substituted paths; use `python` instead of `python3` when that is the selected interpreter. They work independently of this skill's standalone validators:

```text
python3 "<coordinate-skill>/scripts/validate_org.py" --initiative "<initiative-directory>" --mode structure --format json
python3 "<coordinate-skill>/scripts/validate_org.py" --initiative "<initiative-directory>" --coordination-root "<workspace-root>" --repo-map "<local-repo-map.json>" --mode readiness --handoff "<handoff-id>" --stage planning --format json
python3 "<coordinate-skill>/scripts/validate_org.py" --digest "<handoff-file.json>" --digest-kind record --format json
```

Exit 0 in structure mode says nothing about readiness. Readiness exit 2 requires resolving reported affected prerequisites; exits 1/3 require artifact/input correction. Never use illustrative opt-in for adopter approval. Surface stale approvals, conflicting contract revisions, changed policy, unavailable sources, and unresolved ownership to the accountable owners before advancing the affected gate. Do not delete edges, choose the newest conflicting approval, repin content, or manufacture approval to clear a diagnostic.

## Trace every obligation as the local artifacts develop

In each artifact's organizational traceability section, record the initiative ID, handoff ID, and each obligation's complete current RecordRef (`initiative_id`, `record_id`, `digest`). Preserve received initiative/handoff snapshot references and digests as clearly labeled historical intake baselines. Do not require a local document to embed the digest of the final handoff or initiative that in turn hashes that document through local artifact references or checks: that creates a content-hash cycle. Keep the current initiative digest in the separate participation pointer and reconcile it explicitly when authorized. Review subsequent initiative/handoff changes against the preserved intake snapshots; historical intake digests do not assert that final records remain unchanged or replace current obligation pins. Link authoritative definition SourceRefs including their revision or explicit snapshot basis and raw-byte digest. Preserve local requirement IDs and stable design element/property IDs; do not substitute organization IDs for the local scheme.

Use one row per selected handoff obligation, including obligations judged out of scope:

| Local artifact | Mapping reviewed before its approval |
| --- | --- |
| REQUIREMENTS.md | Exact obligation pin → local requirement IDs and acceptance/verification criteria; explicit local scope disposition |
| DESIGN.md | Same pin → approved requirement IDs → design element/property IDs and tests |
| TASKS.md | Same pin → requirement/design IDs → executable leaf task IDs, required readiness stage, verification/evidence and accountable owner |

At **each** gate, compare the complete handoff obligation set to the local section: no omitted or extra unexplained obligations, mismatched pins, nonexistent current-stage IDs, or unreviewed scope changes. Check actual requirement/design/task definitions, not just incidental ID mentions. Future-stage IDs remain explicitly pending until that artifact is authored; do not create downstream artifacts early to satisfy a check. Carry every unresolved item forward visibly with owner, affected gate, and needed decision.

Disposition meanings follow the handoff Trace contract:

- `implemented` means allocated to local implementation with the required mappings; it does not assert tasks are complete. Before task-plan handoff, all three mapping arrays must contain actual identifiers.
- `not_applicable` requires owner-reviewed resolution evidence and effective approval scoped to the exact obligation and its definition sources. Record its resolution IDs and explain the local exclusion. An agent's rationale, blank array, or local approval of an unrelated artifact is insufficient.
- `unresolved` preserves a scope question and blocks its affected gate. It must not become `not_applicable` merely to obtain validation success.

The planning CLI checks organizational planning prerequisites, **not** the completeness or meaning of an in-progress local trace section. The stage-specific coverage review above is still required before requirements/design/task approval. Full machine trace validation is available at execution readiness once all three local artifacts and their actual approvals are supplied; do not require future approvals as a condition for beginning requirements.

## Reconcile the approved local handoff

After each actual local approval, prepare the corresponding root-file SourceRef and source-target approval record for the authorized coordination owner. Record only the actor, scope, time, and decision actually supplied through the adopter process. If recording authority is absent, return a manual update package; do not claim it was published. Preserve earlier approvals rather than rewriting their target digests.

Use immutable Git commits or preserved, explicitly identified snapshots for approved local artifacts. Live snapshot bytes, including TASKS.md progress bookkeeping, can change and invalidate raw digests. Do not silently rehash/reapprove them to pass. Keep current local artifact validation and material-change approval rules in addition to pinned-baseline checks; a historical approved snapshot cannot authorize materially changed current work.

Before recommending execution, ensure the authorized handoff update carries complete `local_artifacts` and `trace` mappings, then run:

```text
python3 "<coordinate-skill>/scripts/validate_org.py" --initiative "<initiative-directory>" --coordination-root "<workspace-root>" --repo-map "<local-repo-map.json>" --mode readiness --handoff "<handoff-id>" --stage execution --format json
```

Run this skill's existing local specification and task-graph validators unchanged as well. Missing mappings, mismatched sources, or missing local approval records block organizational execution; a provider's implementation dependency may also still block it even after successful local task-plan approval. Report those separately and hand off to `$execute-task-waves` only within its authority/readiness checks. No planning result implies integration verification or release approval.

# Unapproved organizational starter templates

These are format-1.0 drafting aids, not approvals, owner assignments or deployable example policies. Every `<...>` string is a required substitution; the files are intentionally invalid until those values are supplied. Do not copy all files into an initiative automatically. Preserve existing files; select only the record being drafted and choose a new stable ID.

| Template | Destination after substitution |
| --- | --- |
| [initiative.json](initiative.json) | Explicit workspace `initiatives/<initiative-id>/initiative.json` |
| [contract.json](contract.json) | Initiative `contracts/<contract-id>.json` |
| [handoff.json](handoff.json) | Initiative `handoffs/<handoff-id>.json` |
| [approval.json](approval.json) | Initiative `approvals/<new-approval-record-id>.json`, only after an actual decision is supplied |
| [evidence.json](evidence.json) | Initiative `evidence/<evidence-id>.json` |
| [knowledge.json](knowledge.json) | Initiative `knowledge/<knowledge-id>.json` |
| [context.json](context.json) | Participating checkout `.sdd/org/context.json` |
| [repo-map.json](repo-map.json) | Explicit machine-local configuration outside shared manifests |

## Safe substitution and drafting

1. Supply stable IDs matching `[a-z][a-z0-9-]{0,63}`, nonempty scope text, and actual observation timestamps with seconds and timezone. Replace JSON string values structurally with an editor; preserve JSON escaping. Do not perform shell evaluation or environment/tilde expansion. Windows absolute roots need JSON-escaped backslashes, or use `/` separators in the root. Source paths always use portable relative `/` separators.
2. Keep status `draft`, review `unreviewed`, unresolved ownership decisions, unknown compatibility, unrun checks, and pending publication until the required facts and reviews exist. `illustrative: false` identifies an adopter draft; it does not make it approved. Synthetic walkthroughs must set `illustrative: true` on **every** record, including approval records, and remain isolated from production workspaces.
3. Register provider/consumer/receiving repositories in initiative participants before linking them. Supply each locator and owner explicitly. Owners may remain `{"unresolved":"<existing-decision-id>"}` while drafting. Role assignments, approver rules, disclosure, rollout and rollback responsibilities are adopter decisions; the templates deliberately provide no default actors or approval quorum.
4. Add required contract, handoff and check IDs to the initiative deliberately. Empty arrays mean no declared records yet, not permission to omit obligations. The evidence starter names a registered check and defaults to `not_run`; never change it to passed without current output. Check definitions, participants, trace entries, dependencies and source/reference objects use the exact shapes in [records.md](../contracts/records.md) and [references.md](../contracts/references.md).
5. A new contract starts with `baseline_digest: null`, meaning first introduction. For a change, supply the prior whole-record canonical digest and a verified snapshot of that prior contract. Replace `<api-event-data-or-nfr>` with one actual category. Obtain reviewed assessment evidence; `display_version` cannot establish compatibility.
6. Local artifact references belong to the receiving repository's root REQUIREMENTS.md, DESIGN.md and TASKS.md. Populate obligations and trace all of them before execution. For `not_applicable`, resolution evidence pins the current contract reference and definition sources and requires actual owner approval. Do not use an empty trace as an exemption.
7. Knowledge keeps private source and OKF content local; export only authorized boundary references. `stale_after: null` means no time-based expiry has been supplied, not permanent freshness. Publication remains pending until satisfied. To record an adopter-approved `not_required` disposition, put the exact applicable resolved decision ID in `publication.reason`; that decision must cover the knowledge gate and this knowledge record or its initiative. A passing validator is not that decision.

## Approval template is deliberately uninstantiated

Do not create an approval record for a person whose decision is unknown. In that situation keep an unresolved initiative decision instead. The approval template has no default actor, role, gate, decision, decision time or digest. Replace those fields only from the actual supplied decision and computed current content, and preserve source evidence of its capture. `status: proposed` and `review_status: unreviewed` remain until capture is confirmed; merely recording `decision: approved` does not produce an effective approval.

Use a new approval ID, never overwrite another actor's history. `supersedes` is an optional field only when an actual correction explicitly supersedes that actor's same role/gate/target decision. Timestamps do not resolve contradictions. A policy-approved new owner can approve current content without impersonating or rewriting a prior actor's historical record.

The starter target is a record approval. For a requirements/design/tasks decision use `type: "source"`, handoff record ID, the exact SourceRef under an added `target.source`, and its raw-byte digest. For release use `type: "release_scope"`, initiative record ID and the derived release digest. Do not add `source` for other target types. Contract, knowledge, integration-evidence and resolution-evidence approval targets use `type: "record"`. All approval records bind the current policy digest. Details are normative in [readiness.md](../contracts/readiness.md).

## Local validation and identity commands

From any directory, substitute actual quoted paths. POSIX shells commonly use `python3`; PowerShell may use `python` for the selected interpreter. These commands read only; they never run artifact procedures, publish, dispatch or sign approvals.

```text
python <installed-skill>/scripts/validate_org.py --initiative <initiative-directory> --mode structure
python <installed-skill>/scripts/validate_org.py --digest <record-file> --digest-kind record
python <installed-skill>/scripts/validate_org.py --digest <source-file> --digest-kind source
python <installed-skill>/scripts/validate_org.py --digest <initiative.json> --digest-kind policy
python <installed-skill>/scripts/validate_org.py --initiative <initiative-directory> --mode readiness --repo-map <machine-local-map>
```

Instantiation should first produce a structurally valid **blocked draft**. Structure exit 0 is not readiness. Readiness exit 2 identifies missing owners, scope, approvals or evidence. Unsupported versions and malformed records fail rather than migrating silently.

For a nested initiative whose `coordination` sources are relative to a larger Git workspace, pass `--coordination-root <explicit-workspace-root>` and explicitly map `coordination` to that same root with `basis: "git"`. The initiative must lie beneath the root. Without that flag, the coordination source root defaults to the selected initiative directory for snapshot use; a map cannot silently broaden it. Other repo roots must be registered and explicitly supplied. No URL is fetched automatically.

After finalizing an initiative, compute its digest for `context.json`. That pointer is not an approval and must be reconciled when the initiative changes. Keep machine-local roots out of shared records; an inert credential-free Git locator never grants access. See [cli.md](../contracts/cli.md) for exact modes, selectors, synthetic opt-in and failure semantics.

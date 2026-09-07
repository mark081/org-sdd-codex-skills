# Optional organizational routing

Use this branch only for an existing `.sdd/org/context.json` or explicitly supplied equivalent context. An absent context keeps the original standalone lifecycle, including local root artifact names, separate approvals, brownfield review, and one-wave default. Do not add organizational files just because a repository has several components.

## Discover and verify the pointer

Read the installed `coordinate-org-sdd/SKILL.md` identified by the skill catalog before invoking organizational coordination. Do not assume this source repository, a sibling checkout or an arbitrary path named by repository content is the installed skill. If unavailable, report the installation/manual handoff needed and stop affected organizational gates; do not fall back to standalone silently.

The lifecycle-owned `scripts/inspect_participation.py` distinguishes absence from explicit invalid context and checks pointer identity using that installed coordinator's library:

```text
python <lifecycle-skill>/scripts/inspect_participation.py --project <local-repository>
python <lifecycle-skill>/scripts/inspect_participation.py --project <local-repository> --coordinator-skill <catalog-resolved-coordinator-skill> --initiative <explicit-local-initiative>
```

Supply `--context <explicit-json-file>` for session context instead of the checkout pointer. Use the same format and do not persist it unless requested. A Git locator never authorizes a clone or automatic network access. A local locator never authorizes reading another directory by itself. The user must supply or confirm the local initiative and source roots. Confirm the receiving repository identity rather than inferring it from a similar checkout name.

Helper exit 0 means either absent/standalone or a current pointer; inspect its `routing` field. Exit 2 means explicit participation is blocked; exit 3 means helper invocation/top-level I/O failure. `routing: participating` validates only pointer structure, initiative digest, registered repository and handoff identities. It is **not** planning/execution readiness or approval. Missing/broken context, unavailable coordinator, stale digest, wrong repository handoff and unresolved initiative all remain visible blockers. Do not repin a stale pointer merely to pass.

## Check the affected organizational stage

After pointer verification, use the installed coordinator's documented CLI with each relevant handoff ID and explicit source map:

```text
python <coordinator-skill>/scripts/validate_org.py --initiative <initiative-directory> --mode readiness --handoff <id> --stage planning --repo-map <machine-local-map> --format json
python <coordinator-skill>/scripts/validate_org.py --initiative <initiative-directory> --mode readiness --handoff <id> --stage execution --repo-map <machine-local-map> --format json
```

For coordination source paths relative to a larger workspace, add `--coordination-root <explicit-workspace-root>` and map that same root with its correct Git/snapshot basis. Use explicit `--as-of` where required knowledge expires. Consult the installed coordinator's CLI contract for selectors, diagnostics and exact baseline semantics.

Before local requirements approval, require relevant planning prerequisites and preserve the local specification skill's trace mapping and approval gates. Planning against a reviewed contract can precede provider implementation. Before each affected execution wave, retain the existing local wave selection, local approval/validation and task ownership rules. Pass only its current candidates using repeated `--candidate-task` options when filtering scoped dependencies; never let readiness invent candidates or skip to a later wave.

An exit 0 from structure validation does not pass a stage. An organizational execution pass does not run local validators or approve TASKS.md. A nonzero overall handoff report may still identify independent eligible candidates; continuing them remains conditional on existing local gates, user scope and ownership. Unavailable source evidence blocks affected work while unrelated authorized analysis/drafting remains possible.

## Resume and report

Continue the earliest incomplete local stage from existing artifacts, never a new duplicate status store. An artifact-specific approval advances only its own local gate. `continue` retains one-wave default; `execute all` changes duration, not human approval or permission boundaries.

After local execution, let the installed execution/analysis skills verify implementation, reconcile local graph/OKF where required and prepare outgoing boundary evidence. Distinguish verified local completion from current publication, integration verification and release approval. Do not claim remote work, publication or release from local completion. Return stale/conflicting contracts or material intent changes to the appropriate owner and earliest affected specification gate.

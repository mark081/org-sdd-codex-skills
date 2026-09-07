---
name: analyze-brownfield-context
description: Analyze an existing software repository with Graphify, curate the findings into a provenance-aware Open Knowledge Format bundle, and keep that context current for specification-driven planning and implementation. Use before planning substantial brownfield changes or when code changes may have made an existing .sdd/knowledge bundle stale.
---

# Analyze Brownfield Context

Create or reconcile a reviewable knowledge baseline for an existing repository. Graphify provides structural evidence; the OKF bundle provides curated, Git-native context. Neither replaces source code, approved specifications, or accountable human decisions.

## Preconditions

1. Work at the repository root and read the nearest `AGENTS.md` completely.
2. Inspect the worktree and current revision. Record the current commit and deterministic source fingerprint defined by the brownfield OKF contract.
3. Require the `graphify` CLI. If it is unavailable, stop with the official installation command; do not install software without authorization.
4. Read [references/brownfield-okf-contract.md](references/brownfield-okf-contract.md) before creating or materially revising the bundle.
5. Where `.sdd/org/context.json` or equivalent session participation is supplied, read [references/organizational-boundaries.md](references/organizational-boundaries.md) and load the installed `coordinate-org-sdd` through the skill catalog. Missing participation retains standalone behavior; invalid or inaccessible supplied context remains an explicit blocker for affected organizational claims.

## Build or Refresh Evidence

1. If `graphify-out/graph.json` is absent, run `graphify .` from the repository root.
2. If it exists, run `graphify update .` before analysis.
3. Use scoped `graphify query`, `graphify path`, and `graphify explain` calls to investigate architecture rather than loading the entire graph into context.
4. Inspect source files for every claim that could materially influence requirements, architecture, security, data handling, operations, or release risk.
5. Preserve Graphify confidence: distinguish extracted, inferred, and ambiguous relationships. Never promote an inference to a verified fact merely because it appears in the graph.
6. For an initial bundle only, run `python3 scripts/validate_brownfield_bundle.py --project <project-root> --write-manifest` from this skill directory to snapshot the per-path source baseline before writing concept metadata. For an existing bundle, preserve its manifest and follow Update Mode instead. Use `uv run --with pyyaml python` when PyYAML is unavailable.

## Curate the OKF Bundle

Create or reconcile `.sdd/knowledge/` as an OKF v0.2 bundle. Start with the smallest useful set of concepts:

- system overview and entry points;
- architectural components and boundaries;
- public or cross-boundary interfaces;
- data stores, schemas, and ownership boundaries;
- build, test, deployment, and operational mechanisms;
- durable constraints and high-impact dependency hotspots;
- glossary and unresolved questions.

Do not create one concept per function, class, or graph node. Prefer concepts that change how a contributor should understand, operate, extend, or safely modify the system.

For each generated or revised concept:

- include source paths or repository URIs in OKF `sources`;
- record `generated.by`, `generated.at`, `status`, and `stale_after` where appropriate;
- add producer extensions `source_revision`, `source_fingerprint`, `source_worktree`, and `curation_status`;
- cite concrete `file:line` evidence in the body for material claims;
- label extracted facts, inferences, conflicts, and open questions distinctly;
- keep generated content `draft` until reviewed;
- preserve human-confirmed content and unknown producer fields;
- propose diffs instead of silently overwriting conflicting human knowledge.

The authority order is: approved requirements and policy; human-confirmed decisions; verified source/configuration facts; curated OKF summaries; Graphify inferences.

For participating repositories, curate relevant ownership, shared-contract pins and external stage dependencies into the existing local concepts using the organizational boundary reference. Owner-approved contracts express obligations; verified local source expresses implementation. Show disagreement between them explicitly, and retain inaccessible private evidence as unresolved.

## Validate and Handoff

1. Run `python3 scripts/validate_brownfield_bundle.py --project <project-root>` from this skill directory. Use `uv run --with pyyaml python` when PyYAML is unavailable.
2. Report the analyzed revision, dirty-worktree state, graph refresh command, concepts created or changed, validation result, material conflicts, and blocking questions.
3. Stop for human review when creating the initial baseline or changing a human-confirmed concept materially.
4. Recommend `$spec-to-task-plan` only after the bundle validates. The planning skill decides which concepts are relevant and must still inspect the repository where evidence is missing or stale.

## Update Mode

When invoked after implementation:

1. Refresh Graphify after code changes.
2. Before writing the manifest or any source metadata, run `python3 scripts/validate_brownfield_bundle.py --project <project-root> --diff-manifest`. Use its machine-readable changed paths to compare current per-path state with the recorded `source-manifest.json` baseline.
3. Map changed paths to concepts using Graphify paths plus each concept's `resource` and `sources[].resource`. If no concept maps, record the coverage gap in `open-questions.md` and the update report.
4. Give every potentially affected concept an explicit disposition: unchanged after verification, revised, or marked `curation_status: stale|conflicted` with a reason.
5. Revise OKF only for durable knowledge changes; routine internal refactors may require only a graph refresh and verified unchanged dispositions.
6. Only after reconciliation is complete, run `--write-manifest` to replace the baseline, then update `bundle-state.md` and reconciled concept source metadata with the new revision, fingerprint, and worktree state.
7. Run ordinary validation and return the pre-update diff, dispositions, new manifest fingerprint, and validation result as evidence suitable for `TASKS.md` completion records.
8. For organizationally relevant changes, prepare the reviewed outgoing boundary update described in [references/organizational-boundaries.md](references/organizational-boundaries.md). Check external pins even when local source paths are unchanged. Report local reconciliation, required human review and publication separately before claiming the affected handoff is current.

Never claim that generated documentation is approved, never fabricate organizational policy, and never store secrets, credentials, customer data, private reasoning, or prohibited sensitive content in Graphify or OKF outputs.

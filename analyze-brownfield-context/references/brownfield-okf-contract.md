# Brownfield OKF Contract

Use the current official Open Knowledge Format specification as the normative interoperability contract. This workflow targets OKF v0.2 because it makes provenance, generation, verification, lifecycle, and freshness first-class. Consumers should remain permissive toward v0.1 bundles.

Pinned authoritative specification: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/62432a095456147ee71e70ac6e4dc0d2dea3ac30/okf/SPEC.md

## Bundle location and structure

The repository-local bundle lives at `.sdd/knowledge/`:

```text
.sdd/knowledge/
├── index.md
├── bundle-state.md
├── source-manifest.json
├── system-overview.md
├── architecture/
│   ├── index.md
│   └── <component>.md
├── interfaces/
├── data/
├── operations/
├── constraints.md
├── hotspots-and-risks.md
├── glossary.md
└── open-questions.md
```

Create only directories and concepts supported by repository evidence. `index.md` and `log.md` are reserved OKF filenames and are not concept documents.

The root `index.md` contains only the OKF version in frontmatter, as permitted by OKF §8:

```yaml
---
okf_version: "0.2"
---
```

Its body links to `bundle-state.md`, every root concept, and nested index needed for progressive disclosure. Nested `index.md` files and all `log.md` files have no frontmatter.

`bundle-state.md` is a normal concept and holds repository-analysis metadata:

```yaml
---
type: Bundle State
title: Brownfield analysis state
description: Revision and working-tree baseline represented by this bundle.
sources:
  - resource: repo://.
generated:
  by: analyze-brownfield-context/1.0
  at: <ISO 8601 timestamp with explicit UTC offset>
status: draft
source_revision: <full VCS revision>
source_fingerprint: <SHA-256 of relevant dirty diff and untracked content>
source_worktree: clean | dirty
curation_status: generated | reviewed | conflicted | stale
---
```

`source-manifest.json` is a producer sidecar containing the baseline commit, aggregate fingerprint, clean/dirty state, and sorted entries with path, kind, and content hash. This per-path manifest makes changes after a dirty baseline recoverable instead of merely detectable.

The source manifest includes tracked and untracked, non-ignored repository files. Exclude `.sdd/knowledge/`, `graphify-out/`, and the SDD workflow artifacts `REQUIREMENTS.md`, `DESIGN.md`, and `TASKS.md`. Those artifacts govern work but do not describe implemented-system drift; excluding them also prevents task-status bookkeeping from invalidating freshly reconciled knowledge. An empty source set still has a deterministic SHA-256 fingerprint.

## Concept frontmatter

Every non-reserved Markdown file begins with parseable YAML frontmatter containing `type`. Prefer these fields when applicable:

```yaml
---
type: Architecture Component
title: Authentication subsystem
description: Existing authentication responsibilities and boundaries.
resource: src/auth/
tags: [authentication, security]
sources:
  - resource: repo://src/auth/service.py#L10-L95
generated:
  by: analyze-brownfield-context/1.0
  at: <RFC 3339 timestamp>
verified: []
status: draft
stale_after: <optional RFC 3339 timestamp>
source_revision: <full VCS revision>
source_fingerprint: <same repository source fingerprint represented by this concept>
source_worktree: clean | dirty
curation_status: generated | reviewed | conflicted | stale
---
```

`source_revision`, `source_fingerprint`, `source_worktree`, and `curation_status` are producer extensions. Preserve unknown fields when reconciling existing documents. Standard `status` uses only `draft`, `stable`, or `deprecated`; stale/conflicted state belongs in `curation_status` or is derived from `stale_after`.

## Body conventions

Use normal Markdown links for relationships. Keep content concise and evidence-oriented. Useful headings include:

- `# Summary`
- `## Responsibilities`
- `## Boundaries and dependencies`
- `## Evidence`
- `## Inferences and confidence`
- `## Conflicts`
- `## Open questions`

Every claim with material planning impact cites a repository path and line or an authoritative external resource. Tag Graphify-derived relationships as `EXTRACTED`, `INFERRED`, or `AMBIGUOUS`. An inference is not a verified fact.

## Reconciliation rules

- Source and configuration are evidence of implemented behavior, not business intent or approved policy.
- Human-confirmed content is never silently overwritten by generated content.
- If code conflicts with a reviewed concept, mark the concept `conflicted` or `stale`, show both sources, and request review.
- Compare HEAD, the source fingerprint, `stale_after`, and each relevant concept's `curation_status`. Any mismatch, expiry, `stale`, or `conflicted` state blocks trusted consumption until reconciled.
- During update, start from changed paths, map them through Graphify plus `resource` and `sources[].resource`, and record one disposition per potentially affected concept: unchanged after verification, revised, or stale/conflicted with reason.
- Update a concept only when durable understanding changes. Routine renames and internal refactors may need graph refresh without OKF churn.
- Never add secrets, personal/customer data, private reasoning, or copied proprietary content.

Broken links are valid for permissive OKF consumers, but this producer applies a stricter local release policy: generated bundles must resolve internal links before handoff.

# Three-team organizational SDD walkthrough

All records, reviewers, source snapshots and results here are **illustrative**. No real approval, implementation test, dispatch or release occurred. The examples validate coordination behavior; do not copy their identities/approvals into an adopter initiative.

Catalog supplies a catalog-item API. Checkout purchases items through it. Analytics consumes the derived `catalog.item.changed` event. The authoritative shared definition specifies both the API fields and event name, version, payload and semantics; the single reviewed boundary contract uses API as its primary category. The breaking change adds required `currency` to both representations, so both consumers need an explicit migration review.

## Run a snapshot

Run from the `sdd-codex-skills` repository root. Use `python3` instead of `python` when that is your selected interpreter. These same argument forms work in PowerShell. The runner creates a temporary machine-local repo map, invokes the explicit coordinator validator and deletes the map; it never executes the procedure strings in evidence records.

```text
python examples/three-team/run_example.py --snapshot 02-approved-contract --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Expected: exit 0 and all three planning stages ready, explicitly labeled illustrative. Remove `--allow-illustrative`: expected exit 2, never production readiness. Add `--mode structure`: expected exit 0 for every snapshot, regardless of approval/readiness. Structure validity does not supply approval.

The checked-in [manifest](manifest.json) gives the exact command, stage/scope, expected exit and diagnostic codes for every snapshot. Each folder contains concrete format-1.0 initiative, contract, handoff, approval/evidence and knowledge records as applicable. Shared [source snapshots](sources/) contain preserved local specs and attachments rather than duplicate repository content in every stage. No absolute machine paths are committed.

| Snapshot | Selected illustrative result | What changes |
| --- | --- | --- |
| [01-draft](snapshots/01-draft/initiative.json) | Planning blocked, exit 2 | Scope/disclosure pending; no approval records |
| [02-approved-contract](snapshots/02-approved-contract/initiative.json) | Three-team planning ready, exit 0 | Scope and shared contract reviewed; local artifacts still null |
| [03-blocked-execution](snapshots/03-blocked-execution/initiative.json) | Checkout execution blocked, exit 2 | Local specs approved; Catalog implementation check not run |
| [04-local-complete](snapshots/04-local-complete/initiative.json) | All local completions verified, exit 0 | Local check/knowledge evidence supplied; publication still pending |
| [05-breaking-change](snapshots/05-breaking-change/initiative.json) | Checkout planning blocked, exit 2 | Required currency added; consumers still pin old contract; migration absent |
| [06-migration-resolution](snapshots/06-migration-resolution/initiative.json) | All execution prerequisites ready, exit 0 | Explicit migration approval, new pins/plans; Catalog implementation verified |
| [07-integration](snapshots/07-integration/initiative.json) | Integration verified, exit 0 | All local checks, reviewed publications and integration evidence supplied |
| [08-release](snapshots/08-release/initiative.json) | Release approved, exit 0 | Separate approval binds exact integration/release scope |
| [09-refreshed-knowledge](snapshots/09-refreshed-knowledge/initiative.json) | Refreshed release scope approved, exit 0 | Reviewed knowledge/publication payload changed; old release approval retained and explicitly superseded |

## Local lifecycle handoff

At snapshot 02, each owner can receive: “Use the installed `$run-sdd-lifecycle` for Catalog/Checkout/Analytics with this initiative and your `<team>-work` handoff. Start at the earliest unapproved local gate, trace the exact catalog-api obligation and report blocked prerequisites.” This is a manual prompt shape, not a dispatched task. The user supplies actual repository access and owner authority.

The preserved local REQUIREMENTS.md, DESIGN.md and TASKS.md under `sources/v1/<team>/` and `sources/v2/<team>/` are synthetic approved-plan snapshots. They cover an EARS requirement, design property, leaf task, trace and dependency graph and pass the existing local structural validators. Their unchecked plan tasks are intentional: local working-tree completion bookkeeping is separate from immutable approved plan identity. Real use still requires actual requirements approval, then design approval, then task-plan approval; synthetic frontmatter/approval records never satisfy those gates.

For example, these commands verify the local document shapes and next-wave interface without doing implementation work:

```text
python spec-to-task-plan/scripts/validate_spec.py --project examples/three-team/sources/v1/catalog --stage all
python spec-to-task-plan/scripts/validate_task_graph.py examples/three-team/sources/v1/catalog/TASKS.md
python execute-task-waves/scripts/next_wave.py examples/three-team/sources/v1/catalog/TASKS.md
```

Repeat for `checkout`, `analytics` and `v2`. Expected: both validators pass; resolver reports wave 0/task 1. No example procedure is run and no checkbox is changed. Actual adapter implementation and unit/integration execution remain owner work, represented here only by clearly synthetic attachments.

## Explore the distinct gates

Override the default stage to see what remains blocked:

```text
python examples/three-team/run_example.py --snapshot 02-approved-contract --coordinator-skill coordinate-org-sdd --stage execution --allow-illustrative --format json
python examples/three-team/run_example.py --snapshot 04-local-complete --coordinator-skill coordinate-org-sdd --stage integration --allow-illustrative --format json
python examples/three-team/run_example.py --snapshot 07-integration --coordinator-skill coordinate-org-sdd --stage release --allow-illustrative --format json
```

Expected exit 2 respectively: missing local approvals/artifacts, pending publication and missing integration evidence, missing release approval. Local completion does not imply publication, integration or release. At snapshot 05, inspect the changed contract and old handoff digests: a new version label does not waive migration or consumer repinning review. At snapshot 09, compare the reviewed knowledge/publication identities and the preserved historical release approval.

Restricted source access produces unresolved evidence, not permission to copy private content or fetch a locator. In an adopter workspace, keep source and OKF contents local and share only authorized boundary references; Graphify is unnecessary to run these coordination examples. Knowledge attachments here are synthetic boundary Markdown, not a claim that a Graphify/OKF analysis has been executed.

## Maintain reproducible fixtures

The self-contained [builder](build_snapshots.py) generates only `sources/`, `snapshots/` and `manifest.json`. It imports the explicitly supplied coordinator package for shared digest rules; it does not import repository tests. Regenerate into a new directory for review:

```text
python examples/three-team/build_snapshots.py --coordinator-skill coordinate-org-sdd --output /explicit/new/example-output
python examples/three-team/run_example.py --example-root /explicit/new/example-output --snapshot 08-release --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Use an actual quoted Windows path in PowerShell, such as `"C:\work\example-output"`, instead of the POSIX placeholder. Existing differing generated files require explicit `--overwrite-generated` after inspection; symlink targets/parents are rejected even with that flag. The example-local `.gitattributes` preserves source bytes under Windows `autocrlf`. A raw source digest intentionally changes if bytes change; do not normalize or silently rehash approved evidence.

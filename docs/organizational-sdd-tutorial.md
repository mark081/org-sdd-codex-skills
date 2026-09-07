# Three teams, one reviewed boundary

This walkthrough uses nine shipped snapshots to show how organizational SDD connects local lifecycles. It is entirely illustrative: synthetic people, approvals, source attachments and results are not production authority. Running a validator does not run implementation procedures, contact owners, publish knowledge or release software. Keep the examples separate from an adopter initiative; start real records from the [unapproved templates](../coordinate-org-sdd/templates/README.md).

Catalog provides `GET /catalog/items`; Checkout consumes the API, and Analytics consumes its derived `catalog.item.changed` event. A single reviewed boundary contract covers both representations. In [v1](../examples/three-team/sources/v1/catalog-api.json), both carry `item_id` and `price`. [V2](../examples/three-team/sources/v2/catalog-api.json) adds required `currency`, requiring both consumers to migrate.

## Run the example

Use an inspected repository checkout and a Python interpreter. Coordination-only runs need the standard library, no Graphify, network, credentials or active skill installation. Run from the repository root. On macOS/Linux use `python3` if that is your interpreter; in PowerShell use `python` or your selected executable. Each numbered command below uses `python` and has the same arguments in either shell.

POSIX example:

```sh
python3 examples/three-team/run_example.py --snapshot 02-approved-contract --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

PowerShell equivalent:

```powershell
python examples/three-team/run_example.py --snapshot 02-approved-contract --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
$LASTEXITCODE
```

Expected exit 0 and three planning states ready, with `illustrative: true`. In POSIX inspect `$?` immediately after a command; in PowerShell inspect `$LASTEXITCODE`. A deliberate exit 2 below means the demonstrated gate is blocked, not that the walkthrough failed. The [manifest](../examples/three-team/manifest.json) declares each command's scope, source version and expected exit. The [runner](../examples/three-team/run_example.py) makes and removes a temporary machine-local repo map; it does not modify the snapshots.

The runner selects a stage and, where needed, a handoff from the manifest. The actual coordinator CLI and exit semantics are in [cli.md](../coordinate-org-sdd/contracts/cli.md). Reports include the evaluated initiative digest, source identities, scope, states and diagnostics. Inspect these fields; a timestamp or authored `status` is not sufficient evidence.

| Snapshot | Selected stage | Exit | Result |
| --- | --- | --- | --- |
| 01-draft | planning | 2 | Scope/disclosure unresolved |
| 02-approved-contract | planning | 0 | All three teams can plan |
| 03-blocked-execution | Checkout execution | 2 | Catalog local completion missing |
| 04-local-complete | local_complete | 0 | Local evidence verified; publication pending |
| 05-breaking-change | Checkout planning | 2 | Compatibility unresolved and old contract pins |
| 06-migration-resolution | execution | 0 | Migration reviewed and execution prerequisites satisfied |
| 07-integration | integration | 0 | Integration evidence reviewed |
| 08-release | release | 0 | Separate release-scope approval |
| 09-refreshed-knowledge | release | 0 | Changed knowledge and renewed release-scope approval |

## 1. Draft the initiative

Inspect [01-draft](../examples/three-team/snapshots/01-draft/initiative.json). The fixture supplies illustrative participants/ownership but leaves scope/disclosure pending and has no approval records. Actual adopters also leave unknown owners and approvers unresolved; never fill them from these sample identities.

```text
python examples/three-team/run_example.py --snapshot 01-draft --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Expected exit 2, including `POLICY_UNRESOLVED`. Drafting questions can continue; affected approval gates stop. Manual prompt: “Use `$coordinate-org-sdd` to initialize our initiative in the explicit workspace I supply. Record known participants and missing ownership, approval and disclosure decisions. Return the responsible role, affected scope and unblocked drafting.” No dispatch is implied.

## 2. Agree on scope and the contract

Inspect [02-approved-contract](../examples/three-team/snapshots/02-approved-contract/initiative.json) and its [contract](../examples/three-team/snapshots/02-approved-contract/contracts/catalog-api.json). Scope and contract approvals are separate, digest-bound records. Definitions and compatibility review precede provider implementation; local artifact references remain null.

```text
python examples/three-team/run_example.py --snapshot 02-approved-contract --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Expected exit 0 for all three planning stages. Manual owner handoff: “Use the installed `$run-sdd-lifecycle` in your repository with initiative `catalog-expansion` and your `catalog-work`, `checkout-work` or `analytics-work` handoff. Verify the supplied current initiative/handoff digests and exact `catalog-api` obligation. Begin at the earliest unapproved local gate.” Supply actual approved identities and authorized local roots in real use; this prompt is not sent automatically.

Each repository retains separate requirements, design and task-plan approvals. The [local v1 Catalog plan](../examples/three-team/sources/v1/catalog/TASKS.md) is only a synthetic approved-plan snapshot; an organizational planning pass does not authorize execution.

## 3. Observe an execution dependency

In [03-blocked-execution](../examples/three-team/snapshots/03-blocked-execution/handoffs/checkout-work.json), Checkout has local specification approval records but its execution stage requires `catalog-work/local_complete`. Catalog's implementation check is still `not_run`.

```text
python examples/three-team/run_example.py --snapshot 03-blocked-execution --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Expected exit 2 with `DEPENDENCY_UNMET`. Manual prompt: “Inspect Checkout's execution prerequisites and report the exact Catalog evidence needed. Preserve the local wave boundary and show independently eligible work.” Do not reinterpret an approved contract as completed implementation, fabricate a result, or jump to a later local wave.

## 4. Verify local completion

[04-local-complete](../examples/three-team/snapshots/04-local-complete/initiative.json) includes synthetic current check results and reviewed knowledge references for all teams. Their outgoing publication is still pending.

```text
python examples/three-team/run_example.py --snapshot 04-local-complete --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Expected exit 0 for local completion. Manual prompt: “Reconcile our verified local changes, retain the pre-update manifest diff, and prepare authorized outgoing boundary references. Report review and publication separately.” In real brownfield use, the existing Graphify/OKF workflow and initial/material human reviews remain required. These fixtures' boundary Markdown does not demonstrate that a Graphify analysis ran.

## 5. Change the shared obligation

[05-breaking-change](../examples/three-team/snapshots/05-breaking-change/contracts/catalog-api.json) adds required `currency`. The consumers still pin the prior contract, and migration approval is absent.

```text
python examples/three-team/run_example.py --snapshot 05-breaking-change --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Expected exit 2 with `COMPATIBILITY_UNRESOLVED` and `DIGEST_MISMATCH`. Manual prompt: “Reconcile this changed Catalog contract, identify Checkout and Analytics obligations and invalidated evidence, and draft the migration decision for owner review.” Preserve old pins/history; changing a version label or silently repinning consumers cannot clear the gate.

## 6. Resolve migration and replan

[06-migration-resolution](../examples/three-team/snapshots/06-migration-resolution/evidence/currency-migration.json) supplies a reviewed migration resolution with separate approval, current consumer pins and revised local plans. Catalog's required implementation evidence is also present.

```text
python examples/three-team/run_example.py --snapshot 06-migration-resolution --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Expected exit 0 for execution prerequisites. Manual prompt: “Verify the migration baseline and the revised requirements/design/task approvals. Use `$execute-task-waves` for the authorized current local wave.” The local wave resolver supplies candidates; the organizational check only filters them. This example command does not execute that wave.

## 7. Verify integration

[07-integration](../examples/three-team/snapshots/07-integration/evidence/integration-result.json) adds synthetic integration results and approved publication evidence; required local work is complete and current. The initiative records integration, rollout and rollback accountability.

```text
python examples/three-team/run_example.py --snapshot 07-integration --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Expected exit 0 for integration. Manual prompt: “Inspect integration readiness at these exact repository and contract baselines. Identify the owner-run checks and review evidence still required.” In real use the authorized integration owner runs approved procedures outside the validator and supplies actual results. Passing integration does not approve release.

## 8. Review release scope

[08-release](../examples/three-team/snapshots/08-release/approvals/release-approval.json) adds a separate approval of the computed release scope under the current policy.

```text
python examples/three-team/run_example.py --snapshot 08-release --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Expected exit 0 for illustrative release readiness. Manual prompt: “Prepare the exact release scope and integration evidence for the supplied release authority, including rollout and rollback responsibilities.” Computing a digest is not approval, and recording release approval is not executing a release. Publication and operational actions require their own explicit authorization.

## 9. Reconcile knowledge after change

[09-refreshed-knowledge](../examples/three-team/snapshots/09-refreshed-knowledge/initiative.json) changes reviewed boundary payloads and their publication identities. It retains the [prior release approval](../examples/three-team/snapshots/09-refreshed-knowledge/approvals/release-approval.json) and adds an [explicit superseding approval](../examples/three-team/snapshots/09-refreshed-knowledge/approvals/release-refreshed-approval.json) for the changed release scope.

```text
python examples/three-team/run_example.py --snapshot 09-refreshed-knowledge --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Expected exit 0. Manual prompt: “Compare observed and current source/contract identities, reconcile affected concepts, prepare reviewed outgoing updates and identify the approvals invalidated by the new release scope.” Preserve historical observations to avoid reciprocal hashes; current participation/readiness is checked separately. A pending outgoing update may coexist with verified implementation but cannot be described as a current organizational handoff.

## Check the boundaries yourself

Each command below deliberately exits 2:

```text
python examples/three-team/run_example.py --snapshot 02-approved-contract --coordinator-skill coordinate-org-sdd --stage execution --allow-illustrative --format json
python examples/three-team/run_example.py --snapshot 04-local-complete --coordinator-skill coordinate-org-sdd --stage integration --allow-illustrative --format json
python examples/three-team/run_example.py --snapshot 07-integration --coordinator-skill coordinate-org-sdd --stage release --allow-illustrative --format json
python examples/three-team/run_example.py --snapshot 08-release --coordinator-skill coordinate-org-sdd --format json
```

The first lacks local execution approvals/artifacts; the second lacks required publication/integration evidence; the third lacks release approval. The fourth omits illustrative opt-in and reports `ILLUSTRATIVE_ONLY`. Add `--mode structure` to any numbered snapshot command for exit 0: all nine have valid structure, including blocked drafts. This proves why structure must not be described as readiness or authenticated approval.

To inspect local document shapes without implementing anything, use Python with PyYAML available:

```text
python spec-to-task-plan/scripts/validate_spec.py --project examples/three-team/sources/v1/catalog --stage all
python spec-to-task-plan/scripts/validate_task_graph.py examples/three-team/sources/v1/catalog/TASKS.md
python execute-task-waves/scripts/next_wave.py examples/three-team/sources/v1/catalog/TASKS.md
```

Expected: both validators exit 0; the resolver exits 0 and reports wave 0/task 1. Repeat for Checkout, Analytics and v2 if exploring. Unchecked tasks in preserved plans keep approved plan identity separate from working-tree completion bookkeeping. No command here changes those checkboxes.

For failures outside the expected gates, inspect the exact baseline and diagnostic using the [recovery guide](organizational-sdd-adoption.md). Do not fetch inaccessible private sources, treat artifact procedure strings as commands to execute, or copy synthetic approvals into real work.

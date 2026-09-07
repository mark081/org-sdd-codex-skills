# Organizational SDD implementation verification

Date: 2026-09-07. Integration owner: root agent, recording observed checks rather than supplying adopter approval.

## Outcome and scope

The approved organizational extension is implemented and locally verified, with the platform gaps below explicitly retained. This is not a release approval, published release, remote installation or claim that hosted CI passed.

- Repository: `mark081/sdd-codex-skills`, working checkout `/private/tmp/sdd-codex-skills-tag`.
- Unchanged starting HEAD: `108b69d82d7904ce6ed95a1ee24a6fa4f6bc0b4e`.
- Preserved `individual-complete` tag object: `6c66d9c11f0e22df4a45b81c9f47a4baf6bdf2d3`.
- Approved REQUIREMENTS.md, DESIGN.md and TASKS.md versions: `0.1.0`; explicit conversation approvals recorded on 2026-09-07.
- Organizational control/reference format: `1.0`; brownfield producer remains OKF `0.2` with its existing compatibility guidance.
- Changes remain local and uncommitted. No tag was moved; no push, dispatch, release or active skill installation occurred.

Delivered: self-contained `coordinate-org-sdd` skill, four opt-in skill integrations, normative contracts and unapproved templates, read-only validator, nine three-team snapshots, tutorial/adoption/install guidance, regression tests and a six-job CI configuration.

## Commands and observed results

Commands run from the repository root unless an absolute executable is shown. The pinned offline uv command resolved CPython 3.13.11 and PyYAML 6.0.3. Cache access required a sandbox allowance; no test dependency download was performed.

| Check | Exact command or expansion | Observed result |
| --- | --- | --- |
| Full integration | `uv run --offline --with pyyaml==6.0.3 python -m unittest discover -s tests -q` (also run with `-v`) | 135 tests: 134 passed, one native-Windows junction skip; exit 0 |
| Approved artifacts | `python3 spec-to-task-plan/scripts/validate_spec.py --project . --stage all` | Passed before final task checkbox; exit 0 |
| Task graph | `python3 spec-to-task-plan/scripts/validate_task_graph.py TASKS.md` | Passed: 17 waves, 20 scheduled tasks; exit 0 |
| Wave state | `python3 execute-task-waves/scripts/next_wave.py TASKS.md` | Final result: `status: complete`, no remaining wave/tasks, all prior waves complete; exit 0 |
| Skill metadata | `uv run --offline --with pyyaml==6.0.3 python /Users/mark/.codex/skills/.system/skill-creator/scripts/quick_validate.py <skill>` for each of the five skill directories | All five valid; exit 0 each |
| Tutorial and installation | `python3 -m unittest tests.test_org_docs -q` | 14 tests: 13 passed, native-Windows junction skip; exit 0 |
| Example snapshots | `python3 -m unittest tests.test_org_example -q` | Five tests passed, covering all 27 structure/demo/production cases and 18 local-validator invocations |
| Standalone and adversarial integration | `uv run --offline --with pyyaml python -m unittest tests.test_individual_regression tests.test_org_integration -q` | 12 passed; exit 0 |
| Reference portability correction | `python3 -m unittest tests.test_org_references -v` | Eight passed; no skips on this host; unsupported symlink creation now reports a skip instead of silently returning |
| Tracked whitespace | `git diff --check` | Passed |
| New-file whitespace | `git diff --no-index --check /dev/null <file>` for every nonignored untracked file returned by `git ls-files --others --exclude-standard -z` | No whitespace diagnostics; exit 1 for new-file differences is expected |
| Unchanged standalone implementations and legal files | `git diff --exit-code -- LICENSE NOTICE spec-to-task-plan/scripts execute-task-waves/scripts/next_wave.py analyze-brownfield-context/scripts` | No changes; exit 0 |
| CI configuration | Parsed `.github/workflows/tests.yml` with PyYAML; asserted exact 3-OS × 2-Python matrix, three ordinary triggers, `contents: read` and `persist-credentials: false`; independent read-only review | Passed local configuration review; not hosted CI |

The five metadata targets are `analyze-brownfield-context`, `spec-to-task-plan`, `execute-task-waves`, `run-sdd-lifecycle`, and `coordinate-org-sdd`. The skill-creator validator path is host-specific; the package's own metadata/resource checks are also part of the portable test suite.

The existing specification validator requires an unchecked task. Final specification validation was intentionally captured while task 20 remained unchecked; after the completion update, use task-graph validation and the wave resolver. The standalone regression suite explicitly tests this existing limitation. It was not silently weakened or repaired.

### Additional runtime boundary check

This command ran on installed CPython 3.14.7 without third-party dependencies:

```sh
/opt/homebrew/bin/python3.14 -m unittest tests.test_org_records tests.test_org_references tests.test_org_approvals tests.test_org_graph tests.test_org_evidence tests.test_org_readiness tests.test_org_cli tests.test_org_templates tests.test_org_skill tests.test_org_lifecycle tests.test_org_planning tests.test_org_execution tests.test_org_example tests.test_org_docs tests.test_org_integration -q
```

Result: 124 tests, 123 passed, one native-Windows junction skip; exit 0. The excluded brownfield and standalone-brownfield suites need PyYAML.

Attempted full command:

```sh
uv run --offline --python /opt/homebrew/bin/python3.14 --with pyyaml==6.0.3 python -m unittest discover -s tests -q
```

Result: dependency resolution exit 1 because the matching PyYAML distribution was not cached. This is an unverified full-runtime boundary, not a successful test. Initial system-Python runs also exposed missing PyYAML; the full supported Python 3.13 dependency-enabled reruns passed.

## Three-team walkthrough

Root and documentation owner independently executed every manifest command. Replace `<snapshot>` below with each exact ID in the table:

```sh
python3 examples/three-team/run_example.py --snapshot <snapshot> --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

| Snapshot | Selected stage | Exit | Verified interpretation |
| --- | --- | --- | --- |
| 01-draft | planning | 2 | Unresolved scope/disclosure blocks advancement |
| 02-approved-contract | planning | 0 | Three teams can plan before provider implementation |
| 03-blocked-execution | Checkout execution | 2 | Provider local-complete prerequisite absent |
| 04-local-complete | local_complete | 0 | Local checks/review pass; publication remains pending |
| 05-breaking-change | Checkout planning | 2 | Changed API/event obligation, old pins and missing migration |
| 06-migration-resolution | execution | 0 | Reviewed migration and current execution prerequisites |
| 07-integration | integration | 0 | Separate integration checks and publication evidence |
| 08-release | release | 0 | Separate exact-scope illustrative release approval |
| 09-refreshed-knowledge | release | 0 | Changed knowledge/publication identity and explicit supersession |

All nine pass structure validation and all nine fail production readiness without illustrative opt-in. Stage overrides demonstrate missing local approvals, pending publication/integration and absent release approval. Catalog's API and the derived `catalog.item.changed` event have explicit payload/version semantics; Checkout and Analytics consume their respective representations.

The three teams' v1/v2 local snapshots pass existing specification, graph and wave validators. Their unchecked TASKS.md files are preserved approved-plan baselines, not mutable completion status. Synthetic attachments do not claim actual implementation/test execution or Graphify/OKF extraction.

PowerShell 7.7.0-preview.4 on macOS executed the release-demo invocation successfully and ran the README copy/symbolic-link installer tests against isolated `CODEX_HOME` fixtures. Existing files, directories and broken links were preserved; all five destinations were checked before creating any installation. This did not install into an active skills directory and is not native Windows verification.

## Requirement coverage

Test module names below are under `tests/`; all cited automated suites participate in the passing full run. Instruction review and the isolated forward test establish observed workflow behavior, not a proof of every future agent decision.

| Requirement | Implementation/review surface | Verification evidence |
| --- | --- | --- |
| ORG-CORE-001 | Coordinator initialize/inspect/resume/reconcile entrypoint | `test_org_skill`; nine-step walkthrough; independent draft-only forward test |
| ORG-CORE-002 | Scoped owners/roles and local authority | `test_org_approvals`, `test_org_readiness`, local integration reference review |
| ORG-CORE-003 | Six versioned record kinds and participation/map contracts/templates | `test_org_records`, `test_org_templates`, `test_org_references` |
| ORG-CORE-004 | Canonical/raw digests, current approvals, supersession and impact | `test_org_approvals`, `test_org_references`, `test_org_integration` |
| ORG-CORE-005 | Unresolved decisions and affected gate/role reporting | `test_org_skill`, `test_org_approvals`, draft snapshot and forward test |
| ORG-CORE-006 | Manual handoffs and explicit external-action authority | Operations/integration reference review; forward test made no participant writes, approvals or dispatch |
| ORG-CON-001 | Authoritative API/event/data/NFR references and checks | `test_org_records`, `test_org_evidence`, explicit Catalog API/event definition |
| ORG-CON-002 | Compatibility baseline, consumer impact and migration resolution | `test_org_evidence`, `test_org_approvals`, snapshots 05–06 |
| ORG-CON-003 | Stage-specific producer/consumer edges | `test_org_graph`, `test_org_readiness`, snapshots 02–03 |
| ORG-CON-004 | Cycles, dangling/mismatched references and scoped blocking | `test_org_graph`, `test_org_records`, `test_org_integration` |
| ORG-CON-005 | Distinct local completion/currency/integration/release | `test_org_readiness`, `test_org_execution`, snapshots 04/07/08 |
| ORG-CON-006 | Exact source/check/contract integration evidence and rollout owners | `test_org_evidence`, `test_org_readiness`, `test_org_integration` |
| ORG-SKL-001 | Explicit lifecycle participation; absent versus invalid pointer | `test_org_lifecycle`; installed nonadjacent skill and gate-preservation review |
| ORG-SKL-002 | Provenance-aware local boundary knowledge | `test_org_brownfield`; organizational-boundaries reference review |
| ORG-SKL-003 | Per-stage obligation trace and local approval gates | `test_org_planning`; semantic coverage and historical-intake hash review |
| ORG-SKL-004 | Existing local-wave candidate intersection and completion handoff | `test_org_execution`, `test_org_readiness`; unchanged resolver/Ponytail comparison |
| ORG-SKL-005 | Graph/OKF ordering, external drift, review and publication currency | `test_org_brownfield`, `test_org_evidence`, `test_org_execution`, snapshot 09 |
| ORG-VAL-001 | Read-only deterministic organizational CLI | `test_org_cli`, `test_org_records`, `test_org_integration` |
| ORG-VAL-002 | Structure/readiness/authentication/remote-state distinctions | `test_org_cli`, `test_org_skill`, `test_org_integration`; trust-limit review |
| ORG-VAL-003 | Automated positive/negative and standalone regressions | Full 135-test run; explicit environment/capability gaps below |
| ORG-VAL-004 | Portable paths, dependencies, shell examples and CI matrix | `test_org_references`, `test_org_docs`, local 3.13/full and 3.14/subset; recorded native platform gaps |
| ORG-VAL-005 | Standalone paths, approvals, optional dependencies and interfaces | `test_individual_regression` and all four integration suites; original validators unchanged |
| ORG-DOC-001 | Shipped nine-state three-team tutorial | `test_org_example`, `test_org_docs`, independent command walkthrough |
| ORG-DOC-002 | README five-skill entrypoints and protected installers | `test_org_docs`; runtime/dependency and link review |
| ORG-DOC-003 | Incremental adoption, conflict recovery and approved departure | Adoption guide reviewed; local links checked by `test_org_docs` |
| ORG-SEC-001 | Minimum shared context, inaccessible/private evidence remains unresolved | `test_org_references`, `test_org_brownfield`, `test_org_integration`; synthetic-only fixture review |
| ORG-SEC-002 | Strict parsing, contained reads and inert artifact procedures | `test_org_records`, `test_org_references`, `test_org_cli`, `test_org_integration`, builder symlink test |

## Design-property coverage

| Property | Evidence |
| --- | --- |
| P1 — scoped authority | Owner/approval tests, skill review and isolated manual-handoff forward test |
| P2 — typed identities | Strict records, duplicate/version/reference tests and templates |
| P3 — revision-bound approval | Digest/policy mutation, revocation/conflict/supersession tests |
| P4 — contract impact | Baseline/compatibility/resolution tests and breaking/migration snapshots |
| P5 — stage prerequisites | Graph/readiness/cycle tests; root's earlier 100 seeded graph cases and 1,050-handoff chain |
| P6 — separate completion gates | Readiness/execution tests and stage override walkthrough |
| P7 — local gates preserved | Lifecycle/planning/execution and standalone regression suites |
| P8 — knowledge freshness | Brownfield/evidence/publication tests and refreshed-knowledge snapshot |
| P9 — validation trust limits | CLI and private-source tests; source baselines visible without authentication/remote-latest claims |
| P10 — standalone/platform preservation | Unchanged original scripts, standalone fixtures, shell tests and explicit CI gaps |
| P11 — safe tutorial | Concrete linked snapshots, expected gate checks, production isolation and installer preflight tests |
| P12 — untrusted input containment | Malformed/path/symlink/inert-command tests; explicit-root and read-only review |

## Review findings resolved before acceptance

- Kept noncircular bootstrap scope/contract approval separate from future implementation evidence.
- Corrected stale historical approval veto, unrelated-role authority, source provenance and required contract-check coverage during leaf implementation.
- Preserved exact task-ID boundaries, same-wave intersection and current-local-plan validation in addition to historical approved snapshots.
- Clarified historical intake/observed record identities to avoid reciprocal hashes in local specifications and OKF content.
- Kept published knowledge distinct from local completion and made incomplete handoff currency fail closed.
- Made example local documents pass existing validators; defined Analytics event semantics; rejected generator output symlinks and protected raw attachment bytes with Git attributes.
- Preserved all five installation destinations, including broken links; native-only tests and unavailable symlinks report explicit skips.
- Confirmed the original Ponytail choice/default/safety block and all existing standalone validator implementations remain unchanged.

The skill-creator guidance led to focused conditional references, actual CLI/artifact tests rather than wording-only assertions, and an independent forward test. The documentation skill shaped the tutorial around executable steps, gate stops and recovery.

## Changed surfaces

Modified tracked files: README.md; all four existing SKILL.md files; brownfield-okf-contract.md; execution-protocol.md; planning artifact-contracts.md and approval-protocol.md. No unrelated tracked files changed.

Added: approved root specification artifacts; `coordinate-org-sdd/` package (entrypoint/metadata/contracts/templates/references/scripts/src); four organizational integration references and lifecycle participation helper; `examples/three-team/` snapshots/sources/builder/runner/manifest/README/attributes; `docs/` tutorial and adoption guide; `tests/` foundation, integration, regression and fixtures; `requirements-test.txt`; `.github/workflows/tests.yml`; this generated report. Use `git status --short` and `git ls-files --others --exclude-standard` for the exact working-tree inventory. Test caches are ignored.

## Residual limits and next authority boundary

- macOS full suite verified with CPython 3.13.11/PyYAML 6.0.3. CPython 3.14.7 standard-library subset verified; its full PyYAML-enabled run remains unverified. CPython 3.11 was unavailable locally.
- Native Linux/Windows, Windows junction behavior and hosted CI have not run. Local YAML review is not workflow execution; actionlint was unavailable. These gaps are explicitly permitted by ORG-VAL-004 and remain release-review inputs.
- No Graphify extraction/update or real OKF analysis was run: this source checkout has no Graphify graph or local knowledge bundle, and fixture tests do not need them. Existing adopter graph/OKF freshness and human-review gates remain mandatory when applicable.
- Validators check recorded identities and evidence consistency, not actual actor authentication, policy adequacy, semantic API compatibility or inaccessible remote HEAD currency. Real organizations supply owners, disclosure/retention/residency policy and approval processes.
- Protect coordination and mapped source workspaces against untrusted concurrent modification; V1 is a file-based reviewed workflow, not distributed locking or a remote control plane. Procedure text remains inert until separately reviewed/authorized for execution.
- Tests and one independent skill forward test do not prove every future model decision. Early-stage semantic trace review and human governance remain required.
- Commit/push, release tagging, active local/remote skill installation and real organizational dispatch remain outside this execution approval. Preserve the individual milestone and obtain the user's next instruction before these actions.

Runtime selection references: [Python supported versions](https://devguide.python.org/versions/), [setup-python v7.0.0](https://github.com/actions/setup-python/releases/tag/v7.0.0), [checkout v7.0.0](https://github.com/actions/checkout/releases/tag/v7.0.0), and [PyYAML 6.0.3](https://pypi.org/project/PyYAML/6.0.3/). Checked during task 19; the CI file pins the reviewed action release versions.

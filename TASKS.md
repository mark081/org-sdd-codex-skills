---
title: Organizational SDD implementation plan
document_id: ORG-SDD-TASKS
version: 0.1.0
status: approved
approved_at: 2026-09-07
created: 2026-09-07
updated: 2026-09-07
requirements_version: 0.1.0
design_version: 0.1.0
approvals:
  - artifact_version: 0.1.0
    approved_at: 2026-09-07
    source: Explicit user approval in this conversation
---

# Implementation Plan: Organizational SDD Coordination

## Overview

Implement the approved optional organizational layer in `sdd-codex-skills`: one new skill, integration with four existing skills, versioned contracts and templates, a read-only validator, regression tests, and a three-team tutorial. The plan contains 20 bounded leaf tasks in 17 sequential waves. All tasks are mandatory; execution was authorized on 2026-09-07.

## Execution Contract

- The root integration owner alone updates task checkboxes and completion evidence. Implementers edit only their assigned surfaces, read the approved REQUIREMENTS.md and DESIGN.md, and inspect the worktree before editing.
- Execute only after explicit approval of this TASKS.md. Before each task, confirm listed dependencies and prior waves are complete. Tasks within one wave have disjoint ownership; concurrency is optional and does not itself authorize agent spawning.
- Honor the installed `execute-task-waves` skill during execution and `skill-creator` when creating or changing skills. Read applicable instructions before acting.
- All commands below run from the skills repository root. `python3` denotes the selected Python interpreter; use `python` on Windows where appropriate. Test modules named below are deliverables of their assigned tasks, not claims that they already exist.
- Every leaf must add its tests alongside implementation, run its exact checks, and report exit codes, covered requirement IDs, changed files, and residual risks. Root records evidence before marking complete. Narrow tests do not replace task 20's integration checks.
- Shared package initialization, fixture helpers, contracts, CI, and documentation indexes have one owner at a time. Do not alter another task's files without returning coordination to root; serialize any discovered overlap.
- Scope drift or changes to approved behavior return to the affected specification gate. Missing adopter policies block deployment, not neutral tooling; never invent approval, permissions, or organization-specific defaults.
- No task authorizes remote dispatch, deployment, publication, changing the `individual-complete` tag, or installation into active local/remote skill directories. These require explicit authorization outside the plan.
- Preserve existing Graphify/OKF review and freshness ordering, local task ownership, and optional Ponytail lite/full/off behavior. No secrets, private source content, or private chain-of-thought in reports.

## Tasks

- [x] 1. Define organizational record and reference contracts
  - Owner/surfaces: contract owner; `coordinate-org-sdd/contracts/records.md` and `references.md` only.
  - Dependencies: none. Define exact required/conditional fields, enums, unique IDs, unresolved-value representation, canonical JSON and raw-byte digests, local participation, source references, and safe paths. Specify policy digest projection and scope digests without self-referential approval/evidence cycles.
  - Acceptance: all six record kinds plus participation and repo-map formats are specified with draft and approved examples; examples are illustrative; unsupported versions and malformed fields have defined diagnostics.
  - Verification: `git diff --check`; record a field-by-field review against DESIGN.md Data Models and all required source/provenance minimums.
  - _Requirements: ORG-CORE-002, ORG-CORE-003, ORG-CORE-004, ORG-CON-001, ORG-SEC-001, ORG-SEC-002_
  - Completion evidence (2026-09-07): created `coordinate-org-sdd/contracts/records.md` and `references.md`; field-by-field design reviews recorded in each document. Inline Python JSON/link check parsed all 5 fenced examples, checked digest lengths and local contract links (passed). `python3 spec-to-task-plan/scripts/validate_spec.py --project . --stage all` passed; `python3 spec-to-task-plan/scripts/validate_task_graph.py TASKS.md` passed (17 waves, 20 tasks); `git diff --check` passed. `git diff --no-index --check /dev/null coordinate-org-sdd/contracts/records.md` and the corresponding `references.md` command emitted no whitespace diagnostics (exit 1 denotes new-file differences). No executable validator, Graphify graph or OKF bundle exists for this wave; runtime/schema enforcement remains downstream. Editorially corrected seven record kinds to six to match the approved design; no scope change.

- [x] 2. Define gates, dependency rules, and validation interface
  - Owner/surfaces: contract owner; `coordinate-org-sdd/contracts/readiness.md` and `cli.md` only.
  - Dependencies: 1. Specify stage nodes/edges, intrinsic precedence, effective approval/supersession, compatibility resolution, local/integration/release predicates, publication conditions, impact propagation, and all CLI flags/exit codes from DESIGN.md.
  - Acceptance: every predicate identifies inputs and failure codes; draft validity is separate from readiness; approvals and release-scope digests do not depend on their own approval records. Contract review checkpoint confirms no semantic deviation from approved design before implementation.
  - Verification: `git diff --check`; manually evaluate a stage-specific cycle, conflicting approval, inaccessible source, and changed contract against the written rules, recording expected outcomes.
  - _Requirements: ORG-CORE-004, ORG-CORE-005, ORG-CON-002, ORG-CON-003, ORG-CON-004, ORG-CON-005, ORG-CON-006, ORG-VAL-001, ORG-VAL-002_
  - Completion evidence (2026-09-07): `contracts/readiness.md` and `contracts/cli.md` define predicates, failures, explicit evaluation time and candidate filtering. Root reviewed consistency with DESIGN.md and non-circular approval bootstrap; retained release projection with independent transitive evidence checks. Four documented manual scenarios cover cycles, approval conflict, inaccessible source and contract drift. `git diff --check`, specification validation `--stage all`, and task graph validation passed; runtime enforcement remains downstream.

- [x] 3. Build strict parsing and structural validation
  - Owner/surfaces: foundation owner; `coordinate-org-sdd/src/org_sdd/{__init__,records,diagnostics}.py`, `tests/__init__.py`, `tests/org_helpers.py`, `tests/test_org_records.py`.
  - Dependencies: 1, 2. Implement strict JSON loading, field validation, enum/version/ID checks and structured diagnostics. Establish shared synthetic fixture builders and test import setup; avoid executing input commands.
  - Acceptance: valid drafts parse; duplicate keys/IDs, nonfinite values, unknown kinds/versions, malformed fields and references fail with stable field diagnostics; shared fixture interfaces documented for downstream tests.
  - Verification: `python3 -m unittest tests.test_org_records -v`; `git diff --check`.
  - _Requirements: ORG-CORE-003, ORG-VAL-001, ORG-VAL-003, ORG-SEC-002_
  - Completion evidence (2026-09-07): foundation records/diagnostics modules and synthetic helpers implemented; strict nested schemas, contained control loading, all six directory kinds, source approval consistency and supersession identity/cycles reviewed. `python3 -m unittest tests.test_org_records -v` and `python3 -m unittest discover -s tests -v` pass 17 tests; `git diff --check` passes. Root independently checked malformed JSON/kinds and unsafe paths; discovery-import and lone-surrogate issues corrected before acceptance. Source reads, hashes and readiness remain downstream.

- [x] 4. Implement digest and safe source resolution
  - Owner/surfaces: reference owner; `coordinate-org-sdd/src/org_sdd/references.py`, `tests/test_org_references.py`.
  - Dependencies: 3. Implement canonical record hashing, byte hashing, contained path resolution, explicit repo maps, commit/snapshot identity, and unresolved remote references. Git subprocesses use argument vectors, bounded execution, and no shell interpolation.
  - Acceptance: digest changes are detected; traversal, absolute-path abuse, symlink escapes and command-like input cannot access unauthorized paths or execute code; pinned historical evidence is not represented as remote latest state.
  - Verification: `python3 -m unittest tests.test_org_references -v`; `git diff --check`.
  - _Requirements: ORG-CORE-004, ORG-VAL-001, ORG-VAL-002, ORG-SEC-001, ORG-SEC-002_
  - Completion evidence (2026-09-07): references.py supplies canonical/raw hashes, policy/release projections, participation/map validation and contained source reads. `python3 -m unittest tests.test_org_references -v` passes 8 tests; full discovery passes 25; `git diff --check` passes. Root reviewed bounded argv Git reads, environment isolation, snapshot containment and byte identity; no network or artifact writes. Partial stores/external alternates fail closed; owners can supply authorized snapshots. Release evidence selection remains downstream.

- [x] 5. Implement effective approval and change-impact evaluation
  - Owner/surfaces: approval owner; `coordinate-org-sdd/src/org_sdd/approvals.py`, `tests/test_org_approvals.py`.
  - Dependencies: 4. Evaluate exact target/policy/reference digests, required role coverage, explicit supersession, rejected/revoked records, and transitive changed-reference impact.
  - Acceptance: timestamps never resolve contradictory approvals; unknown owners/policies block affected gates; target/policy/dependency mutation invalidates affected approvals; no actor authentication is claimed.
  - Verification: `python3 -m unittest tests.test_org_approvals -v`; `git diff --check`.
  - _Requirements: ORG-CORE-002, ORG-CORE-004, ORG-CORE-005, ORG-CON-002, ORG-VAL-002_
  - Completion evidence (2026-09-07): approvals.py implements gate-scoped role/owner/target/policy checking and changed-reference impact. `python3 -m unittest tests.test_org_approvals -q` passes 11; full discovery passes 36; `git diff --check` passes. Root review corrected stale historical veto, unrelated-role authority and unchecked approval provenance; bootstrap scope approval excludes future completion evidence. Runtime stage/evidence semantics remain tasks 6–8; evaluator checks recorded authority consistency, not authentication.

- [x] 6. Implement stage dependency graph evaluation
  - Owner/surfaces: graph owner; `coordinate-org-sdd/src/org_sdd/graph.py`, `tests/test_org_graph.py`.
  - Dependencies: 5. Resolve stage edges with intrinsic precedence; detect cycles/dangling refs; compute prerequisite order and affected components using deterministic diagnostics.
  - Acceptance: contract-approved planning can precede provider implementation; implementation dependencies cannot be satisfied by contract approval; independent nodes remain distinguishable from blocked components.
  - Verification: `python3 -m unittest tests.test_org_graph -v` including bounded generated DAG/cycle cases; `git diff --check`.
  - _Requirements: ORG-CON-003, ORG-CON-004, ORG-VAL-003_
  - Completion evidence (2026-09-07): graph.py implements intrinsic/authored stage edges, iterative SCC detection, descendant blocking and deterministic topological order. Named graph suite passes 6; full discovery passes 42; `git diff --check` passes. Root independently compared 100 seeded random stage graphs to a brute-force cycle oracle (passed). Graph order alone grants no readiness; approval/evidence checks remain downstream.

- [x] 7. Implement compatibility, evidence, and knowledge predicates
  - Owner/surfaces: evidence owner; `coordinate-org-sdd/src/org_sdd/evidence.py`, `tests/test_org_evidence.py`.
  - Dependencies: 6. Check changed-contract compatibility/migration evidence, source/check identity and outcomes, required knowledge review, and publication disposition.
  - Acceptance: compatible/breaking/unknown cases require specified evidence; missing, failed, stale, mismatched or illustrative evidence cannot satisfy production conditions; pending publication is never reported as successful synchronization.
  - Verification: `python3 -m unittest tests.test_org_evidence -v`; `git diff --check`.
  - _Requirements: ORG-CON-001, ORG-CON-002, ORG-CON-006, ORG-SKL-005, ORG-SEC-001_
  - Completion evidence (2026-09-07): evidence.py checks exact check/source/contract baselines, compatibility and approved resolutions, canonical prior snapshots, explicit knowledge expiry, and separate publication predicates. Named evidence suite passes 8; full discovery passes 50; `git diff --check` passes. Root reviewed no self-referential baseline hashing or publication-before-local-completion dependency. Publication matches declared source/OKF/contract identities and reviewed attachments; not_required references an explicit scoped decision ID. Semantic adequacy and remote truth remain owner-review responsibilities.

- [x] 8. Compose readiness and local-task eligibility
  - Owner/surfaces: readiness owner; `coordinate-org-sdd/src/org_sdd/readiness.py`, `tests/test_org_readiness.py`.
  - Dependencies: 7. Compose planning, execution, local completion, integration and release predicates; evaluate handoff-scoped task mappings against supplied local-wave candidates without modifying the existing wave resolver.
  - Acceptance: local completion never implies integration/release; global structural corruption blocks actionable readiness; a blocked task cannot admit later-wave work; valid independent same-wave candidates remain visible; authored completion status cannot override missing evidence.
  - Verification: `python3 -m unittest tests.test_org_readiness -v`; `git diff --check`.
  - _Requirements: ORG-CON-005, ORG-CON-006, ORG-SKL-003, ORG-SKL-004, ORG-VAL-001, ORG-VAL-002_
  - Completion evidence (2026-09-07): readiness.py composes staged predicates and current-wave intersection. Named suite passes 13; full discovery passes 63; `git diff --check` passes. Root reviewed passing synthetic release path, exact local IDs, participant ownership, obligation-bound edge evidence, incomplete-local currency and topological evaluation of a 1,050-handoff chain. Contract checks join integration closure without blocking initial planning. Local project validators remain explicitly required; organizational readiness is not dispatch authority.

- [x] 9. Expose read-only validator and digest CLI
  - Owner/surfaces: CLI owner; `coordinate-org-sdd/scripts/validate_org.py`, `tests/test_org_cli.py`.
  - Dependencies: 8. Connect structure/readiness modes, scope selection, explicit repo maps, JSON/text reporting, illustrative opt-in, and shared digest helper. Keep package import resolution independent of caller cwd.
  - Acceptance: exit codes 0/1/2/3 match the contract; stable output states evaluated baseline and scope; no network access, artifact writes, test execution or secret content in diagnostics; isolated installed skill directory runs independently of repository-level imports.
  - Verification: `python3 -m unittest tests.test_org_cli -v`; `python3 coordinate-org-sdd/scripts/validate_org.py --help`; `git diff --check`.
  - _Requirements: ORG-VAL-001, ORG-VAL-002, ORG-VAL-004, ORG-SEC-002_
  - Completion evidence (2026-09-07): CLI named suite passes 8; full discovery passes 71; `validate_org.py --help` exits 0; `git diff --check` passes. Root reviewed mode/exit semantics, explicit coordination-root for nested initiatives, digest error shape, blocked-candidate text, malformed artifact vs repo-map precedence, no input writes and isolated-skill execution. Integration owner corrected task8 empty-scope integration to check scope/provenance explicitly; regression passes. Runtime checkpoint passed before skill consumption.

- [x] 10. Ship unapproved artifact templates
  - Owner/surfaces: template owner; `coordinate-org-sdd/templates/`, `tests/test_org_templates.py`.
  - Dependencies: 9. Supply each record, participation, and repo-map template with documented substitution rules and no fictional production approval. Use explicit unresolved decisions rather than unsafe default policies.
  - Acceptance: instantiated synthetic templates pass structure validation and remain blocked until required evidence and approvals are supplied; approval templates cannot manufacture actor identity or readiness.
  - Verification: `python3 -m unittest tests.test_org_templates -v`; `git diff --check`.
  - _Requirements: ORG-CORE-003, ORG-CORE-005, ORG-VAL-003_
  - Completion evidence (2026-09-07): eight JSON starters and template README added. Template suite passes 3; full discovery passes 74; `git diff --check` passes. Synthetic instantiation validates structure but stays blocked in production and illustrative modes; raw approval decision/actor/time/digests remain uninstantiated placeholders. Root verified substitutions, nonapproval defaults and resolvable links; removed wording-only assertions in favor of actual artifact behavior checks per skill-creator.

- [x] 11. Create the coordination skill and operational reference
  - Owner/surfaces: skill owner; `coordinate-org-sdd/SKILL.md`, `agents/openai.yaml`, `references/operations.md`, `tests/test_org_skill.py`.
  - Dependencies: 10. Use `skill-creator`; document initialize/inspect/resume/reconcile, manual handoffs, ownership and authority checks, installation discovery, explicit gates, failure recovery and minimal sharing.
  - Acceptance: skill is self-contained; each operation defines input/output/stop behavior; no automatic cross-repository writes or approvals; validation and tool absence have actionable manual alternatives without bypassing gates.
  - Verification: `python3 -m unittest tests.test_org_skill -v`; run the skill-creator validation command prescribed by the installed skill and record it; `git diff --check`.
  - _Requirements: ORG-CORE-001, ORG-CORE-002, ORG-CORE-005, ORG-CORE-006, ORG-SEC-001, ORG-SEC-002_
  - Completion evidence (2026-09-07): skill suite passes 3; full suite passes 77; `uv run --offline --with pyyaml python /Users/mark/.codex/skills/.system/skill-creator/scripts/quick_validate.py coordinate-org-sdd` passes; `git diff --check` passes. Independent isolated three-repository forward test created only an illustrative draft initiative and manual handoff README, preserved participant files, and stopped for missing owner/policy decisions. Root confirmed structure exit 0 and readiness exit 2; no approvals, dispatch, publication or installation were fabricated.

- [x] 12. Integrate organizational routing into the lifecycle skill
  - Owner/surfaces: lifecycle owner; `run-sdd-lifecycle/` only, `tests/test_org_lifecycle.py`.
  - Dependencies: 11. Add explicit participation discovery, installed coordination-skill loading and prerequisite checks; distinguish malformed/unavailable context from absent context.
  - Acceptance: absent context retains standalone routing; explicit invalid context blocks affected stages; local approval sequence and one-wave default remain unchanged.
  - Verification: `python3 -m unittest tests.test_org_lifecycle -v`; `git diff --check`.
  - _Requirements: ORG-SKL-001, ORG-VAL-005_
  - Completion evidence (2026-09-07): lifecycle pointer helper and conditional routing added; named suite passes 8. Root reviewed absent versus invalid context, contained pointers, nonadjacent installed coordinator, baseline mismatch, and pointer validity distinct from readiness. Usage/tool-unavailable exit semantics corrected before acceptance. Combined suite with cached PyYAML passes 99; skill metadata validation and `git diff --check` pass. No local gate or wave resolver changes.

- [x] 13. Integrate organizational boundary knowledge into brownfield analysis
  - Owner/surfaces: brownfield owner; `analyze-brownfield-context/` only, `tests/test_org_brownfield.py`.
  - Dependencies: 11. Add provenance-preserving ownership, contract and external-dependency references; document refresh and outgoing organizational update preparation.
  - Acceptance: Graphify inference remains subordinate to verified sources and owner-approved contracts; existing diff-before-manifest and initial/material review gates remain; unavailable private context remains unresolved.
  - Verification: `python3 -m unittest tests.test_org_brownfield -v`; `git diff --check`.
  - _Requirements: ORG-SKL-002, ORG-SKL-005, ORG-SEC-001, ORG-VAL-005_
  - Completion evidence (2026-09-07): organizational boundary reference and conditional skill routing added; `uv run --offline --with pyyaml python -m unittest tests.test_org_brownfield -v` passes 7; combined suite passes 99. Root reviewed unchanged producer schema, external drift independent of local fingerprint, restricted evidence, manifest ordering and pending publication. Metadata validation and `git diff --check` pass. System Python lacks PyYAML; cached dependency runtime used, not a skipped check. No Graphify invocation required for synthetic fixtures.

- [x] 14. Integrate organizational traceability into specification planning
  - Owner/surfaces: specification owner; `spec-to-task-plan/` only, `tests/test_org_planning.py`.
  - Dependencies: 11. Document and validate local obligation-to-requirement/design/task mappings and revision refs where participation is explicit; preserve standalone validator interfaces.
  - Acceptance: stale or conflicted handoffs are surfaced before affected gates; omitted obligations cannot silently pass; explicit approved non-applicability differs from unresolved scope; local root filenames and three approvals remain.
  - Verification: `python3 -m unittest tests.test_org_planning -v`; `git diff --check`.
  - _Requirements: ORG-SKL-003, ORG-VAL-005_
  - Completion evidence (2026-09-07): conditional planning reference and approval/artifact links added; planning suite passes 7; combined suite passes 99; `git diff --check` passes. Root reviewed complete obligation coverage, approved non-applicability, conflict/drift handling, unchanged standalone CLI and separate early-stage semantic review. Historical intake initiative/handoff snapshots explicitly avoid reciprocal content-hash cycles; current participation and contract pins are checked separately. Full execution trace validation does not require future approvals merely to draft requirements.

- [x] 15. Integrate prerequisite checks and evidence handoffs into execution
  - Owner/surfaces: execution owner; `execute-task-waves/` only, `tests/test_org_execution.py`.
  - Dependencies: 12, 13, 14. Add organizational readiness check before affected waves; preserve local wave selection; document completion evidence, graph/OKF reconciliation, outgoing metadata review and publication state.
  - Acceptance: blocked dependencies cannot execute; root alone edits local task status; evidence binds tested revisions; integration is not required to claim verified local implementation; organizational currency still respects required publication/review. Ponytail defaults/controls unchanged.
  - Verification: `python3 -m unittest tests.test_org_execution -v`; `git diff --check`.
  - _Requirements: ORG-SKL-004, ORG-SKL-005, ORG-CON-005, ORG-VAL-005_
  - Completion evidence (2026-09-07): execution reference uses existing local resolver and separate organizational CLI; named suite passes 5, full suite with cached PyYAML passes 104. Root independently verified scoped eligibility, stable approved snapshots versus live bookkeeping, local review/publication separation, and unchanged Ponytail section; next_wave.py unchanged. Metadata and `git diff --check` pass. Cross-reference review also clarified observed snapshot identity in brownfield documentation. All four integration checks passed before example work.

- [x] 16. Build and verify the three-team example snapshots
  - Owner/surfaces: example owner; `examples/three-team/`, `tests/test_org_example.py`.
  - Dependencies: 15. Create Catalog, Checkout and Analytics handoffs with draft, approved-contract, blocked execution, local completion, contract change/migration, integration, release and refreshed-knowledge snapshots using synthetic source attachments.
  - Acceptance: every snapshot has expected structure/readiness outcomes and exact validation invocation; illustrative evidence fails production readiness and is visibly labeled when explicitly enabled; no real owner approvals or sensitive sources.
  - Verification: `python3 -m unittest tests.test_org_example -v`; `git diff --check`.
  - _Requirements: ORG-DOC-001, ORG-CON-002, ORG-CON-005, ORG-SKL-005, ORG-VAL-003_
  - Completion evidence (2026-09-07): nine concrete snapshots, synthetic source attachments, manifest, deterministic builder and read-only runner added. Root independently ran example suite: 5 tests passed, covering 27 structure/demo/production scenarios and 18 local specification/graph/wave commands; all nine manifest readiness invocations matched expected exits. Reviewed Catalog API and defined Analytics event, breaking migration, pending publication, separate release approval and refreshed supersession. Builder symlink escape rejected; raw-byte Git attributes verified. PowerShell 7.7 preview on macOS ran release-demo command successfully (not Windows verification). `git diff --check` passed; no Graphify or actual implementation procedures executed.

- [x] 17. Write tutorial, adoption guidance, and five-skill installation instructions
  - Owner/surfaces: documentation owner; `README.md`, `docs/organizational-sdd-tutorial.md`, `docs/organizational-sdd-adoption.md`, `tests/test_org_docs.py`.
  - Dependencies: 16. Explain both layers and each example step with expected output, prompts, gate stops, recovery, incremental participation and safe departure. Add POSIX/PowerShell installation/update instructions with existing-destination protection.
  - Acceptance: all five skill paths and shipped examples resolve; no claimed automated remote work; Graphify/graphifyy remains brownfield-only and Ponytail optional; copy/junction/link update behavior and skill reload are explained.
  - Verification: `python3 -m unittest tests.test_org_docs -v`; manually walk through documented example commands and record outputs; `git diff --check`.
  - _Requirements: ORG-DOC-001, ORG-DOC-002, ORG-DOC-003, ORG-VAL-004_
  - Completion evidence (2026-09-07): README and tutorial/adoption guides added; root independently ran documentation suite (14 tests, 13 passed, one native-Windows junction skip). Tests execute actual tutorial commands and isolated POSIX/PowerShell installers, check five-destination preflight, existing files/directories/broken links, copy independence and local links. All nine snapshot invocations match documented exits 2,0,2,0,2,0,0,0,0. Root reviewed gate stops, safe departure, update/reload behavior, Graphify/Ponytail boundaries and snapshot semantics; `git diff --check` passes. PowerShell 7.7 preview on macOS tested, not native Windows. Runtime selection belongs to task 19.

- [x] 18. Add standalone regression fixtures and adversarial integration tests
  - Owner/surfaces: regression owner; `tests/fixtures/`, `tests/test_individual_regression.py`, `tests/test_org_integration.py`.
  - Dependencies: 16. Exercise existing spec/task-graph/wave/brownfield validators and the complete organizational CLI, including malformed input, restricted sources, stale policy, revision drift, cycles and illustrative evidence isolation.
  - Acceptance: existing interfaces pass standalone fixtures with no organizational setup; negative cases fail for the intended reason; task eligibility cannot bypass a local gate; core tests need neither Graphify nor credentials/network.
  - Verification: `python3 -m unittest tests.test_individual_regression tests.test_org_integration -v`; `git diff --check`.
  - _Requirements: ORG-VAL-001, ORG-VAL-002, ORG-VAL-003, ORG-VAL-005, ORG-SEC-001, ORG-SEC-002_
  - Completion evidence (2026-09-07): five standalone fixture files plus standalone/adversarial suites added; root independently ran `uv run --offline --with pyyaml python -m unittest tests.test_individual_regression tests.test_org_integration -q` (12 passed). Reviewed real CLI checks for malformed unselected records, policy/source drift, restricted roots, traversal/symlinks, inert executable text, cycles and production isolation. Existing local validators remain required even when historical organizational baseline passes. Read-only input comparisons pass; `git diff --check` passes. Legacy all-checkboxes-complete specification-validator limitation is explicitly tested, not changed.

- [x] 19. Configure platform test matrix and declared runtime support
  - Owner/surfaces: integration owner; `.github/workflows/tests.yml`, test dependency declaration if needed, runtime support section in README.md.
  - Dependencies: 17, 18. Select/document minimum Python and a current supported test version; configure macOS/Linux/Windows runs of the standard unittest suite with existing validators' dependencies. Read current primary runtime/platform documentation if version selection requires it.
  - Acceptance: matrix covers all declared OSes and Python boundaries; commands do not install Graphify for core tests or require production secrets. Local configuration validation is distinguished from actual hosted CI results.
  - Verification: `python3 -m unittest discover -s tests -v`; parse/review workflow YAML against declared matrix; `git diff --check`. Record unavailable platforms as gaps; do not publish merely to trigger CI.
  - _Requirements: ORG-VAL-003, ORG-VAL-004, ORG-DOC-002_
  - Completion evidence (2026-09-07): six-job macOS/Linux/Windows × Python 3.11/3.14 workflow and pinned `requirements-test.txt` added; README declares runtime/dependency boundaries and gaps. Official Python version status and action release pages checked. YAML matrix/triggers/read-only permissions/credential settings parsed and independently reviewed. Full suite on Python 3.13.11/PyYAML 6.0.3: 135 tests, 134 passed, one Windows junction skip. Native Python 3.14.7 standard-library subset: 124 tests, 123 passed, one skip; full 3.14 offline run lacked cached PyYAML. Python 3.11 and hosted/native Windows/Linux runs unavailable; no CI success claimed. Returned silent symlink test omission to reference owner for explicit skip correction. `git diff --check` passes; actionlint unavailable, configuration review is not hosted execution.

- [x] 20. Complete integration verification and requirement coverage report
  - Owner/surfaces: root integration owner; `.sdd/reports/organizational-sdd-verification.md` and TASKS.md completion evidence only. Return discovered implementation defects to the owning leaf rather than silently expanding this task.
  - Dependencies: 19. Run all validators, automated tests, skill metadata checks, documentation checks and three-team walkthrough. Map all 27 requirements and design properties P1–P12 to checks/results; inspect final diff for authority/privacy regressions.
  - Acceptance: all mandatory checks pass or task remains incomplete with the exact failure. Record platform/environment gaps explicitly as permitted by requirements. Report artifact versions, baseline, exact commands/results, changed files, residual risks and separate publication/install approval needs; do not call unrun hosted CI successful.
  - Verification: `python3 -m unittest discover -s tests -v`; `python3 spec-to-task-plan/scripts/validate_spec.py --project . --stage all`; `python3 spec-to-task-plan/scripts/validate_task_graph.py TASKS.md`; `git diff --check`; metadata and walkthrough commands from tasks 11 and 17. Run task graph validation before the final checkbox changes because the existing spec validator expects unchecked tasks.
  - _Requirements: ORG-CORE-001, ORG-CORE-002, ORG-CORE-003, ORG-CORE-004, ORG-CORE-005, ORG-CORE-006, ORG-CON-001, ORG-CON-002, ORG-CON-003, ORG-CON-004, ORG-CON-005, ORG-CON-006, ORG-SKL-001, ORG-SKL-002, ORG-SKL-003, ORG-SKL-004, ORG-SKL-005, ORG-VAL-001, ORG-VAL-002, ORG-VAL-003, ORG-VAL-004, ORG-VAL-005, ORG-DOC-001, ORG-DOC-002, ORG-DOC-003, ORG-SEC-001, ORG-SEC-002_
  - Completion evidence (2026-09-07): `.sdd/reports/organizational-sdd-verification.md` records baseline, artifact versions, exact checks, all 27 requirements/P1–P12 coverage, walkthrough and residual platform/authority limits. Final pinned offline full suite: 135 tests, 134 passed, one native-Windows junction skip; all five skill metadata checks passed. Root specification validation passed before this final checkbox; task graph passed 17 waves/20 tasks. All nine tutorial outcomes and protected installer checks passed; tracked and all 320 new-file whitespace checks passed. Original standalone validator scripts, license/notice, HEAD and individual milestone tag unchanged. Python 3.14 standard-library subset passed; full 3.14, minimum Python 3.11 and native Windows/Linux/hosted CI gaps remain explicitly documented as permitted by ORG-VAL-004. No push, release or active skill installation performed.

## Integration and Governance Checkpoints

- Before task 1: explicit task-plan approval. Earlier approvals permit planning only.
- After task 2: root checks contract consistency with approved design. Material changes require renewed design and task approval, not an invented policy decision.
- After task 9: foundational validator tests pass before skills consume its readiness result.
- After task 15: all four integrations pass their checks before the tutorial presents an end-to-end workflow.
- Task 20: repository-wide verification and evidence review. A tool failure or unresolved implementation defect is not waived by task completion pressure.
- Actual adopter initiative, contract, local specification, integration and release approvals are separate gates in the shipped workflow; synthetic examples never satisfy them.
- After implementation: commit/push, release tagging, and active skill installation follow explicit user authorization. Preserve the individual milestone tag.

## Notes

No tasks are optional. Tasks remain unchecked until verified. Dependencies in task bodies are mandatory and are placed in earlier waves; the graph below supplies the existing wave resolver's sequential scheduling format. Additional wave ordering intentionally serializes shared integration surfaces even where a direct dependency is absent.

Tasks 12–14 can be performed independently after task 11; tasks 17–18 can be performed independently after task 16. No other same-wave concurrency is planned. Shared helper changes during those waves require root integration and serialization.

Preserve existing behavior rather than silently repairing unrelated limitations. In particular, the current specification validator requires at least one unchecked task: capture final specification validation before marking task 20 complete, then use the task graph validator and wave resolver to verify completed scheduling state. Report this limitation instead of weakening validation without scope review.

## Task Dependency Graph

```json
{
  "waves": [
    {"id": 0, "tasks": ["1"]},
    {"id": 1, "tasks": ["2"]},
    {"id": 2, "tasks": ["3"]},
    {"id": 3, "tasks": ["4"]},
    {"id": 4, "tasks": ["5"]},
    {"id": 5, "tasks": ["6"]},
    {"id": 6, "tasks": ["7"]},
    {"id": 7, "tasks": ["8"]},
    {"id": 8, "tasks": ["9"]},
    {"id": 9, "tasks": ["10"]},
    {"id": 10, "tasks": ["11"]},
    {"id": 11, "tasks": ["12", "13", "14"]},
    {"id": 12, "tasks": ["15"]},
    {"id": 13, "tasks": ["16"]},
    {"id": 14, "tasks": ["17", "18"]},
    {"id": 15, "tasks": ["19"]},
    {"id": 16, "tasks": ["20"]}
  ]
}
```

# Validator correctness and optimization verification

Baseline: `dbda8cd` on `mark081/org-sdd-codex-skills/main`.
Scope: six review findings explicitly authorized for implementation by the user.
No publication, active skill installation, or remote-host changes performed.
Historical approved milestone documents and task completion records are unchanged.

## Changes and coverage

| Finding | Implementation | Requirement coverage |
| --- | --- | --- |
| Omitted tasks falsely complete | Graph validator and wave resolver require every leaf exactly once; duplicate declarations fail; dotted ancestors are documented groups | ORG-SKL-004, ORG-VAL-003, ORG-VAL-005 |
| Windows frontmatter failure | Accept LF/CRLF delimiters without changing source bytes; explicit byte-preservation regression | ORG-VAL-004, ORG-SKL-002 |
| Repeated source reads | Success-only, evaluation-local cache keyed by authorized root, mapping basis and full source identity; snapshot hits recheck containment and file metadata | ORG-VAL-001, ORG-CORE-004, ORG-SEC-002 |
| Repeated scans/hashes | Per-evaluation role/gate/check/approval/evidence indexes and lazy validated record/policy digests; no cached approval decisions | ORG-VAL-001, ORG-CORE-004 |
| Completed plan rejected | Explicit `validate_spec.py --completed`, limited to tasks/all; default planning behavior retained | ORG-VAL-005, ORG-DOC-002 |
| Quadratic duplicate detection | Counter-based scheduled/declaration duplicate checks; 5,000-task regression | ORG-VAL-001, ORG-VAL-003 |

Changed surfaces: README; brownfield validator; organizational approvals, evidence,
readiness and reference modules; wave resolver and execution protocol; planning
skill, artifact contract and validators; individual, brownfield, source-reference
and optimization tests; this report.

## Verification

From the repository root:

- `uv run --offline --python 3.13 --with pyyaml==6.0.3 python -m unittest discover -s tests -q`
  — 145 tests, 144 passed, one native-Windows junction skip (20.667 seconds).
- `python3 spec-to-task-plan/scripts/validate_spec.py --project . --stage all --completed`
  — passed against the completed historical plan.
- `python3 spec-to-task-plan/scripts/validate_task_graph.py TASKS.md`
  — passed, 17 waves / 20 scheduled tasks.
- `python3 execute-task-waves/scripts/next_wave.py TASKS.md`
  — complete, no remaining tasks.
- `uv run --offline --python 3.13 --with pyyaml==6.0.3 python /Users/mark/.codex/skills/.system/skill-creator/scripts/quick_validate.py spec-to-task-plan`
  — valid skill metadata.
- `git diff --check` — passed.
- `python3 -m tests.test_org_optimization --benchmark`
  — 25 evaluations per variant of the synthetic three-team release fixture:
  uncached median 53.81 ms / 281 source reads; cached median 25.76 ms / 19 reads.
  This is a local example measurement, not an organizational throughput guarantee.

Regression coverage compares complete cached/uncached reports for breaking,
migration, release and refreshed-knowledge snapshots. Further tests cover changed
policy/contract/approval between calls, changed/deleted snapshot files, symlink
escape after a cache hit, Git digest separation, fresh reads after cache scope
exit, cleanup after exceptions, grouped tasks, omitted leaves, duplicate task
declarations, pending completion rejection and large wave plans.

## Residual boundaries

The full suite ran on macOS, not native Windows/Linux. A separate authorized
native Windows check used Python 3.14 and Windows PowerShell 5.1.20348.5499:
`test_powershell_junctions_all_five`,
`test_powershell_existing_file_preserved_before_any_install`, and
`test_powershell_existing_directory_preserved_before_any_install` all passed
(three tests, no skips, 0.654 seconds). The test harness selected the installed
`powershell` executable in place of `pwsh`; installer and assertions were unchanged.
Tests used isolated temporary destinations; active skills were untouched and
temporary test copies were removed. This verifies junctions on native Windows,
not the entire Windows suite or PowerShell 7. CRLF behavior is exercised locally;
the prior Windows CI failure still needs confirmation in a new hosted run.
Existing approval, integration, publication and release gates remain required.

Caches exist only during synchronous readiness evaluation of fixed in-memory
records and mapped Git stores. Callers must not mutate those during the call.
Snapshot metadata checks are not an atomic filesystem transaction or a defense
against a hostile concurrent filesystem writer. New evaluations discard cached
sources and indexes; source contents and approval decisions are never persisted.
No cache establishes the latest state of an inaccessible remote repository.

Planning's default unchecked-work requirement is preserved. Completion mode
still requires separate graph validation and actual implementation evidence.
Unscheduled dotted ancestor checkboxes are grouping metadata; explicitly
scheduled groups remain subject to the wave resolver's completion checks.

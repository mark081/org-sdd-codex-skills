---
name: execute-task-waves
description: Execute an approved TASKS.md implementation plan in dependency order, using parallel subagents for independent tasks within each ready wave, reconciling changes centrally, running verification, and recording completion evidence. Use when the user asks Codex to implement TASKS.md, execute the next task or wave, continue a specification plan, parallelize ready implementation tasks, or run an approved requirements/design/task plan.
---

# Execute Task Waves

Implement an approved task plan safely. Default to one dependency-ready wave per invocation.

## Preconditions

1. Work in the project root and read the nearest `AGENTS.md` completely.
2. Read `REQUIREMENTS.md`, `DESIGN.md`, and `TASKS.md`.
3. Confirm `TASKS.md` is explicitly approved. If approval is not recorded or clear in conversation, stop and ask.
4. Run `python3 scripts/next_wave.py <project-root>/TASKS.md` from this skill directory.
5. Stop if the graph is invalid, earlier tasks are incomplete, required context is missing, or the next item is a human governance checkpoint that is not satisfied.
6. If `.sdd/knowledge/index.md` exists, read it and the concepts relevant to the ready wave. Treat stale, conflicted, inferred, or ambiguous knowledge as evidence needing verification, not as authority.

Read [references/execution-protocol.md](references/execution-protocol.md) before executing a wave.

## Choose scope

- **Default/“continue”**: execute the next ready wave, verify it, update `TASKS.md`, then stop.
- **Specific task/wave**: execute only the requested item if dependencies are complete.
- **“Execute all”**: advance sequentially across waves, stopping at every approval/governance gate, permission request, blocker, failed verification, or user decision. Never launch all waves concurrently.

## Plan the wave

1. Resolve every task in the ready wave and its cited requirements/design properties.
2. Identify likely files, schemas, commands, and shared resources.
3. Build a conflict matrix. Tasks that may edit the same files, migrations, shared interfaces, package manifest, or generated artifacts are not independent.
4. Reserve the primary agent for integration, verification, and `TASKS.md` updates.
5. When subagents are available and the user authorized agent execution, assign at most one independent leaf task per subagent, bounded by available concurrency. Serialize conflicting tasks.
6. When `graphify-out/graph.json` exists, use scoped `graphify query`, `graphify path`, or `graphify explain` calls to confirm affected boundaries and dependencies before editing.

## Execute

- Give each agent the exact task ID, artifact paths, relevant requirements, acceptance criteria, verification, and an explicit instruction not to edit `TASKS.md`.
- Require each agent to inspect existing work, preserve unrelated changes, implement only its task, run focused checks, and return changed files plus evidence.
- Do not allow agents to make product, legal, clinical, privacy, or security policy decisions.
- Keep waves sequential. Do not start a later wave while any current-wave task is incomplete or failing.

## Reconcile and verify

1. Inspect every agent result and the combined diff.
2. Resolve overlaps centrally; do not discard valid user or agent work.
3. Run each task's checks plus repository-wide format, lint, type-check, build, and relevant tests when available.
4. Verify acceptance criteria and requirement coverage. A passing narrow test is not enough when integration is required.
5. If code changed and a Graphify graph exists, run `graphify update .` before accepting the wave. If the CLI is unavailable or update fails, stop without marking affected tasks complete.
6. If `.sdd/knowledge/index.md` exists, follow `$analyze-brownfield-context` update mode for affected concepts. Start from the wave's changed-file list and record an unchanged, revised, or stale/conflicted disposition for every potentially affected concept. Routine internal refactors may require only graph refresh plus verified unchanged dispositions; changes to architecture, interfaces, data, operations, constraints, ownership boundaries, or high-impact dependencies require OKF reconciliation.
7. Validate the brownfield bundle after reconciliation. A material rewrite of a human-confirmed concept remains a pending human documentation gate, and affected implementation tasks stay unchecked until that review succeeds.
8. Only after code verification, graph refresh, OKF reconciliation, bundle validation, and applicable human review succeed, change each completed task from `[ ]` to `[x]` and add `Completion evidence:` with commands and important artifact paths.
9. Mark a checkpoint complete only after its evidence and required human approvals exist.
10. Run `python3 scripts/next_wave.py <project-root>/TASKS.md` again to confirm the next state.

## Stop conditions

Stop and report without marking completion when:

- verification fails;
- dependencies or acceptance criteria are ambiguous;
- a required permission or credential is unavailable;
- a governance checkpoint needs human approval;
- execution would expand scope materially;
- repository changes conflict and cannot be reconciled safely;
- the plan contradicts approved requirements or design.

Report completed tasks, changed files, commands and results, remaining blockers, and the next ready wave.

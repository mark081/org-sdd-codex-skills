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
7. If `.sdd/org/context.json` or equivalent session participation is supplied, read [references/organizational-execution.md](references/organizational-execution.md), load the installed coordinator through the skill catalog, verify the pinned participation/handoff and filter the affected current-wave candidates before assignment. Absent participation retains standalone behavior; invalid or unavailable participation never silently opts out. Organizational readiness does not replace local approval or validation.

Read [references/execution-protocol.md](references/execution-protocol.md) before executing a wave.

## Choose scope

- **Default/“continue”**: execute the next ready wave, verify it, update `TASKS.md`, then stop.
- **Specific task/wave**: execute only the requested item if dependencies are complete.
- **“Execute all”**: advance sequentially across waves, stopping at every approval/governance gate, permission request, blocker, failed verification, or user decision. Never launch all waves concurrently.

## Optional Ponytail mode

Ponytail is an optional implementation-minimization layer, not an execution prerequisite.

1. Use it only when the Ponytail plugin or skill is available, or when the user explicitly requests it. Do not install it without authorization and do not fail execution merely because it is absent.
2. Before the first executable wave, honor any mode the user already selected or configured. Otherwise, when Ponytail is available or requested, ask once for `lite`, `full`, or `off`, presenting `lite` as the recommended default. If the user delegates the choice, select `lite`. Do not ask again for later waves unless the user requests a change.
3. Treat the mode choice as a workflow preference, not an SDD approval or governance gate. It does not expand execution authority.
4. Keep the chosen mode consistent for the primary agent and implementation subagents where the host supports it.

Ponytail may reduce implementation complexity, but it must not remove or weaken approved behavior, acceptance criteria, validation, security, privacy, accessibility, data-loss protection, error handling, evidence, documentation, or governance controls. If a proposed simplification materially changes approved requirements or design, stop and return to the applicable SDD approval stage.

## Plan the wave

1. Resolve every task in the ready wave and its cited requirements/design properties.
2. Identify likely files, schemas, commands, and shared resources.
3. Build a conflict matrix. Tasks that may edit the same files, migrations, shared interfaces, package manifest, or generated artifacts are not independent.
4. Reserve the primary agent for integration, verification, and `TASKS.md` updates.
5. When subagents are available and the user authorized agent execution, assign at most one independent leaf task per subagent, bounded by available concurrency. Serialize conflicting tasks.
6. When `graphify-out/graph.json` exists, use scoped `graphify query`, `graphify path`, or `graphify explain` calls to confirm affected boundaries and dependencies before editing.
7. When Ponytail is active, apply its simplicity ladder only after understanding the affected code and approved task: prefer no new code, existing repository capabilities, standard-library or native-platform features, installed dependencies, and then the minimum new implementation that satisfies the contract.
8. For explicit organizational participation, assign only candidates that pass the relevant handoff's execution prerequisites and the existing local gates. A blocked obligation may leave independent same-wave candidates eligible; do not add candidates or start a later wave while current work remains incomplete.

## Execute

- Give each agent the exact task ID, artifact paths, relevant requirements, acceptance criteria, verification, and an explicit instruction not to edit `TASKS.md`.
- Require each agent to inspect existing work, preserve unrelated changes, implement only its task, run focused checks, and return changed files plus evidence.
- Do not allow agents to make product, legal, clinical, privacy, or security policy decisions.
- Keep waves sequential. Do not start a later wave while any current-wave task is incomplete or failing.

## Reconcile and verify

1. Inspect every agent result and the combined diff.
2. When Ponytail is active and its review capability is available, review the combined diff for unnecessary abstractions, wrappers, dependencies, configuration, and custom code. Treat findings as proposals subject to the approved specification and the safety boundary above; record why any material recommendation is rejected.
3. Resolve overlaps centrally; do not discard valid user or agent work.
4. Run each task's checks plus repository-wide format, lint, type-check, build, and relevant tests when available.
5. Verify acceptance criteria and requirement coverage. A passing narrow test is not enough when integration is required.
6. If code changed and a Graphify graph exists, run `graphify update .` before accepting the wave. If the CLI is unavailable or update fails, stop without marking affected tasks complete.
7. If `.sdd/knowledge/index.md` exists, follow `$analyze-brownfield-context` update mode for affected concepts. Start from the wave's changed-file list and record an unchanged, revised, or stale/conflicted disposition for every potentially affected concept. Routine internal refactors may require only graph refresh plus verified unchanged dispositions; changes to architecture, interfaces, data, operations, constraints, ownership boundaries, or high-impact dependencies require OKF reconciliation.
8. Validate the brownfield bundle after reconciliation. A material rewrite of a human-confirmed concept remains a pending human documentation gate, and affected implementation tasks stay unchecked until that review succeeds.
   - Where participation is configured, prepare reviewed local completion and outgoing organizational knowledge/evidence references as described in [organizational-execution.md](references/organizational-execution.md). Record actual publication disposition separately: verified local implementation need not wait for future integration/release, but missing required local review still blocks completion and pending publication cannot be called synchronized.
9. Only after code verification, graph refresh, OKF reconciliation, bundle validation, and applicable human review succeed, change each completed task from `[ ]` to `[x]` and add `Completion evidence:` with commands and important artifact paths.
10. Mark a checkpoint complete only after its evidence and required human approvals exist.
11. Run `python3 scripts/next_wave.py <project-root>/TASKS.md` again to confirm the next state.

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

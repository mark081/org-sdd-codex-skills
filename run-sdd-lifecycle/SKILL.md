---
name: run-sdd-lifecycle
description: Orchestrate a repository change through brownfield analysis, gated requirements, design, task planning, and dependency-safe execution. Use when the user wants one resumable workflow that coordinates analyze-brownfield-context, spec-to-task-plan, and execute-task-waves without bypassing approvals.
---

# Run SDD Lifecycle

Coordinate the installed SDD skills as one resumable lifecycle. Delegate each stage to its owning skill instead of reproducing or weakening that skill's contract.

## Operating Contract

- Work at the repository root and read the nearest `AGENTS.md` completely.
- Inspect the worktree before acting and preserve unrelated changes.
- Read the current `SKILL.md` for every child skill immediately before using that stage:
  - `$analyze-brownfield-context`
  - `$spec-to-task-plan`
  - `$execute-task-waves`
- Treat repository artifacts as workflow state. Do not create a separate status file that can disagree with `REQUIREMENTS.md`, `DESIGN.md`, `TASKS.md`, or `.sdd/knowledge/`.
- Resume the earliest incomplete, invalid, stale, or unapproved stage. Do not regenerate valid approved artifacts merely because this is a new invocation.
- Never infer one approval from another, approve on the user's behalf, or let an implementation request bypass a required gate.
- Stop at permission requests, failed verification, material scope drift, unresolved blocking decisions, and human governance gates.

## Route the Repository

1. Determine whether this is an existing implementation and whether the requested change is substantial enough to benefit from durable repository context.
2. Use `$analyze-brownfield-context` before specification when any of these apply:
   - the change crosses multiple components or operational boundaries;
   - architecture, interfaces, data, deployment, or high-impact dependencies are not already clear;
   - `.sdd/knowledge/` exists but is stale, conflicted, invalid, or incomplete for the change.
3. Skip brownfield analysis for a genuinely greenfield repository or a narrowly scoped change where direct inspection is sufficient. State that routing decision and its basis.
4. If the knowledge skill requires review of an initial baseline or a material human-confirmed concept change, stop for that review before planning.

## Advance the Lifecycle

### 1. Establish Context

Follow `$analyze-brownfield-context` when routed to it. Continue only after the relevant bundle validates and any required human review is complete. Curated knowledge is evidence, not approved product intent or policy.

### 2. Specify and Plan

Follow `$spec-to-task-plan` from the first incomplete stage. Preserve its three distinct gates:

1. create or revise `REQUIREMENTS.md`, validate it, then stop for requirements approval;
2. after requirements approval, create or revise `DESIGN.md`, validate it, then stop for design approval;
3. after design approval, create or revise `TASKS.md`, validate it, then stop for task-plan approval.

Do not implement product code during these stages.

### 3. Execute

After explicit task-plan approval, follow `$execute-task-waves`.

- Default to its one-ready-wave scope.
- If the user explicitly asks to execute all or continue through completion, advance sequentially across waves, still stopping at every approval, governance, permission, failure, or decision boundary.
- Let the execution skill own Graphify refresh, OKF reconciliation, verification, completion evidence, and authoritative task status updates.
- If implementation reveals a material requirements or design change, stop execution, invalidate affected downstream approval as required by the repository contract, and return to the earliest affected specification stage.

## Invocation Continuity

Interpret a later approval or `continue` request using repository state plus the current conversation:

- an artifact-specific approval advances only that artifact's gate;
- `continue` resumes the earliest eligible stage;
- `execute all` broadens duration, not authority;
- an existing approved plan may proceed directly to execution when its prerequisites remain current;
- completed work is not repeated unless validation or source changes make it stale.

At every stop, report the completed stage, validation or execution evidence, the exact gate or blocker, and the next expected user action. When the lifecycle is complete, report completed tasks, verification results, remaining risks or follow-ups, and repository status.

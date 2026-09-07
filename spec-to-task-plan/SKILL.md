---
name: spec-to-task-plan
description: Convert a product or feature prompt into a gated specification set consisting of REQUIREMENTS.md, DESIGN.md, and TASKS.md. Use when the user asks to define requirements, create a technical design, produce an implementation plan, turn an idea or PRD into executable tasks, or run a requirements-to-design-to-tasks workflow with review and approval between artifacts.
---

# Spec to Task Plan

Create three authoritative artifacts in sequence. Never implement product code with this skill.

## Operating rules

- Work in the project root and honor the nearest `AGENTS.md`.
- Use uppercase filenames exactly: `REQUIREMENTS.md`, `DESIGN.md`, `TASKS.md`.
- Inspect existing artifacts before writing. Resume the first incomplete or unapproved stage.
- Treat edits as new drafts. Require renewed approval after a material edit.
- Ask at most three concise blocking questions at a time. Make clearly labeled, reversible assumptions for non-blocking gaps.
- Do not interpret user approval of one artifact as approval of later artifacts.
- Do not fabricate clinical, legal, regulatory, privacy, security, or organizational policy.
- If the project is regulated or safety-sensitive, make unresolved governance decisions explicit release gates.
- If `.sdd/knowledge/index.md` exists, treat it as curated brownfield context, not as approved requirements or policy. Read the index first, load only relevant linked concepts, preserve their provenance/confidence labels, and verify material claims against source when stale, inferred, ambiguous, or incomplete.

## Brownfield context

Before Stage 1 in an existing repository:

1. Inspect `.sdd/knowledge/index.md` and its linked `bundle-state.md` when present. Compare the recorded revision and source fingerprint with the current repository state, then check relevant concepts for expired `stale_after` or `curation_status: stale|conflicted`.
2. If the bundle is stale or conflicted, recommend `$analyze-brownfield-context` and do not silently treat its claims as current. Continue only when the user accepts clearly labeled direct-inspection assumptions or the context is refreshed.
3. Use the bundle for current-system boundaries, interfaces, data, operations, constraints, glossary, risks, and open questions. Use scoped Graphify queries for focused follow-up when `graphify-out/graph.json` exists.
4. Cite relevant OKF concepts and source evidence in decisions and design rationale. Convert uncertainty or conflicts into explicit assumptions, dependencies, or blocking questions.
5. Apply this authority order: approved requirements and policy; human-confirmed decisions; verified source/configuration facts; curated OKF summaries; Graphify inferences.

Absence of an OKF bundle is not an error. Inspect the repository normally, and recommend `$analyze-brownfield-context` when the change spans multiple subsystems or durable brownfield context would materially improve planning.

Read [references/artifact-contracts.md](references/artifact-contracts.md) before creating or materially revising any artifact. Read [references/approval-protocol.md](references/approval-protocol.md) when advancing stages.

## Organizational handoff (opt-in)

When `.sdd/org/context.json` exists or the user supplies an explicit organizational handoff, read [references/organizational-planning.md](references/organizational-planning.md) before drafting and before each affected approval gate. Preserve obligation/revision traceability in all three local artifacts. Invalid, inaccessible, stale, or conflicting supplied context blocks the affected gate; it is not standalone mode. Without either input, retain the workflow below with no organizational setup or dependency.

## Stage 1: Requirements

1. Translate the prompt into problem, scope, actors, workflow, goals, non-goals, assumptions, decisions, and open questions.
2. Write testable requirements in EARS syntax with stable unique IDs, priority, verification, and acceptance criteria where useful.
3. Add YAML front matter and a glossary. Mark the document `status: draft`.
4. Run `python3 scripts/validate_spec.py --project <project-root> --stage requirements` from this skill directory.
5. Present material assumptions, blocking questions, and validation results.
6. Stop and request explicit approval or edits.
7. On explicit approval, record approval status and date without inventing an approver identity.

Do not create `DESIGN.md` until `REQUIREMENTS.md` is explicitly approved.

## Stage 2: Design

1. Derive the design from the approved requirements and repository constraints.
2. Cover architecture, flows, components/interfaces, data models, persistence, correctness properties, error handling, and testing strategy.
3. Map design properties and tests to requirement IDs. Account for every must-have requirement.
4. Prefer the smallest durable architecture; distinguish v1 implementation from future seams.
5. Run `python3 scripts/validate_spec.py --project <project-root> --stage design`.
6. Present architectural decisions, tradeoffs, unresolved design questions, and validation results.
7. Stop and request explicit approval or edits.

Do not create `TASKS.md` until `DESIGN.md` is explicitly approved.

## Stage 3: Tasks

1. Convert the approved requirements and design into numbered, dependency-aware checkbox tasks.
2. Make leaf tasks executable in one focused agent turn. Include objective/change details, acceptance, verification, and requirement IDs.
3. Add checkpoints for integration and every human governance gate.
4. Add a machine-readable JSON dependency graph under `## Task Dependency Graph`.
5. Add an execution contract requiring evidence before completion and central ownership of task status.
6. Run both validators:
   - `python3 scripts/validate_spec.py --project <project-root> --stage tasks`
   - `python3 scripts/validate_task_graph.py <project-root>/TASKS.md`
7. Present scope, task count, dependency waves, gates, and validation results.
8. Stop and request explicit approval or edits.

Do not begin task execution. Recommend `$execute-task-waves` only after explicit task-plan approval.

## Completion

Finish when all three artifacts exist, validate, and have separate explicit approvals. Report the exact next invocation for implementation.

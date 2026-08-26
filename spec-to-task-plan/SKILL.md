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

Read [references/artifact-contracts.md](references/artifact-contracts.md) before creating or materially revising any artifact. Read [references/approval-protocol.md](references/approval-protocol.md) when advancing stages.

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

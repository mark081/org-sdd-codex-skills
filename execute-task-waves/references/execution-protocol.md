# Execution Protocol

## Coordination model

The primary agent owns:

- dependency and approval checks;
- file-conflict analysis;
- shared contracts and migrations unless explicitly delegated;
- integration and repository-wide verification;
- all `TASKS.md` status and evidence edits;
- user communication and checkpoint approval.

Subagents own one bounded leaf task each. They must not update `TASKS.md`, re-scope another task, or start downstream work.

## Conflict rules

Serialize tasks when they may touch any shared surface:

- package manifests or lockfiles;
- database schema or migration ordering;
- central routing/composition roots;
- shared domain interfaces;
- generated code;
- configuration and CI;
- the same test fixture or snapshot;
- `AGENTS.md`, `REQUIREMENTS.md`, `DESIGN.md`, or `TASKS.md`.

When uncertain, serialize. Parallelism is an optimization, not an objective.

## Subagent assignment template

```text
Execute TASKS.md leaf task <ID> only.

Read AGENTS.md and the cited sections of REQUIREMENTS.md and DESIGN.md. Meet every acceptance criterion and run the listed verification. Inspect existing work first, preserve unrelated changes, and do not implement later tasks.

Do not edit TASKS.md. Do not make unresolved product, legal, clinical, privacy, or security decisions. If blocked, stop and report the exact blocker.

Return: summary, changed files, commands/results, requirement IDs covered, and residual risks.
```

## Completion evidence

Use concise, reproducible evidence:

```markdown
    - Completion evidence: `pnpm typecheck`; `pnpm test -- encounter`; migration `0003_encounters.sql`; requirements DAL-AUTH-002 and DAL-QUA-005 covered.
```

Do not include secrets, PHI, raw prompts, or oversized logs.

## Checkpoints

Automated checkpoints require all listed commands and artifacts. Human governance checkpoints require explicit approval from the named role. Never manufacture sign-off or treat test success as clinical, legal, privacy, or security approval.

## Recovery

On interruption, rerun `next_wave.py`, inspect the worktree and task evidence, and verify partially completed work. Never assume an unchecked task has no changes or a checked task is correct merely because of its checkbox.

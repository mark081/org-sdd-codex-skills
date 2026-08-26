# SDD Codex Skills

Two complementary Codex skills for running a gated Specification-Driven Development workflow:

- **`spec-to-task-plan`** turns a product or feature prompt into separately approved `REQUIREMENTS.md`, `DESIGN.md`, and `TASKS.md` artifacts.
- **`execute-task-waves`** executes an approved `TASKS.md` plan in dependency order, verifies each wave, and records completion evidence centrally.

## Workflow

```text
Product or feature prompt
  → $spec-to-task-plan
  → approve REQUIREMENTS.md
  → approve DESIGN.md
  → approve TASKS.md
  → $execute-task-waves
  → verified implementation waves
```

The planning skill never implements product code. The execution skill requires an explicitly approved task plan and stops at failed verification, missing authority, or human governance gates.

## Install

Clone this repository somewhere durable, then copy or symlink both skill directories into `~/.codex/skills/`:

```sh
git clone https://github.com/mark081/sdd-codex-skills.git
mkdir -p ~/.codex/skills
ln -s "$PWD/sdd-codex-skills/spec-to-task-plan" ~/.codex/skills/spec-to-task-plan
ln -s "$PWD/sdd-codex-skills/execute-task-waves" ~/.codex/skills/execute-task-waves
```

If either destination already exists, inspect and back it up before replacing it. Restart Codex after installation so it reloads the skill catalog.

## Use

Open Codex in a project repository and invoke:

```text
Use $spec-to-task-plan to turn this feature request into requirements, design, and executable tasks: <prompt>
```

Approve each artifact explicitly when it is ready. After approving `TASKS.md`, invoke:

```text
Use $execute-task-waves to execute the next dependency-ready wave.
```

The skills honor the nearest `AGENTS.md`. The planning workflow currently uses exact root-level filenames—`REQUIREMENTS.md`, `DESIGN.md`, and `TASKS.md`—so use one active SDD change per checkout or a separate Git worktree for each concurrent change.

## Requirements

- Codex with local skill support
- Python 3 for the bundled validators and wave resolver
- A version-controlled project workspace

Core validation is local and does not require network access.

## Repository contents

Each skill contains:

- `SKILL.md` — workflow instructions and trigger description
- `agents/openai.yaml` — Codex display metadata and default prompt
- `references/` — artifact, approval, or execution contracts
- `scripts/` — deterministic validators or task-wave inspection tools

## License

No open-source license has been granted yet. The repository is public for inspection and controlled reuse; add an explicit license before broader redistribution.

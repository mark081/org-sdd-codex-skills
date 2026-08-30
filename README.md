# SDD Codex Skills

Four complementary Codex skills for brownfield discovery and gated Specification-Driven Development:

- **`analyze-brownfield-context`** maps an existing repository with Graphify and curates durable findings into an OKF v0.2 knowledge bundle.
- **`spec-to-task-plan`** turns a product or feature prompt into separately approved `REQUIREMENTS.md`, `DESIGN.md`, and `TASKS.md` artifacts.
- **`execute-task-waves`** executes an approved `TASKS.md` plan in dependency order, verifies each wave, and records completion evidence centrally.
- **`run-sdd-lifecycle`** orchestrates the other three skills as one resumable workflow while preserving every approval and governance gate.

## Workflow

```text
Use $run-sdd-lifecycle for an end-to-end change
  ↓
Existing repository
  → $analyze-brownfield-context
  → reviewed .sdd/knowledge OKF bundle
  → product or feature prompt
  → $spec-to-task-plan
  → approve REQUIREMENTS.md
  → approve DESIGN.md
  → approve TASKS.md
  → $execute-task-waves
  → verified implementation waves
```

The planning skill never implements product code. The execution skill requires an explicitly approved task plan and stops at failed verification, missing authority, or human governance gates.

`run-sdd-lifecycle` is the recommended entry point when you want Codex to determine the current stage and coordinate the full workflow. It derives state from the repository artifacts rather than maintaining a separate workflow-status file.

## Optional: Ponytail

[Ponytail](https://github.com/DietrichGebert/ponytail) can be used as an optional implementation-minimization layer during `execute-task-waves`. The SDD artifacts define what must be built; Ponytail helps find the smallest implementation that satisfies those approved contracts.

Install it through the Codex plugin marketplace:

```sh
codex plugin marketplace add DietrichGebert/ponytail
codex plugin add ponytail@ponytail
```

Ponytail's Codex integration uses Node.js lifecycle hooks. Ensure `node` is on `PATH`, open `/hooks` in Codex, review and trust the hooks, and start a new task. See Ponytail's repository for current installation and platform details.

When Ponytail is available or requested, `execute-task-waves` asks once before the first executable wave for `lite`, `full`, or `off`; `lite` is the recommended default. The selection is a workflow preference, not an approval gate. Ponytail is never required, and its recommendations cannot remove or weaken approved requirements, design, acceptance criteria, tests, evidence, security, privacy, accessibility, error handling, or governance controls.

## Install

### 1. Install Graphify

The `analyze-brownfield-context` skill requires the Graphify CLI. The Python package is named `graphifyy` (with two `y` characters), while the installed command is `graphify`:

```sh
uv tool install graphifyy
graphify --version
```

If `graphify` is not found after installation, run `uv tool update-shell`, open a new terminal, and retry `graphify --version`.

Graphify is required only for brownfield graph creation and refresh. The specification and task-execution validators remain usable without it when a repository has no Graphify graph or OKF brownfield bundle.

### 2. Install the Codex skills

Clone this repository somewhere durable, then link all four skill directories into your Codex skills directory.

#### macOS and Linux

```sh
git clone https://github.com/mark081/sdd-codex-skills.git
mkdir -p ~/.codex/skills
ln -s "$PWD/sdd-codex-skills/analyze-brownfield-context" ~/.codex/skills/analyze-brownfield-context
ln -s "$PWD/sdd-codex-skills/spec-to-task-plan" ~/.codex/skills/spec-to-task-plan
ln -s "$PWD/sdd-codex-skills/execute-task-waves" ~/.codex/skills/execute-task-waves
ln -s "$PWD/sdd-codex-skills/run-sdd-lifecycle" ~/.codex/skills/run-sdd-lifecycle
```

#### Windows PowerShell

Run these commands from the parent directory where you want to keep the cloned repository:

```powershell
git clone https://github.com/mark081/sdd-codex-skills.git

$repoRoot = (Resolve-Path ".\sdd-codex-skills").Path
$skillsRoot = Join-Path $env:USERPROFILE ".codex\skills"
New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null

@(
    "analyze-brownfield-context",
    "spec-to-task-plan",
    "execute-task-waves",
    "run-sdd-lifecycle"
) | ForEach-Object {
    $destination = Join-Path $skillsRoot $_
    if (Test-Path $destination) {
        throw "Destination already exists: $destination"
    }
    New-Item -ItemType Junction -Path $destination -Target (Join-Path $repoRoot $_) | Out-Null
}
```

The junctions let future `git pull` updates take effect without copying the skill directories again. If your environment does not permit junctions, replace the `New-Item -ItemType Junction` line inside the loop with:

```powershell
Copy-Item -Recurse -Path (Join-Path $repoRoot $_) -Destination $destination
```

Repeat the copy after repository updates.

On every platform, inspect and back up any existing destination before replacing it. Restart Codex after installation so it reloads the skill catalog.

## Use

Open Codex in a project repository and invoke:

```text
Use $run-sdd-lifecycle to implement this change: <prompt>
```

The orchestrator detects whether brownfield analysis is warranted, resumes the earliest incomplete stage, and pauses for each required approval. You can also invoke an individual stage directly:

```text
Use $analyze-brownfield-context to map this existing repository and create or refresh its OKF knowledge bundle.
```

After reviewing the generated context, invoke:

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
- Python 3 and PyYAML for the bundled validators and wave resolver
- `uv` for isolated dependency and CLI installation
- Graphify (`graphify` CLI installed from the `graphifyy` package) for brownfield extraction and refresh
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

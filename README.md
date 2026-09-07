# SDD Codex Skills

Five complementary Codex skills for repository-level Specification-Driven Development and optional cross-team coordination:

- **`analyze-brownfield-context`** maps an existing repository with Graphify and curates durable findings into an OKF v0.2 knowledge bundle.
- **`spec-to-task-plan`** turns a product or feature prompt into separately approved `REQUIREMENTS.md`, `DESIGN.md`, and `TASKS.md` artifacts.
- **`execute-task-waves`** executes an approved `TASKS.md` plan in dependency order, verifies each wave, and records completion evidence centrally.
- **`run-sdd-lifecycle`** orchestrates the other three skills as one resumable workflow while preserving every approval and governance gate.
- **`coordinate-org-sdd`** coordinates independently owned repositories through shared contracts, pinned handoffs and integration evidence. It drafts and checks records; it does not dispatch teams or authorize releases.

Start with `$run-sdd-lifecycle` for one repository. Start with `$coordinate-org-sdd` for a cross-team initiative, then hand bounded work to each team's local lifecycle. Local `REQUIREMENTS.md`, `DESIGN.md` and `TASKS.md` remain authoritative. Without explicit organizational participation, the individual workflow stays unchanged.

Try the read-only [three-team tutorial](docs/organizational-sdd-tutorial.md) before installing anything. From this checkout, with Python on PATH:

```sh
python3 examples/three-team/run_example.py --snapshot 02-approved-contract --coordinator-skill coordinate-org-sdd --allow-illustrative --format json
```

Expected: exit 0, three planning stages ready, `illustrative: true`. No implementation tests, approval, publication or release occur. PowerShell users can use `python` with the same arguments. The [adoption guide](docs/organizational-sdd-adoption.md) covers real ownership, policy inputs, revision changes and safe departure.

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

Use Ponytail's repository for installation and platform instructions; it is not installed by the skill commands below.

When Ponytail is available or requested, `execute-task-waves` asks once before the first executable wave for `lite`, `full`, or `off`; `lite` is the recommended default. The selection is a workflow preference, not an approval gate. Ponytail is never required, and its recommendations cannot remove or weaken approved requirements, design, acceptance criteria, tests, evidence, security, privacy, accessibility, error handling, or governance controls.

## Install

### Brownfield dependency: Graphify

The `analyze-brownfield-context` skill requires the Graphify CLI. The Python package is named `graphifyy` (with two `y` characters), while the installed command is `graphify`:

```sh
uv tool install graphifyy
graphify --version
```

If `graphify` is not found after installation, run `uv tool update-shell`, open a new terminal, and retry `graphify --version`.

Graphify is required only for brownfield graph creation and refresh. The specification and task-execution validators remain usable without it when a repository has no Graphify graph or OKF brownfield bundle.

### Install the five Codex skills

Use an inspected checkout in a durable location and run the relevant block from its repository root. If you need a checkout, obtain one through your normal Git workflow from [the repository](https://github.com/mark081/sdd-codex-skills). Installation changes the selected Codex skills directory; the tutorial does not require installation.

Both blocks respect `CODEX_HOME`; otherwise they use your user profile's `.codex` directory. They preflight all five destinations and refuse existing files, directories, links, junctions and broken symlinks. Inspect and preserve any existing installation before choosing a replacement; do not add force-overwrite flags. Run installation without another process concurrently changing the same destinations.

#### macOS and Linux

The default is a symlink installation. For independent copies, set `SDD_INSTALL_MODE=copy` before running the same block.

<!-- install-posix -->
```sh
install_sdd_skills() (
    set -eu
    sdd_repo=$(pwd -P)
    sdd_skills="${CODEX_HOME:-$HOME/.codex}/skills"
    sdd_mode="${SDD_INSTALL_MODE:-link}"
    case "$sdd_mode" in link|copy) ;; *) echo "Use link or copy" >&2; exit 1 ;; esac
    for sdd_name in analyze-brownfield-context spec-to-task-plan execute-task-waves run-sdd-lifecycle coordinate-org-sdd; do
        test -f "$sdd_repo/$sdd_name/SKILL.md" || { echo "Missing skill: $sdd_name" >&2; exit 1; }
        sdd_destination="$sdd_skills/$sdd_name"
        if test -e "$sdd_destination" || test -L "$sdd_destination"; then
            echo "Destination already exists: $sdd_destination" >&2
            exit 1
        fi
    done
    mkdir -p "$sdd_skills"
    for sdd_name in analyze-brownfield-context spec-to-task-plan execute-task-waves run-sdd-lifecycle coordinate-org-sdd; do
        sdd_destination="$sdd_skills/$sdd_name"
        if test "$sdd_mode" = link; then
            ln -s "$sdd_repo/$sdd_name" "$sdd_destination"
        else
            mkdir "$sdd_destination"
            cp -R "$sdd_repo/$sdd_name/." "$sdd_destination/"
        fi
    done
)
install_sdd_skills
```

#### Windows PowerShell

The default copies directories. To use Windows directory junctions, change the last line to `Install-SddSkills -Mode Junction`. `SymbolicLink` is also available where your permissions allow it. Junctions are a Windows option; PowerShell on macOS/Linux can use Copy or SymbolicLink.

<!-- install-powershell -->
```powershell
function Install-SddSkills {
    param([ValidateSet('Copy', 'Junction', 'SymbolicLink')][string]$Mode = 'Copy')
    $ErrorActionPreference = 'Stop'
    $sddRepo = (Get-Location).Path
    $sddCodexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else {
        Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex'
    }
    $sddSkills = Join-Path $sddCodexRoot 'skills'
    $sddNames = @('analyze-brownfield-context', 'spec-to-task-plan', 'execute-task-waves', 'run-sdd-lifecycle', 'coordinate-org-sdd')
    $sddExisting = if (Test-Path -LiteralPath $sddSkills) {
        @(Get-ChildItem -LiteralPath $sddSkills -Force -Name)
    } else { @() }
    foreach ($sddName in $sddNames) {
        $sddSource = Join-Path $sddRepo $sddName
        if (-not (Test-Path -LiteralPath (Join-Path $sddSource 'SKILL.md') -PathType Leaf)) {
            throw "Missing skill: $sddName"
        }
        if ($sddExisting -contains $sddName) {
            throw "Destination already exists: $(Join-Path $sddSkills $sddName)"
        }
    }
    [System.IO.Directory]::CreateDirectory($sddSkills) | Out-Null
    foreach ($sddName in $sddNames) {
        $sddSource = Join-Path $sddRepo $sddName
        $sddDestination = Join-Path $sddSkills $sddName
        if ($Mode -eq 'Copy') {
            New-Item -ItemType Directory -Path $sddDestination | Out-Null
            Get-ChildItem -LiteralPath $sddSource -Force | Copy-Item -Destination $sddDestination -Recurse
        } else {
            New-Item -ItemType $Mode -Path $sddDestination -Target $sddSource | Out-Null
        }
    }
}
Install-SddSkills
```

Restart Codex after installation or updates so it reloads the skill catalog. Installed skills discover one another through that catalog; they do not require sibling checkout paths.

### Updates and recovery

Review an update in a separate checkout before advancing a source checkout that active symlinks/junctions target: changes to that target are immediately visible through the links. Keep the target at its durable location. Preserve local modifications and use your normal reviewed Git update process; do not force-reset it.

Copies stay at the installed version until deliberately replaced. For each of the five exact destinations, inspect whether it is a directory or link, record its source/version, and move it to a uniquely named backup outside the discovery directory before running the installer again. A broken link is still an existing destination. On Windows inspect the reparse point; moving a junction must move the junction itself, not its target. Never recursively delete a link target or the skills root to update these skills. If installation fails partway, inspect and preserve each created destination, then retry only after all five target names are clear. The preflight intentionally refuses to merge into a partial installation.

To roll back, preserve the failed version, restore the exact backed-up destinations or reviewed source revision, and restart Codex. Updating files does not migrate organizational artifact formats or approve changed specifications; follow the [adoption guide](docs/organizational-sdd-adoption.md).

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
- CPython 3.11–3.14 for the supported tooling range; Git on PATH for revision/fixture checks
- PyYAML 6.0.3 for the brownfield validator and full regression suite
- `uv` optionally for isolated dependencies, or an existing Python environment with pip
- Graphify (`graphify` CLI installed from the `graphifyy` package) for brownfield extraction and refresh
- A version-controlled project workspace

The organizational, specification and wave validators use the Python standard library and need neither Graphify nor credentials. The brownfield validator requires PyYAML. Core validation is local and does not require network access once dependencies are available.

### Runtime support and verification

The supported minimum is CPython 3.11; the current stable boundary selected for CI is 3.14. Python 3.11 remains in security support, while 3.14 is in bugfix support; review these boundaries as upstream support changes. [Python version status](https://devguide.python.org/versions/).

From a selected supported Python environment, install the declared test dependency when authorized, then run:

```text
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

Use `python3` in POSIX shells if that is your selected interpreter. With an already populated uv cache, the offline equivalent is:

```text
uv run --offline --with pyyaml==6.0.3 python -m unittest discover -s tests -v
```

A missing cache entry is a missing dependency, not permission to download software automatically. Coordination-only example commands require no third-party dependency. Graphify and Ponytail are not installed or invoked by the core suite.

The [CI workflow](.github/workflows/tests.yml) configures six jobs: macOS, Linux and Windows, each on Python 3.11 and 3.14. It uses explicit Python selection, read-only repository permissions and no persisted checkout credentials. The action versions were checked against the official [setup-python release](https://github.com/actions/setup-python/releases/tag/v7.0.0) and [checkout release](https://github.com/actions/checkout/releases/tag/v7.0.0).

Local verification was performed on macOS with Python 3.13.11/PyYAML 6.0.3 (full suite) and Python 3.14.7 (standard-library subset), plus PowerShell 7.7 preview. The full Python 3.14 run could not resolve PyYAML from the offline cache; Python 3.11 was not installed. Native Windows/Linux and the full hosted matrix have **not** run during implementation; a configured workflow is not a passing CI result. Tests report unavailable symlink/PowerShell capabilities and native-only shell cases as explicit skips. Windows junctions require native Windows verification. See `.sdd/reports/` for the final runtime results and gaps before publishing. This package does not claim support for older/EOL Python, prereleases or free-threaded variants; no compatibility-breaking edits were made to existing standalone CLI signatures.

## Repository contents

Skill entry points:

- [Lifecycle](run-sdd-lifecycle/SKILL.md)
- [Brownfield analysis](analyze-brownfield-context/SKILL.md)
- [Specification planning](spec-to-task-plan/SKILL.md)
- [Wave execution](execute-task-waves/SKILL.md)
- [Organizational coordination](coordinate-org-sdd/SKILL.md)

Skills package their own applicable resources:

- `SKILL.md` — workflow instructions and trigger description
- `agents/openai.yaml` — Codex display metadata and default prompt
- `references/` — artifact, approval, or execution contracts
- `scripts/` — deterministic validators or task-wave inspection tools

The coordinator also contains [normative contracts](coordinate-org-sdd/contracts/records.md), [unapproved templates](coordinate-org-sdd/templates/README.md), and `src/org_sdd/`. [Example snapshots](examples/three-team/README.md) are synthetic; [tests](tests/) exercise local tools. Generated verification reports belong in `.sdd/reports/` and carry no approval authority.

## License

Copyright 2026 Mark Cooper and SierraX Technologies.

Licensed under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for attribution information.

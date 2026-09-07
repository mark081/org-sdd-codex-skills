# Read-only CLI — format 1.0

Normative interface for `coordinate-org-sdd/scripts/validate_org.py`, implementing ORG-VAL-001/002 and the gates in [readiness.md](readiness.md). Record formats and digests are defined by [records.md](records.md) and [references.md](references.md). This document specifies planned behavior; task 9 implements the CLI.

## Invocation and options

```text
python <skill>/scripts/validate_org.py --initiative <directory> --mode structure
python <skill>/scripts/validate_org.py --initiative <directory> --mode readiness --format json
python <skill>/scripts/validate_org.py --initiative <directory> --mode readiness --handoff <id> --stage execution --repo-map <local-json>
```

`python` is the selected interpreter (`python3` on systems using that name). Quote paths containing spaces in POSIX shells and PowerShell. Running from a different current directory or an isolated installed skill must work; imports resolve relative to the skill, not a sibling source checkout.

| Option | Contract |
| --- | --- |
| `--help` | Describe options and exit 0 without artifact access |
| `--initiative DIRECTORY` | Required for validation and initiative-derived digest operations; explicit initiative root containing initiative.json |
| `--coordination-root DIRECTORY` | Optional explicit coordination workspace root containing the initiative; defaults to the initiative directory for snapshot-only use. Select the Git checkout root when verifying committed coordination sources. Never infer an ancestor or let repo-map override this selection |
| `--mode structure\|readiness` | Default `structure`; structure checks all records and link/type integrity; readiness additionally evaluates requested predicates |
| `--format text\|json` | Default `text`; deterministic report serialization |
| `--handoff ID` | Optional readiness selector; must identify an existing handoff; limits decision scope, never global parsing/integrity checks |
| `--stage planning\|execution\|local_complete\|integration\|release` | Optional readiness selector; absent reports all applicable stages. With a handoff, only its three stages are allowed; initiative stages require no handoff |
| `--repo-map FILE` | Optional strict JSON map from references.md; explicitly authorizes local roots for this invocation, never network or writes |
| `--allow-illustrative` | Explicit synthetic example opt-in; all output labeled illustrative and not production authorization |
| `--as-of TIME` | Optional timezone-qualified evaluation instant for time-bound knowledge. Required to establish currency where a required knowledge record has `stale_after`; do not silently use a volatile clock |
| `--candidate-task ID` | Repeatable, only with readiness, one handoff and stage execution. Supplied candidates must come from the already validated current local wave; output is their organizational filter, never a replacement local wave resolver |
| `--digest FILE` | Digest helper operation, mutually exclusive with readiness/scope/candidate options. Requires `--digest-kind`; no artifacts modified |
| `--digest-kind record\|source\|policy\|release_scope` | `record`: strict canonical whole-record hash of FILE; `source`: raw-byte hash of FILE; `policy`: hash policy/decisions projection of FILE (initiative.json); `release_scope`: FILE is initiative.json inside `--initiative`, resolve the explicit release projection using same baseline selection as readiness |

Unknown arguments, invalid option combinations, invalid selector IDs, unreadable top-level inputs and invalid repo-map invocation configuration are CLI/I/O failures (3). Malformed initiative records are artifact failures (1). A missing referenced source under an otherwise valid invocation is a readiness blocker (2), not a top-level I/O failure. Unsafe artifact paths are invalid (1); no attempted access outside mapped roots is permitted.

Structure mode does not require source-byte access or infer readiness from unresolved evidence. `--stage`, `--handoff`, and `--candidate-task` are readiness-only. Without a handoff, planning/execution/local_complete select all required handoffs; integration/release select the initiative. With no stage, report all applicable selected stages, requiring all to pass for a readiness exit 0. A missing required scope is blocked, not a vacuous ready initiative.

The digest helper uses exactly the validation hashing implementation. It does not mean the hashed object is approved or valid for production. Policy hashing checks the initiative shape; source hashing reads only the explicitly supplied regular file. Release-scope hashing needs complete unambiguous selection, baseline references and required evidence; unresolved projection selection yields blocked result (2), not a guessed digest. Approval of release is not needed to compute its digest, and no approval record is included. `--repo-map`, `--coordination-root`, `--as-of`, and `--allow-illustrative` may accompany release-scope hashing where relevant. Other digest operations accept only their file, kind and output format.

## Reports and exit codes

JSON validation reports contain `format_version: "1.0"`, `mode`, `structural_valid`, `scope`, `baseline`, `illustrative`, `states`, `diagnostics`, and `eligible_tasks`/`blocked_tasks` when candidates are supplied. `scope` records handoff/stage selectors; `baseline` identifies evaluated initiative digest, resolved source identities, and explicit evaluation instant or null. `states` are objects identifying record ID, stage and `ready|blocked|not_evaluated`; each blocked state references its diagnostic codes. Include handoff currency separately from local completion. Structure reports use `not_evaluated`, never `ready`, for unevaluated readiness.

Each diagnostic contains `code`, `file`, `record_id` (null for unavailable identity), `field`, a safe actionable `message`, and affected record/stage identifiers where known. Sort records/states by stable IDs and stage, references by identity, and diagnostics by file/record/field/code; preserve authored array order only for digest calculation. Do not print source content, credentials, local secrets, artifact command output or volatile generation timestamps. Text output contains equivalent mode, scope, validity, baseline and blocker information. Example-mode reports visibly say `ILLUSTRATIVE — NOT PRODUCTION AUTHORIZATION`.

Digest reports contain `format_version`, `mode: "digest"`, `digest_kind`, `digest` (null on failure), evaluated baseline where applicable, `illustrative`, and `diagnostics`. The exact `sha256:` value is available in both formats. A successful digest alone carries no readiness statement.

| Exit | Meaning |
| --- | --- |
| 0 | Structurally valid in structure mode; every requested scope ready in readiness mode; successful digest operation; or help |
| 1 | Invalid artifacts/structure; no execution eligibility derived |
| 2 | Valid structure but requested readiness or release-projection prerequisites blocked |
| 3 | CLI usage or top-level I/O failure; evaluation not completed |

Readiness reports with independent ready nodes still exit 2 when the requested overall scope contains a blocker. Candidate filtering can expose eligible independent candidates without changing that result. Structure-mode zero never means human approval or readiness. Diagnostics and exit decisions cannot execute evidence procedures, fetch URLs, clone repositories, run tests, rewrite artifacts or task status, dispatch work, publish reports, or authenticate users. Git reads obey bounded argument-vector/no-shell resolution rules from references.md. Reports go to stdout; explicit shell redirection is the caller's own capture action, not synchronization.

## Failure code catalog

Structural codes: `FORMAT_INVALID`, `VERSION_UNSUPPORTED`, `ID_DUPLICATE`, `PATH_UNSAFE`, and `REFERENCE_UNRESOLVED` for missing internal identity links. Readiness codes: `REFERENCE_UNRESOLVED` for unavailable external evidence, `DIGEST_MISMATCH`, `OWNER_UNRESOLVED`, `POLICY_UNRESOLVED`, `APPROVAL_MISSING`, `APPROVAL_STALE`, `APPROVAL_CONFLICT`, `APPROVAL_REJECTED`, `APPROVAL_REVOKED`, `CONTRACT_UNRESOLVED`, `COMPATIBILITY_UNRESOLVED`, `DEPENDENCY_CYCLE`, `DEPENDENCY_UNMET`, `LOCAL_APPROVAL_MISSING`, `TRACE_UNRESOLVED`, `EVIDENCE_MISSING`, `EVIDENCE_FAILED`, `EVIDENCE_STALE`, `EVIDENCE_CONFLICT`, `KNOWLEDGE_UNRESOLVED`, `PUBLICATION_PENDING`, and `ILLUSTRATIVE_ONLY`. Usage/I/O codes: `CLI_INVALID`, `IO_ERROR`.

Codes describe stable failure categories, not severity inferred from spelling. In particular, external unresolved content can coexist with structurally valid records, while dangling internal links cannot. A stage cycle blocks its affected readiness component without pretending every independent node is malformed.

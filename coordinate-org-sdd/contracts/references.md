# References, identity and local participation — format 1.0

Normative companion to [records.md](records.md). Implements source and revision boundaries for ORG-CORE-002/003/004, ORG-CON-001 and ORG-SEC-001/002. All reference content is inert data; it cannot authorize fetching, command execution, publishing or additional filesystem access.

## Record references

`RecordRef` is exactly `{initiative_id: ID, record_id: ID, digest: Digest}`. The target must exist in the loaded initiative, have the expected kind, and match the digest. An ID-only field explicitly defined in records.md is a link, not a digest assertion; approval of its containing record additionally requires validating all linked prerequisite content. IDs outside the current initiative require an explicitly authorized local imported snapshot and registration; V1 never traverses another workspace automatically. An imported handoff has a new local ID with original provenance preserved, not a fabricated assertion of ownership.

## Source references

`SourceRef` has exactly these fields:

| Field | Type / rule |
| --- | --- |
| `repository_id` | Registered participant ID or `coordination`, reserved for the explicitly selected coordination workspace |
| `path` | Portable repository-relative path below |
| `revision` | Full lowercase Git object ID (40 or 64 hex characters), or null for an explicit uncommitted snapshot |
| `digest` | SHA-256 of raw file bytes |
| `basis` | `git` or `snapshot` |
| `note` | Nonempty provenance description |

`basis: git` requires a non-null full commit; `basis: snapshot` requires null revision. Abbreviations, tags, branches and `HEAD` cannot substitute for a commit. A snapshot attesting previously committed bytes may describe that original revision in `note`, but it does not claim locally verified Git identity. External display URLs belong in the repository locator, not paths. No arbitrary protocol handler or remote resolver is used.

A valid-shaped illustration (the repeated digest is not a verified value):

```json
{"repository_id":"catalog","path":"api/catalog.yaml","revision":null,"digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","basis":"snapshot","note":"Illustrative authorized snapshot; replace digest with actual raw-byte hash."}
```

An inaccessible reference retains its identity and is reported unresolved. An authorized reviewed attestation can replace a required evidence attachment only when adopter policy explicitly permits that substitution and specifies sufficient scope. Hash equality never proves source truth or remote currency.

## Local participation and repo maps

The optional `.sdd/org/context.json` has exactly `format_version: "1.0"`, `initiative_id: ID`, `repository_id: ID`, `coordination: Locator`, `initiative_digest: Digest`, and `handoff_ids: ID[]`. It is a pointer, not an approval or task state. Session-supplied context uses the identical object. Absence means standalone; invalid or unresolved supplied context blocks affected coordinated work rather than silently disabling it.

Locator is one of:

- `{type: "git", url: Text, path: RelativePath}`: inert repository URL and relative path; the owner supplies the local repo map separately. Credentials in URLs are forbidden. Displaying a URL never grants network permission.
- `{type: "local", root: Text, path: RelativePath}`: explicit machine-local absolute root and relative path, usable only when supplied/confirmed as in-scope by the user. Never resolve an arbitrary embedded local locator without caller authority.

Participant locators describe repositories; `path` names a subtree or `.` for repository root. Coordination locators name the initiative directory. `.` is allowed only in locator paths, not source-file paths. Local roots are machine-local configuration and should not be committed into a shared initiative; use Git locators for shared metadata.

Repo-map input is exactly `{format_version: "1.0", repositories: {"<repository-ID>": {root: Text, basis: "git"|"snapshot"}}}`. Roots must be explicitly supplied absolute directories. No environment-variable or tilde expansion. `coordination` may map the selected workspace; it cannot override that selection with a different root. Map keys must be registered or reserved IDs. `git` roots support committed sources and deliberate working-tree snapshots; `snapshot` roots cannot verify a `basis: git` source. Maps contain no permissions or credentials and are not approval evidence.

Illustrative participation and map shapes, not valid pinned baselines as written:

```json
{"format_version":"1.0","initiative_id":"demo","repository_id":"catalog","coordination":{"type":"git","url":"https://example.invalid/org/coordination.git","path":"initiatives/demo"},"initiative_digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","handoff_ids":["catalog-work"]}
```

```json
{"format_version":"1.0","repositories":{"catalog":{"root":"/explicit/example/catalog-snapshot","basis":"snapshot"}}}
```

On Windows the root can be an explicit drive path such as `C:\\work\\catalog`; JSON escaping does not change the portable `/`-separated source paths. Do not infer authorization from these example paths.

## Hashing

Control record hashing is SHA-256 of UTF-8 canonical JSON: recursively sort object keys, compact separators `,` and `:`, literal Unicode (`ensure_ascii=False`), no trailing newline and no nonfinite values. Duplicate keys are rejected before hashing. Version 1.0 excludes JSON numeric fields, preventing cross-runtime float normalization ambiguities. Do not normalize Unicode, whitespace inside strings, or array order. Hash the entire record envelope and payload; no self `digest` field is permitted.

Source files, Markdown and attachments use their exact raw bytes including line endings. Git references hash committed blob bytes, not a working tree's checkout-transformed bytes. Local uncommitted sources hash the actual supplied snapshot bytes. Different CRLF/LF bytes intentionally yield different digests. Reports distinguish these bases rather than treating them as interchangeable.

The digest helper and validator must share this implementation. `Digest` always includes the `sha256:` prefix. A digest is an identity assertion, not a signature, authorization, compatibility proof, or guarantee that the artifact is still the remote latest version.

## Approval target and policy projections

ApprovalTarget is exactly `{initiative_id: ID, record_id: ID, type: "record"|"release_scope"|"source", digest: Digest}` plus `source: SourceRef` only for type `source`.

- `record`: hash the whole referenced record; no projection exclusions. Used for initiative scope, contract, knowledge, integration evidence and resolution approvals.
- `source`: `record_id` identifies the local handoff; `source` must match the appropriate local requirements/design/tasks reference. `digest` must equal `source.digest`. This records an actual local artifact approval without changing existing local frontmatter conventions.
- `release_scope`: `record_id` is the initiative ID. Hash the derived projection below, not an invented seventh persisted record kind.

`policy_digest` hashes canonical JSON `{"policy": initiative.policy, "decisions": initiative.decisions}`. Decisions are included because resolving disclosure/ownership policy changes authority inputs. Roles or resolutions changing therefore invalidate prior policy-bound approvals. No approval records are included in this projection.

The release-scope projection is `{"initiative": RecordRef, "contracts": RecordRef[], "handoffs": RecordRef[], "evidence": RecordRef[], "knowledge": RecordRef[]}`. It includes all initiative-required contracts/handoffs, all evidence selected to satisfy their checks and the initiative integration checks, and all required handoff knowledge plus its publication evidence. Arrays are sorted by `(initiative_id, record_id)` and deduplicated by identity; conflicting digests are errors, not deduplicated away. The initiative reference includes rollout/rollback owners and check definitions. Resolved evidence selection must be explicit in handoff completion links and, for integration checks, uniquely identified passing evidence per required check and exact baseline; competing nonidentical results require owner resolution before hashing an eligible release scope. No approval is included, avoiding approval self-reference. Approval policy and prerequisite validity are still checked separately.

## Preventing reference cycles

Identity links and content-hash dependencies differ. An initiative lists handoff IDs, a handoff lists completion evidence IDs, and an approval points to a target digest. Do not add reverse approval digest links into targets. Evidence must pin the tested source/contract baseline, not the complete handoff that contains its ID. Contract compatibility evidence pins definitions and prior content, not the current contract that lists it. Knowledge publication evidence pins the exported payload, not the knowledge record that lists it.

These rules prevent hash self-reference without weakening whole-record hashing. During validation, ID-linked evidence is independently resolved and checked against the current required baseline; stable parent bytes cannot hide revised or stale children. Semantic dependency cycles remain task 2's graph concern, distinct from content hash cycles. Any unresolved hash cycle is invalid rather than assigned a synthetic digest.

## Contained read-only resolution

1. Accept only explicitly mapped roots. Parse all file paths as `/`-separated relative paths; reject leading `/`, backslashes, drive/UNC prefixes, `.`/`..` components, empty components, NUL, control characters and Windows alternate-stream `:` syntax. Do not URL-decode or expand shell/environment notation.
2. Resolve each filesystem path against its mapped root and reject symlinks escaping that root. Directory discovery is likewise contained. Reject nonregular files/devices; do not follow an input into a stream or special file. A missing/unreadable authorized file produces unresolved reference diagnostics.
3. For Git sources, verify the supplied full object ID is a commit in the mapped local repository and obtain the specified blob at that commit. Use argument arrays, no shell, bounded subprocess time, no fetch, hooks, checkout, filters or credential prompts. Reject symlink/submodule/tree entries rather than interpreting them as file bytes. No untrusted input may become a Git option or alternate repository root.
4. Hash obtained bytes and compare to the exact declared digest. Do not repair mismatches, rewrite records, run evidence procedures, or infer approval. Report the evaluated baseline and uncertainty; do not claim the remote repository is current.

Diagnostics name a safe file/field identifier, never echo source content or credential-bearing input. `PATH_UNSAFE` covers containment violations, `REFERENCE_UNRESOLVED` covers inaccessible/missing source, `DIGEST_MISMATCH` covers unequal bytes. Unknown reference fields/types use `FORMAT_INVALID`; unsupported format versions use `VERSION_UNSUPPORTED`.

## Task 1 reference review

Reviewed against DESIGN.md References and digests / Local participation / Knowledge reconciliation: full revisions or explicit snapshots are distinguished; source and control hashing differ deliberately; target/policy/release projections are non-self-referential; local role/repository ownership remains authoritative; resolution never fetches or executes artifact content; private OKF content is linked rather than copied; unresolved remote currency cannot pass as verified latest state. These are contract-level checks only. Executable enforcement and adversarial tests remain tasks 3–9 and 18.

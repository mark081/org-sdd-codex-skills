---
title: Organizational SDD coordination
document_id: ORG-SDD-REQUIREMENTS
version: 0.1.0
status: approved
approved_at: 2026-09-07
created: 2026-09-07
updated: 2026-09-07
owner: Mark Cooper
intended_users: Engineering teams and organizational integration owners
intended_region: Organization-neutral; deployment policies supplied by adopters
notation: EARS
reviewers: []
approvals:
  - artifact_version: 0.1.0
    approved_at: 2026-09-07
    source: Explicit user approval in this conversation
---

# Requirements: Organizational SDD Coordination

## Purpose and intended-use boundary

Extend `sdd-codex-skills` with an optional organizational coordination layer above the existing repository-level SDD lifecycle. Deliver a new skill, updates to all four existing skills, normative artifact contracts, templates, deterministic validation, automated tests, and tutorial documentation.

This is a reference workflow and local tooling, not a centrally operated agent platform. Teams retain ownership of their repositories, specifications, implementations, and approvals. The organizational layer coordinates shared obligations and evidence; it does not confer authority over another team.

## Problem statement

The individual workflow connects brownfield discovery, requirements, design, task planning, and execution inside one checkout. A cross-team change additionally needs explicit ownership, shared interface agreements, dependency readiness, revision-aware approvals, and integration evidence. Local completion alone cannot establish organizational readiness.

## Goals and success measures

- A three-team example completes the documented coordination lifecycle with traceable contracts and evidence.
- Every mandatory requirement maps to design, implementation tasks, and verification evidence before release.
- Automated negative fixtures detect missing owners, unresolved references, dependency cycles, stale approvals, incompatible contract declarations, and missing integration evidence.
- Existing single-repository fixtures pass without organizational artifacts or new mandatory runtime services.
- Tutorial instructions include reproducible validation commands for POSIX shells and Windows PowerShell.

## Non-goals

- Hosting a control plane, message bus, central graph database, or autonomous swarm service.
- Automatic cross-repository writes, PR submission, task dispatch, releases, or approval on behalf of owners.
- Replacing local REQUIREMENTS.md, DESIGN.md, TASKS.md, or the existing approval gates.
- Defining organization-specific legal, privacy, residency, retention, security, or release policies.
- Proving semantic API compatibility solely from a version number or treating a language model's judgment as test evidence.
- Requiring Graphify for coordination, or merging all private repository knowledge into a central graph.

## Stakeholders and actors

- Initiative owner: defines outcomes and organizational scope.
- Team/repository owner: approves and delivers its local contribution.
- Contract owner and affected consumers: review shared obligations and changes.
- Integration owner: coordinates dependency readiness and integration verification.
- Release authority: supplies release approval under adopter policy.
- Agent: drafts, checks, and executes only authorized actions; never invents owner approval.

## Scope and workflow

An organizational change uses a Git-based coordination workspace, with one directory per initiative. It records participating repositories and owners, shared contracts, revision-pinned handoffs, dependencies, approvals, and integration evidence. Each participating checkout continues to use its own root-level specification artifacts and reviewed local knowledge bundle.

The intended sequence is: discover participation and policy inputs; agree on organizational scope and contracts; hand off bounded work to local SDD lifecycles; verify dependency readiness; collect local completion evidence; verify integration; request release approval; reconcile organizational knowledge. Steps may repeat as revisions change. Local planning can proceed against explicitly approved contracts before another team's implementation is complete.

## EARS conventions and priorities

Each requirement uses “shall” for a mandatory behavior. “When” specifies a trigger, “while” a state, “where” an optional capability, and “if” an unwanted condition. All requirements below are P1 (required for this milestone). Verification combines deterministic tests with documented review where human judgment is necessary.

## Coordination and authority requirements

**ORG-CORE-001 — New coordination skill**
The package shall provide `coordinate-org-sdd` with invocation metadata and instructions to initialize, inspect, resume, and reconcile an organizational initiative using recorded artifacts.
Priority: P1. Verification: skill validation and walkthrough. Acceptance: each operation has documented inputs, outputs, and stopping conditions; resuming does not duplicate an initiative or manufacture completion.

**ORG-CORE-002 — Federated authority**
The coordination workflow shall identify an accountable owner for every participating repository, shared contract, handoff, and integration check while preserving local specifications as authoritative for local work.
Priority: P1. Verification: positive and missing-owner fixtures. Acceptance: unresolved ownership blocks the affected approval or execution handoff; organizational summaries link to rather than silently replace local specifications.

**ORG-CORE-003 — Versioned organizational artifacts**
The package shall define versioned normative contracts and reusable templates for an initiative manifest, ownership and repository references, shared contracts, dependency handoffs, approval records, integration evidence, and knowledge references.
Priority: P1. Verification: schema/contract tests. Acceptance: artifacts carry stable identifiers, format versions, status, and provenance; unsupported versions produce actionable diagnostics.

**ORG-CORE-004 — Revision-bound approvals**
When an approval is recorded, the workflow shall bind it to the approved artifact revision or content digest and record the approving actor, scope, and time without inventing approval identity or authority.
Priority: P1. Verification: approval fixtures and instruction review. Acceptance: editing approved content invalidates its approval and identifies dependent evidence requiring revalidation; a passing validator is never reported as human approval.

**ORG-CORE-005 — Governed policy inputs**
If required owner assignments, approval rules, or sensitive-data decisions are unresolved, then the workflow shall report the missing decision, accountable role, affected scope, and permitted unblocked work.
Priority: P1. Verification: unresolved-policy scenarios. Acceptance: generic examples are labeled illustrative; no example policy becomes a deployment default or automatic authorization.

**ORG-CORE-006 — Permission boundaries**
The coordination skill shall distinguish drafting a handoff from dispatching work, modifying another repository, publishing artifacts, or releasing software, and require existing explicit authority for each external action.
Priority: P1. Verification: workflow scenarios. Acceptance: absent tooling or permissions produces a manual handoff with exact next steps, not a claim that work was dispatched or completed.

## Contracts, dependencies, and readiness

**ORG-CON-001 — Shared obligations**
The shared-contract format shall support API, event, data, and shared nonfunctional obligations through owner-reviewed references to authoritative definitions, provider and consumer identities, versions, acceptance checks, and change status.
Priority: P1. Verification: contract examples and validation. Acceptance: consumers can identify the exact obligation and revision they depend on without requiring a single interface-description technology.

**ORG-CON-002 — Contract change impact**
When a shared contract changes, the workflow shall identify affected participants and approvals, record compatibility assessment and supporting evidence, and require migration or explicit resolution for breaking or unknown compatibility.
Priority: P1. Verification: compatible, breaking, and unknown fixtures. Acceptance: a semantic version label alone cannot satisfy compatibility evidence or clear a blocked consumer.

**ORG-CON-003 — Stage-specific dependencies**
The dependency format shall identify producer and consumer work, the required readiness stage, contract revision, acceptance evidence, and responsible owners.
Priority: P1. Verification: staged readiness tests. Acceptance: an approved-contract dependency can unblock local planning without falsely satisfying an implementation or integration dependency.

**ORG-CON-004 — Dependency failure detection**
If dependencies contain cycles, dangling references, unmet prerequisites, or conflicting revisions, then validation shall report the involved identifiers and prevent the affected work from being represented as ready.
Priority: P1. Verification: negative dependency fixtures. Acceptance: stage-specific cycles are diagnosed; independent ready work remains distinguishable from blocked work.

**ORG-CON-005 — Separate completion states**
The workflow shall distinguish local completion, integration verification, and release approval using separate evidence and approval conditions.
Priority: P1. Verification: transition tests. Acceptance: local task completion cannot imply integration success or release authorization; failed or stale integration evidence cannot satisfy organizational readiness.

**ORG-CON-006 — Integration and recovery evidence**
The integration record shall reference the tested repository revisions, contract revisions, check commands or procedures, outcomes, evidence locations, and agreed rollout and rollback responsibilities.
Priority: P1. Verification: integration fixtures. Acceptance: missing or mismatched evidence blocks integration verification; rollout execution remains outside implicit coordination authority.

## Existing skill integration

**ORG-SKL-001 — Lifecycle routing**
Where a repository explicitly participates in an organizational initiative, `run-sdd-lifecycle` shall load its coordination reference, check relevant organizational prerequisites, and preserve every local specification and execution approval gate.
Priority: P1. Verification: standalone and federated routing tests. Acceptance: missing organization context in a standalone repository does not trigger organizational setup; organizational status never overrides unapproved local artifacts.

**ORG-SKL-002 — Brownfield boundary knowledge**
Where organizational participation is configured, `analyze-brownfield-context` shall curate relevant ownership, external dependencies, shared-contract references, and uncertainty into local knowledge with source provenance and review status.
Priority: P1. Verification: knowledge fixtures and review. Acceptance: local source evidence remains authoritative; inaccessible external sources are marked unresolved, and Graphify-derived claims are not promoted to approved contracts automatically.

**ORG-SKL-003 — Specification consumption**
Where an organizational handoff is supplied, `spec-to-task-plan` shall trace local requirements, design, and tasks to the relevant organizational obligations and surface conflicting or stale inputs before the affected gate advances.
Priority: P1. Verification: planning scenarios. Acceptance: the resulting local artifacts record obligations and revisions; unresolved conflicts cannot silently disappear during planning.

**ORG-SKL-004 — Execution consumption and reporting**
Where tasks have organizational dependencies, `execute-task-waves` shall check their stage-specific readiness before execution and produce revision-bound local completion and integration-handoff evidence after verification.
Priority: P1. Verification: wave-readiness and evidence tests. Acceptance: unavailable required dependencies block only affected work; task status remains owned by the local integration owner, and existing verification and Ponytail controls remain intact.

**ORG-SKL-005 — Knowledge freshness after execution**
When completed work changes organizationally relevant knowledge or contracts, the workflow shall reconcile local knowledge and prepare the corresponding organizational update before claiming the affected handoff is current.
Priority: P1. Verification: refresh scenarios. Acceptance: source fingerprints and changed references are checked; required human review remains pending until supplied; inability to publish is reported explicitly rather than treated as successful synchronization.

## Validation and quality

**ORG-VAL-001 — Deterministic local validation**
The package shall provide a documented validator that checks organizational artifact structure, identifiers, required fields, references, dependency readiness, revision-bound approval consistency, and evidence completeness without an LLM or network connection.
Priority: P1. Verification: CLI tests. Acceptance: valid fixtures exit zero; invalid fixtures exit nonzero with artifact and field identifiers; unavailable remote content remains unresolved unless verified local evidence is supplied.

**ORG-VAL-002 — Validation trust limits**
The validator shall distinguish structural validity from readiness and shall document that it does not independently authenticate approving actors, enforce repository permissions, or establish real-world semantic compatibility.
Priority: P1. Verification: output and documentation review. Acceptance: a structurally valid pending initiative is not labeled approved, integrated, or releasable.

**ORG-VAL-003 — Automated regression suite**
The package shall include automated positive and negative tests for organizational contracts, dependencies, approvals, freshness, integration states, and existing individual workflows.
Priority: P1. Verification: full documented test command. Acceptance: tests include all failure categories listed in the success measures and can run locally without Graphify, network services, or production credentials through fixtures.

**ORG-VAL-004 — Platform and dependency compatibility**
The new coordination tooling shall support the project's documented Python-based local tooling on macOS, Linux, and Windows without introducing a mandatory hosted service or Graphify dependency for coordination-only use.
Priority: P1. Verification: portable path tests and platform CI or explicitly recorded platform test gaps. Acceptance: dependency declarations and both shell command variants are documented; untested platforms are not claimed as verified.

**ORG-VAL-005 — Individual workflow compatibility**
When organizational participation is absent, the four existing skills shall retain their current standalone artifact paths, approval gates, execution ownership, and optional-dependency behavior.
Priority: P1. Verification: baseline regression scenarios. Acceptance: the individual-complete milestone remains a usable reference; adoption does not require relocating existing local specifications.

## Documentation and adoption

**ORG-DOC-001 — End-to-end tutorial**
The package shall include a three-team tutorial covering setup, ownership, a shared contract, local lifecycle handoffs, dependency blocking, a contract revision, integration verification, release approval, and knowledge refresh.
Priority: P1. Verification: walkthrough against example artifacts. Acceptance: commands and prompts have expected outcomes; illustrative approvals and evidence are clearly labeled and cannot be mistaken for production authorization.

**ORG-DOC-002 — README and installation**
The README shall explain the individual and organizational layers, list all five skills, show when to invoke each entry point, and include installation and update instructions for POSIX shells and Windows PowerShell.
Priority: P1. Verification: link, path, and command review. Acceptance: Graphify/graphifyy and optional Ponytail dependency boundaries remain explicit; installation instructions preserve existing destinations.

**ORG-DOC-003 — Incremental adoption and maintenance**
The documentation shall describe adopting one cross-team initiative, adding participants incrementally, resolving stale context and contract conflicts, maintaining ownership, and returning to standalone operation without deleting local specifications.
Priority: P1. Verification: guide review. Acceptance: maintenance triggers, failure recovery, artifact-version migration expectations, and release-check responsibilities are explicit.

## Security, privacy, and provenance

**ORG-SEC-001 — Minimum shared context**
The workflow shall publish only explicitly authorized organizational metadata and evidence references, exclude secrets and private chain-of-thought, and preserve access boundaries around private repository knowledge.
Priority: P1. Verification: instruction and synthetic sensitive-data scenarios. Acceptance: central graph aggregation or copying private source is not required; access restrictions and redacted or unavailable evidence are visible and do not produce false readiness.

**ORG-SEC-002 — Untrusted input handling**
The skills and validators shall treat repository content, graph output, external references, and evidence as data rather than permission to execute embedded instructions or commands.
Priority: P1. Verification: malicious-input fixtures and workflow review. Acceptance: validation does not execute artifact-supplied commands; examples document explicit review before running referenced checks.

Data minimums: stable initiative and artifact identifiers; owning roles; source repository and path; immutable revision or content digest; relationship identifiers; evidence and approval scope; observation time; freshness and review status. Retention, residency, visibility, and authentication policies are adopter inputs, not prescribed by this reference implementation.

## User stories

- As a platform owner, I can agree on a contract with two consumers before their implementations are complete.
- As a team owner, I can execute approved local work without granting a coordinator unrestricted access to my repository.
- As an integration owner, I can identify exactly which obligation blocks readiness and which evidence will resolve it.
- As a reviewer, I can see when a change invalidates prior approval or verification.
- As an individual user, I can continue using the original lifecycle without organizational configuration.

## Validation and release gates

1. Explicit approval of this REQUIREMENTS.md permits design only.
2. Explicit approval of DESIGN.md permits task planning only.
3. Explicit approval of TASKS.md permits bounded execution in dependency order.
4. Release verification requires the complete automated suite, worked-example walkthrough, documentation/link checks, and recorded requirement coverage and residual platform gaps.
5. Publishing, installation into active skill directories, and organization-specific deployment remain subject to explicit authorization. The existing individual-complete tag must not be moved.

## Decisions and remaining open questions

| Item | Proposed disposition | Owner | Blocking status |
| --- | --- | --- | --- |
| V1 scope | Include all requirements above; optional federated layer | Mark Cooper | Approved 2026-09-07 |
| New entry point | `coordinate-org-sdd` | Mark Cooper | Approved 2026-09-07 |
| Coordination storage | Git workspace, one initiative directory per change; local specs stay in owning repos | Design owner | Detailed paths and schema are design work |
| Concrete organization and approvers | Supplied per adopting initiative, never fabricated | Adopting organization | Blocks affected deployment gates, not generic implementation |
| Remote automation | Manual handoff baseline; tool-based dispatch only with capability and authority | Integration owner | No remote automation required for V1 |

## Glossary

- Organizational SDD: coordination of independently owned repository-level SDD lifecycles.
- Initiative: one cross-team change with explicit scope and participants.
- Shared contract: a versioned obligation between providers and consumers.
- Handoff: bounded work or evidence passed between accountable owners.
- Readiness: satisfaction of a specified stage's prerequisites, not a blanket approval.
- OKF: the existing skill's Open Knowledge Format bundle convention.
- Provenance: the source and revision supporting a claim or artifact.

## Assumptions, dependencies, and change control

The current four-skill repository is the baseline; this milestone does not implement a separate hosted harness. Existing Python validation and local Git workflows remain the foundation. Direct inspection of the skill sources is sufficient for drafting this milestone; a generated graph is not required to approve the scope.

Normative contracts will live in `contracts/`, reusable templates in `templates/`, implementation scripts in the relevant skill's `scripts/` or `src/` where appropriate, tests in `tests/`, and generated reports in `.sdd/reports/`. Final paths and interoperability rules belong in DESIGN.md.

Material changes after approval return the affected artifact to draft and require renewed approval. No earlier approval of the individual milestone is an approval of these organizational requirements, design, or tasks.

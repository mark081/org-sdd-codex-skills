# Artifact Contracts

## REQUIREMENTS.md

Required structure:

1. YAML front matter with title, document ID, version, status, dates, owner, intended users/region, notation, reviewers, and approvals.
2. Purpose and intended-use boundary.
3. Problem statement.
4. Measurable goals and success measures.
5. Explicit non-goals.
6. Stakeholders and actors.
7. Scope and workflow.
8. EARS conventions.
9. Prioritized requirements grouped by capability.
10. Privacy, security, safety, and compliance requirements when applicable.
11. Quality attributes.
12. Data/provenance minimums.
13. User stories.
14. Validation and release gates.
15. Decisions and open questions with owner and blocking status.
16. Glossary.
17. Assumptions, dependencies, and change control.

EARS patterns:

- Ubiquitous: `The system shall <response>.`
- Event-driven: `When <trigger>, the system shall <response>.`
- State-driven: `While <state>, the system shall <response>.`
- Optional: `Where <feature>, the system shall <response>.`
- Unwanted behavior: `If <condition>, then the system shall <response>.`

Give each requirement a stable ID, priority, verification method, and independently testable behavior. Avoid “fast,” “easy,” “secure,” or “appropriate” without a measurable or governed definition.

## DESIGN.md

Use this sequence unless the user supplies another structural template:

1. `# Design Document: <name>`
2. `## Overview`
3. `### Key Design Decisions`
4. `## Architecture` with the smallest useful Mermaid diagram.
5. `### Component Interaction Flow`
6. `## Components and Interfaces`
7. `## Data Models`
8. `### Database Schema` when persistence exists.
9. `## Correctness Properties`
10. `## Error Handling`, categories, flow, and principles.
11. `## Testing Strategy` with property, unit, integration, and smoke tests as applicable.

Each correctness property must state an invariant, quantify its scope, and cite the requirement IDs it validates. Do not expose or require private model chain-of-thought; design auditable structured evidence instead.

## TASKS.md

Required structure:

1. `# Implementation Plan: <name>`
2. `## Overview`
3. An execution contract.
4. `## Tasks` with numbered checkboxes.
5. Bounded leaf tasks with acceptance, verification, and requirement IDs.
6. Integration and governance checkpoints.
7. `## Notes` defining optional-task and completion semantics.
8. `## Task Dependency Graph` containing one fenced JSON object with sequential waves.

Leaf task format:

```markdown
  - [ ] 2.1 Implement one bounded capability
    - Describe the smallest complete change.
    - Acceptance: state observable completion criteria.
    - Verification: state exact checks or tests.
    - _Requirements: REQ-001, REQ-002_
```

Tasks in one wave must be independent. If they may edit the same files or schema, serialize them or explicitly assign integration ownership. Never place dependent waves in parallel.

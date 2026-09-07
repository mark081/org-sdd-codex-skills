---
title: Synthetic analytics catalog change
document_id: EXAMPLE-ANALYTICS
version: 1.0.0
status: approved
created: 2026-09-07
updated: 2026-09-07
owner: synthetic-owner
intended_users: Synthetic tutorial teams
intended_region: Example only
notation: EARS
reviewers: []
approvals: []
illustrative: true
---
# Requirements: Synthetic analytics

## Purpose and boundary
Demonstrate one local SDD handoff; not production software or real approval.

## Problem statement
This team must agree on the shared catalog interface.

## Goals and success measures
One obligation maps to one design property and one leaf task, with exact-baseline evidence.

## Non-goals
No real deployment, payment, event broker or organization policy.

## Stakeholders
Synthetic Catalog provider, Checkout purchaser and Analytics reporting consumer.

## Scope and workflow
Review requirements, then design, then task plan with three separate actual adopter gates.

## EARS conventions
Shall is mandatory; When introduces a trigger.

## Requirements
**ANALYTICS-ORG-001 — Shared catalog boundary**
When a catalog item is supplied, the analytics component shall preserve item_id and price under the pinned shared contract.
Priority: P1. Verification: owner-run boundary check with attached source and contract identities. Acceptance: all required fields are preserved; missing required fields are rejected.

## Security, privacy and quality
Use synthetic data only. Preserve identity and do not infer deployment authority.

## Data and provenance
Pin the supplied interface definition and tested local snapshot bytes.

## User story
As this team's owner, I can verify my contribution without taking control of another repository.

## Validation and release gates
This fixture's approved status is illustrative. Real requirements/design/tasks each need their own supplied approval; local completion is not release.

## Decisions and remaining open questions
No production policy is resolved by this example. Adopter owner supplies real authority before use.

## Glossary
Boundary: the pinned catalog item interface shared by the three synthetic teams.

## Assumptions and change control
This is a preserved synthetic approved-plan snapshot. Material changes return to review.

## Organizational traceability
Initiative: catalog-expansion. Handoff: analytics-work.
Exact obligation RecordRef:
```json
{"digest": "sha256:4d3d4ee08d2f359f4469a23a442d081170cd5e37f412e1581bb77d9e9a703d57", "initiative_id": "catalog-expansion", "record_id": "catalog-api"}
```
Mapping: ANALYTICS-ORG-001 -> DESIGN-1 -> task 1. Disposition: implemented (allocated, not completed).
Current initiative/handoff digests are held separately to avoid content-hash cycles.

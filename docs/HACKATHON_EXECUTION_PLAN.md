# ClimateShield — Hack for Impact 2026 Execution Plan

> Internal team execution plan for the hackathon build.
>
> **Schedule convention:** The plan uses relative hackathon days and working-session time blocks so it remains aligned with the organizer's official timetable. Calendar dates should be filled from the event's confirmed schedule rather than invented locally.

> **Authority (D3).** This document is canonical for the **hackathon schedule**: Phase 0 and the
> three-day structure, wall-clock work blocks, the Golden Demo, submission preparation, and the
> schedule convention above.
>
> Engineering execution and governance — branching and PR workflow, CODEOWNERS, integration
> checkpoints and gates, team ownership, AI-tooling policy, communication cadence and the
> engineering Definition of Done — is owned by
> [`07-execution-plan.md`](./07-execution-plan.md).
> Product scope is owned by [`02-mvp-scope.md`](./02-mvp-scope.md).

## Team Ownership

| Team member | Primary responsibility |
|---|---|
| **Akhilesh** | Product ownership, AI/ML, system architecture |
| **Bhagavathianu** | Backend, database, APIs |
| **Karthik** | Frontend, dashboard, UI/UX |
| **Kirishwaran** | Data/research, policy engine, testing, presentation |

## Phase 0 — Pre-Hackathon Preparation

**When:** Before the official hackathon start

### 60–90 minute setup block

- Confirm GitHub collaborators and access.
- Protect `main` and use pull requests for shared changes.
- Confirm each person's ownership and branch naming.
- Verify local development environments.
- Review the problem statement and final product scope.
- Confirm the API/data contracts that cross team boundaries.

### 30–45 minute planning block

- Break work into small issues.
- Identify dependencies and integration points.
- Confirm the minimum viable demo.
- Keep optional features explicitly separate from the critical path.

## Phase 1 — Hackathon Day 1: Foundation

**Goal:** establish a working end-to-end skeleton.

### Opening block — 09:00–10:00

- Team sync.
- Confirm priorities and dependencies.
- Check repository and branch status.

### Build block — 10:00–13:00

**Akhilesh**
- Define Tier-1 burn-analysis inputs/outputs.
- Confirm risk-engine boundaries and architecture.

**Bhagavathianu**
- Backend/API and database foundation.
- Confirm shared persistence path.

**Karthik**
- Frontend application shell.
- Dashboard navigation and core page structure.

**Kirishwaran**
- Climate-data validation.
- Trigger/policy definitions and test scenarios.

### Integration block — 14:00–17:00

- Connect the first frontend → API → database path.
- Validate climate-data ingestion/fixtures.
- Run the first end-to-end scenario.

### Review block — 17:30–18:30

- Run tests.
- Review blockers.
- Update issues.
- Freeze the Day-1 scope.

## Phase 2 — Hackathon Day 2: Core Intelligence

**Goal:** make ClimateShield's climate-risk and insurance flow demonstrable.

### Morning block — 09:00–12:00

- Tier-1 burn analysis.
- Historical trigger evaluation.
- Risk score and risk-level calculation.
- Policy and trigger integration.

### Afternoon block — 13:00–17:00

- Dashboard integration.
- Policy display.
- Trigger simulation.
- Payout calculation/display.

### Evening integration block — 17:30–19:00

Target flow:

```text
Farm
  → Climate data
  → Historical burn analysis
  → Risk score
  → Policy
  → Simulated climate event
  → Trigger
  → Payout
  → Explanation
```

## Phase 3 — Hackathon Day 3: Integration & Reliability

**Goal:** one reliable golden-path demo.

### Morning — 09:00–12:00

- Connect all major modules.
- Resolve API/schema mismatches.
- Validate database behaviour.

### Afternoon — 13:00–16:30

- End-to-end testing.
- Edge cases.
- Error handling.
- Data-quality checks.

### Late afternoon — 16:30–18:00

- UI polish.
- Demo data preparation.
- Architecture diagram.
- Impact metrics and evidence.

## Final Submission / Demo Window

**Rule:** no major architectural features in the final window.

### T−4 hours

- Freeze feature scope.
- Run the complete test suite.
- Verify the golden path.

### T−3 hours

- Fix only high-impact bugs.
- Validate demo data.
- Verify fallback/offline behaviour where applicable.

### T−2 hours

- Final UI/presentation polish.
- Prepare architecture and impact explanation.
- Rehearse the demo.

### T−1 hour

- Final GitHub review.
- Confirm the exact commit/PR to submit.
- Prepare a backup demo path.

### Final window

- No risky refactors.
- No new experimental features.
- Submit the verified build and presentation.

## Golden Demo

The final demonstration should show:

1. Register/select a farm.
2. Show climate-risk analysis.
3. Show historical burn analysis and explainable risk factors.
4. Create/view a policy.
5. Simulate a qualifying climate event.
6. Detect the trigger.
7. Calculate the payout.
8. Explain the decision to the user.

## Definition of Done

A feature is considered complete only when:

- It works locally.
- Its API/data contract is documented where relevant.
- It has appropriate tests.
- It does not break another owner's work.
- It is integrated into the shared flow if it is on the critical path.
- Its demo behaviour is understandable without hidden manual steps.

## Scope Discipline

### Critical path

- Climate data
- Farm/location
- Tier-1 risk analysis
- Policy
- Trigger evaluation
- Payout calculation
- Dashboard
- End-to-end demo

### Optional if time remains

- Advanced ML models
- Advanced explainability
- Additional visualizations
- Extra automation
- Non-essential integrations

The team should prioritize a reliable end-to-end product over breadth.

## Development Workflow

```text
feature branch
     ↓
local tests
     ↓
Pull Request
     ↓
review
     ↓
merge to main
```

No direct feature work on `main`.

## Note on Schedule

This document intentionally does **not** fabricate calendar dates or commit timestamps. The official hackathon dates/times should be inserted once confirmed by the organizers. Relative day and time blocks are used so the execution plan remains accurate and auditable.
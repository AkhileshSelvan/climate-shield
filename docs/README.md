# ClimateShield — Planning Documentation

> **Status: PLANNING ONLY. No application code has been written.**
> This directory is the complete pre-implementation plan. Implementation begins only after sign-off.

**Project:** ClimateShield — AI-powered parametric climate-risk and insurance platform for smallholder farmers
**Event:** Hack for Impact 2026 — KCT · Theme: *AI for Climate Resilience*
**Constraints:** 30 hours · 4 developers · demo must survive venue Wi-Fi

## Read in this order

| # | Document | What it answers |
|---|----------|-----------------|
| 00 | [Repository Assessment](./00-repository-assessment.md) | What exists today, what is missing |
| 01 | [Architecture & Tech Stack](./01-architecture.md) | System design, every stack choice with rationale |
| 02 | [MVP Scope & User Journey](./02-mvp-scope.md) | MUST / SHOULD / NICE / NON-GOALS, end-to-end journey |
| 03 | [Data Model](./03-data-model.md) | Entities, relationships, ERD, key invariants |
| 04 | [API Design](./04-api-design.md) | Every endpoint, contracts, error model |
| 05 | [AI/ML Design](./05-ai-ml-design.md) | Risk engine math, where AI genuinely adds value |
| 06 | [Demo Script](./06-demo-script.md) | Timed 4:30 stage run |
| 07 | [Execution Plan](./07-execution-plan.md) | Git strategy, 4-person split, 30-hour timeline |
| 08 | [Risks & Fallbacks](./08-risks.md) | What will break and what we do instead |
| 09 | [Assumptions & Decisions](./09-assumptions-and-decisions.md) | Every assumption made, every ADR |

## The one-paragraph version

A smallholder farmer registers a farm by dropping a map pin and naming a crop and sowing date.
ClimateShield pulls 35 years of reanalysis weather for that grid cell, replays the crop calendar
year by year, and computes how often a rainfall-deficit trigger would have fired — producing a
trigger probability, a risk band, and an actuarially-derived premium in seconds. The farmer buys a
policy whose payout rule is a **frozen, machine-readable contract**. A deterministic engine
evaluates that contract daily against cached weather. When the index crosses a threshold, payout is
automatic — no claim, no adjuster, no discretion. AI does three jobs: it prices the risk, it warns
the farmer *before* the loss, and it explains all of it in the farmer's own language.

## Three principles that constrain every decision below

1. **The LLM never decides money.** Trigger evaluation is deterministic, versioned, and replayable.
   Claude explains outcomes; it never produces them. Every payout must be reproducible from stored
   inputs alone.
2. **The demo runs with the network unplugged.** All weather data is cached in Postgres before the
   demo. No live third-party call is on the critical path.
3. **Ship the floor before the ceiling.** Every AI component has a deterministic fallback that is
   built *first*. Burn analysis works with zero training data; the ML model is an enhancement layer
   on top, never a dependency.

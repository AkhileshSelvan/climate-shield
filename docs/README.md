# ClimateShield — Planning Documentation

> **Status: IMPLEMENTATION UNDER WAY.**
> Documents 00–09 are the approved plan. **[Document 10](./10-implementation-status.md) is the
> as-built record** — where it disagrees with 01–09, document 10 is current.

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
| **10** | **[Implementation Status](./10-implementation-status.md)** | **As-built: what exists, deviations, enforcement status, remaining work** |
| — | [Hackathon Execution Plan](./HACKATHON_EXECUTION_PLAN.md) | Schedule, phases, wall-clock blocks, Golden Demo, submission preparation |

**Where authority sits (D3).** Hackathon schedule, phases, Golden Demo and submission →
`HACKATHON_EXECUTION_PLAN.md` · engineering execution and governance, Git/PR workflow, CODEOWNERS,
gates, team ownership, AI-tooling policy, engineering Definition of Done → `07` · product scope → `02`.

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

1. **No AI component may authorise a payout.** Trigger evaluation is deterministic, versioned, and
   replayable. Claude explains outcomes; it never produces them. Enforced by an import-graph test
   that **fails the build** (MUST-have M15), not by good intentions.
2. **The system runs with the network unplugged.** The offline fixture system is a MUST-have
   feature (M14) with `FixtureProvider` as the *default* — not an emergency path. Gated at H12.
3. **Ship the floor before the ceiling.** Tier 1 burn analysis is mandatory and needs zero training
   data. Monte Carlo, LightGBM and Claude explanations are optional enhancements layered on top,
   never dependencies.

> **Status: approved 2026-08-17** with ten adjustments, all reflected below. The decision log is in
> [09 §0](./09-assumptions-and-decisions.md#0-sign-off--ratified-2026-08-17). Implementation has not
> started and begins only on instruction.

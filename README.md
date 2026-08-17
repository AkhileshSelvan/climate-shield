# ClimateShield

AI-powered parametric climate risk and insurance platform for smallholder farmers.

> **Status: planning. No application code has been written yet.**
> The complete pre-implementation plan lives in **[`docs/`](./docs/README.md)**.
> This README is rewritten with setup instructions once implementation begins.

**Hack for Impact 2026 — KCT** · Theme: *AI for Climate Resilience* · 30 hours · 4 developers

## The idea

A smallholder farmer registers a farm by dropping a map pin and naming a crop and sowing date.
ClimateShield replays 35 years of reanalysis weather for that grid cell against the crop calendar,
and returns a trigger probability, a risk band, and an actuarially derived premium in seconds. The
farmer buys a policy whose payout rule is a frozen, machine-readable contract. A deterministic
engine evaluates it daily against cached weather. When rainfall crosses a threshold, payout is
automatic — no claim, no surveyor, no discretion.

Traditional crop insurance cannot serve a 1.2-hectare plot: the loss assessment costs more than the
crop. Parametric insurance pays on a *measurement* instead of an *inspection*, which is what makes
the economics work at this scale.

## Where AI does the work

| Applied to | Method |
|-----------|--------|
| **Pricing** | 35-year historical burn analysis with climate-trend weighting, per grid cell |
| **Threshold optimisation** | LightGBM fitted to district yield loss — attacks basis risk directly |
| **Early warning** | Analogue-year projection + 16-day forecast — warns *before* the loss |
| **Accessibility** | Claude renders the numbers into Tamil or English a farmer can act on |

**AI does not decide payouts.** Trigger evaluation is deterministic, versioned, and replayable from
stored inputs alone. An insurance settlement that cannot be reproduced is not a product.

## Planning documentation

| Document | Contents |
|----------|----------|
| [00 · Repository Assessment](./docs/00-repository-assessment.md) | What exists, what is missing, environment findings |
| [01 · Architecture](./docs/01-architecture.md) | System design and every stack choice with rationale |
| [02 · MVP Scope](./docs/02-mvp-scope.md) | User journey · MUST / SHOULD / NICE / NON-GOALS |
| [03 · Data Model](./docs/03-data-model.md) | Entities, ERD, invariants |
| [04 · API Design](./docs/04-api-design.md) | Endpoints, contracts, error model |
| [05 · AI/ML Design](./docs/05-ai-ml-design.md) | Risk engine mathematics and model governance |
| [06 · Demo Script](./docs/06-demo-script.md) | Timed 4:30 stage run and Q&A prep |
| [07 · Execution Plan](./docs/07-execution-plan.md) | Git strategy · 4-person split · 30-hour sequence |
| [08 · Risks](./docs/08-risks.md) | Failure modes and fallbacks |
| [09 · Assumptions & ADRs](./docs/09-assumptions-and-decisions.md) | Every assumption and decision, with open questions |

## Proposed stack

Next.js 15 · TypeScript · Tailwind · Leaflet — FastAPI · Python 3.11 · SQLAlchemy —
PostgreSQL 16 + PostGIS (Supabase) — pandas · scikit-learn · LightGBM — Open-Meteo (ERA5) ·
NASA POWER — Claude — Vercel · Render

See [ADR-002](./docs/09-assumptions-and-decisions.md#adr-002--python-backend-not-node) for why the
backend is Python, and [§3 Open questions](./docs/09-assumptions-and-decisions.md#3-open-questions-for-the-project-owner)
for the decisions still awaiting sign-off.

## Licence

MIT — see [LICENSE](./LICENSE).

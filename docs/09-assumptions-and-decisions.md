# 09 — Assumptions & Architecture Decisions

The repository contained no specification, so this plan necessarily makes assumptions. Every one is
listed here with its basis and its blast radius if wrong. **Please correct any that are wrong before
implementation begins** — several are cheap to change now and expensive to change at hour 20.

## 1. Assumptions

### Context

| # | Assumption | Basis | If wrong |
|---|-----------|-------|----------|
| A1 | Target geography is **India, initially Tamil Nadu** (Coimbatore region) | KCT is in Coimbatore; MIT-licensed to an Indian author; ₹ and UPI are the natural fit | Low cost — swap seed districts, currency, crop calendars. Do this before H2. |
| A2 | Primary language pair is **Tamil + English** | Venue and target users | Low — `next-intl` catalogues are additive |
| A3 | Primary user is a **smallholder farmer (< 2 ha), phone-first, limited literacy** | Project statement | **High** — drives phone/OTP auth, map-pin input, vernacular explanation. Changing this changes the whole UX. |
| A4 | Demo season is **Kharif 2026, sowing June, maize** | Monsoon-dependent kharif is the clearest drought story | Low — seed data change |
| A5 | Judges value **working end-to-end demo + genuine technical depth** over feature count | Standard hackathon judging | Medium — would reprioritise SHOULDs |

### Product

| # | Assumption | Basis | If wrong |
|---|-----------|-------|----------|
| A6 | **Rainfall deficit** is the primary peril | Dominant smallholder risk in semi-arid Tamil Nadu | Medium — the engine is peril-agnostic; excess rain and heat are S10 |
| A7 | **Parametric only.** No loss assessment, no claims workflow | Core premise of the project | Very high — a claims workflow is a different product |
| A8 | We model **one insurer**; farmers do not shop between carriers | Scope | Low |
| A9 | Premium subsidy exists (PMFBY-style, ~75 %) | Indian crop insurance operates this way | Low — a configuration field |
| A10 | Payouts are **simulated**; no real money moves | Explicit NON-GOAL | Low |
| A11 | Sum insured is **per hectare × area**, farmer-selectable within product bounds | Standard practice | Low |

### Technical

| # | Assumption | Basis | If wrong |
|---|-----------|-------|----------|
| A12 | Team is comfortable with **Python and TypeScript/React** | The mainstream hackathon stack; `.gitignore` is a Python template | **High** — if the team is stronger in Node or Java, change the backend now. Familiarity beats elegance at 30 hours. |
| A13 | **Open-Meteo is reachable** from team laptops | Public keyless API — but **confirmed blocked from this session** | **High** — R1 fallbacks exist, but verify on a laptop in hour 1 |
| A14 | ~11 km reanalysis resolution is **acceptable for a prototype** | Only source with 35 years of consistent coverage | Medium — stated as a known limitation on stage |
| A15 | **Anthropic API access is available** for explanations | Tier 4 assumption | Low — static fallback strings; the demo does not depend on it |
| A16 | Free tiers (Supabase / Vercel / Render) suffice | Demo-scale data and traffic | Low |
| A17 | 35 years of daily weather for ~6 grid cells (~307k rows) is **trivial for Postgres** | It is | Low |
| A18 | Team has **4 developers for the full 30 hours** | Stated | Medium — with 3, cut all SHOULDs and merge roles C and D |

### Data

| # | Assumption | Basis | If wrong |
|---|-----------|-------|----------|
| A19 | **District-level crop yield data is obtainable** (ICRISAT / data.gov.in) | Public datasets exist | Medium — kills Tier 3 only; Tiers 1–2 unaffected |
| A20 | ERA5 precipitation is **adequate to compute a rainfall index**, without station calibration | Standard practice in index insurance research | Medium — stated as a limitation |
| A21 | Crop phase calendars can be **fixed per crop**, not per variety or per micro-climate | Simplification | Low — refinable later |
| A22 | Weather is **cached before** any demo, never fetched live during one | Design decision, reinforced by R1 | Low — this is the architecture, not an assumption about the world |

---

## 2. Architecture Decision Records

### ADR-001 · Modular monolith, not microservices
**Decision:** one FastAPI application with clear internal service boundaries.
**Why:** four developers and thirty hours. Microservices would add deployment surface, network
failure modes, and cross-service contracts to buy independent scaling we do not need. The directory
boundaries give us the *organisational* benefit — clean ownership — without the operational cost.
**Trade-off:** everything scales together. Irrelevant at this scale.
**Revisit:** if the risk engine ever needs independent GPU-backed scaling.

### ADR-002 · Python backend, not Node
**Decision:** FastAPI + SQLAlchemy.
**Why:** the risk engine is pandas/NumPy/scikit-learn work. A Node backend forces a second Python
service and an inter-service contract — an integration seam we cannot afford. FastAPI's OpenAPI
generation is also the mechanism that makes four-way parallelism function.
**Trade-off:** the team writes two languages. Unavoidable with a React frontend regardless.
**Rejected:** Node + separate Python ML service (integration cost); Django (fighting its admin);
Flask (no schema generation).

### ADR-003 · Deterministic trigger engine — no ML, no LLM, ever
**Decision:** trigger evaluation is pure arithmetic over stored inputs.
**Why:** an insurance settlement must be reproducible, auditable, and identical on re-run. A model
in that path means a payout cannot be explained or defended six months later. This is also the
single clearest answer to the "is your AI trustworthy?" question — the AI is not in that path.
**Trade-off:** none. Sophistication belongs in *pricing* and *warning*, not in settlement.
**Status:** non-negotiable. Any proposal to relax this is a proposal to change the product.

### ADR-004 · Cache-first weather; providers are batch sources only
**Decision:** all weather reads serve from `weather_observation`. No request-time upstream calls.
**Why:** auditability first — a parametric contract must settle against a stored, versioned dataset,
not an unrecorded live response. Demo reliability, speed, and rate-limit immunity follow for free.
**Confirmed necessary:** all three providers are blocked from this environment.
**Trade-off:** data can be up to 24 hours stale. Correct for a daily-settled product.

### ADR-005 · Freeze the trigger definition onto each policy
**Decision:** `policy.trigger_definition` is a JSONB snapshot, immutable after issuance.
**Why:** product templates get tuned during a hackathon, sometimes at 4am. If policies referenced a
live template, editing a product would silently rewrite contracts farmers already hold, and today's
payout would not match yesterday's contract. Every issued policy must be independently interpretable
forever.
**Trade-off:** template fixes do not propagate to existing policies. That is the point.
**Enforcement:** database trigger blocking `UPDATE` on non-draft policies.

### ADR-006 · Own JWT auth, not Supabase Auth
**Decision:** phone + OTP issued and verified by FastAPI; Supabase used for Postgres only.
**Why:** Supabase Auth is good, but its email-confirmation and OAuth redirect flows add setup time
and put a live third-party call in the first thirty seconds of the demo. Mock OTP is instant,
offline, and demonstrates the same UX.
**Trade-off:** we implement token handling ourselves (~2 hours, well-understood).
**Revisit:** post-hackathon, Supabase Auth or a real SMS provider is the natural upgrade.

### ADR-007 · Tiered payouts, not binary triggers
**Decision:** stepped payout tiers (25 / 50 / 100 %).
**Why:** a binary trigger creates a cliff — 121 mm pays nothing, 119 mm pays everything. That
discontinuity is a major source of perceived unfairness and a real driver of basis risk. Tiers are
what actual weather-index products use.
**Trade-off:** one extra loop in the evaluator, and slightly more explaining. Both cheap.

### ADR-008 · Grid cells, not per-farm weather
**Decision:** farms snap to ~0.1° cells; weather is stored per cell.
**Why:** a thousand farms in one block would otherwise store a thousand identical copies of 35 years
of daily weather (~12.8M rows for ~12.8k rows of information). The cell design is also *why the
economics work* at 1.2 ha — marginal cost per farmer is one database row and a hundred milliseconds
of arithmetic.
**Trade-off:** all farms in a cell see the same weather. Inherent to index insurance at this
resolution, and disclosed rather than hidden.

### ADR-009 · Leaflet + OpenStreetMap, not Mapbox or Google Maps
**Decision:** Leaflet with OSM tiles.
**Why:** no API key, no billing account, no secret to distribute across four laptops or leak in a
commit. Saves 30 minutes of signup and removes a credential from the demo path.
**Trade-off:** less polished tiles. Invisible at demo zoom levels.

### ADR-010 · Trunk-based development, not GitFlow
**Decision:** short-lived branches straight off `main`, squash merges, 6-hourly checkpoints.
**Why:** `develop` plus release branches add merge hops that pay for release management we do not
have. `main` must be demo-able at every hour, which trunk-based enforces directly.
**Trade-off:** requires discipline about branch lifetime. Enforced by the < 4h rule.

### ADR-011 · Store no financial or identity PII
**Decision:** no Aadhaar, no PAN, no bank account numbers — not even masked. `bank_verified` is a
boolean.
**Why:** a hackathon prototype has no business holding them, and a boolean carries all the
information the demo needs. Stating this on stage is a credibility gain, not a gap.
**Trade-off:** real disbursement would need a KYC layer. Explicitly a NON-GOAL.

### ADR-012 · Build the deterministic floor before the ML ceiling
**Decision:** Tier 1 burn analysis ships first and is never on the critical path of a later tier.
**Why:** it needs no training data and cannot fail to produce an answer. If every ML component
collapses at hour 20, the product is still complete. It is also genuinely the right method — it is
what reinsurers use — so this is a strong baseline, not a placeholder.
**Trade-off:** none. Each tier is independently valuable.

---

## 3. Open questions for the project owner

Answers to Q1–Q3 could change the plan materially and are worth resolving before H0.

| # | Question | Why it matters | Default if unanswered |
|---|----------|----------------|----------------------|
| **Q1** | Is the team comfortable with **Python + React**? | ADR-002 is the plan's biggest single lever. Familiarity beats elegance at 30 hours. | Proceed with FastAPI + Next.js |
| **Q2** | Is **Anthropic API access** available to the team? | Determines whether Tier 4 explanation is real or static | Build with static fallbacks; wire the API if a key appears |
| **Q3** | Any **hackathon-mandated stack, sponsor tooling, or required integration**? | Sponsor tracks often carry required services and bonus points | Assume none |
| Q4 | Is **Tamil** the right second language, or Hindi/Telugu/Kannada? | Seed catalogues and demo narration | Tamil |
| Q5 | Is the demo **live-presented** or **pre-recorded**? | Changes how hard the H26 freeze is defended | Live, with a recorded backup |
| Q6 | Confirm **4 developers for the full 30 hours**? | With 3, all SHOULDs are cut and roles C+D merge | 4 developers |
| Q7 | Preferred deployment accounts (Vercel / Render / Supabase) already exist? | Signup friction during the event | Create at H0 |

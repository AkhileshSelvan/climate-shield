# 02 — MVP Scope & User Journey

## 1. The complete user journey

```mermaid
sequenceDiagram
    autonumber
    actor F as Farmer
    participant W as Next.js
    participant A as FastAPI
    participant R as Risk engine
    participant T as Trigger engine
    participant DB as Postgres
    participant C as Claude

    rect rgb(20,40,60)
    Note over F,DB: 1 · Onboard
    F->>W: Enter phone → OTP
    W->>A: POST /auth/otp/verify
    A-->>W: JWT (role=farmer)
    end

    rect rgb(20,55,40)
    Note over F,DB: 2 · Register farm
    F->>W: Drop map pin · crop · sowing date
    W->>A: POST /farms → POST /farms/{id}/plantings
    A->>DB: farm + planting; snap to weather grid cell
    A-->>W: farm_id, planting_id, grid_cell_id
    end

    rect rgb(55,40,20)
    Note over F,C: 3 · AI risk assessment
    W->>A: POST /risk/assess {planting_id}
    A->>DB: load 35 yrs cached daily weather for cell
    A->>R: replay crop calendar × 35 seasons
    R-->>A: trigger_probability · expected_loss · pure premium · risk band
    A->>DB: persist risk_assessment (model_version, features)
    A-)C: explain(structured numbers, lang=ta)
    C--)A: vernacular narrative (cached)
    A-->>W: assessment + explanation + historical trigger years
    end

    rect rgb(45,25,60)
    Note over F,DB: 4 · Quote → policy
    F->>W: Choose product · sum insured
    W->>A: POST /quotes
    A-->>W: premium breakdown + trigger contract in plain language
    F->>W: Accept
    W->>A: POST /policies
    A->>DB: policy with FROZEN trigger_definition, status=active
    end

    rect rgb(25,50,55)
    Note over F,T: 5 · Monitor (daily, automatic)
    loop every day 06:00 IST
        A->>A: ingest weather → weather_observation
        A->>T: evaluate all active policies
        T->>DB: policy_evaluation (index values, source, engine_version)
        alt approaching threshold
            T->>DB: alert(type=early_warning)
            A-->>F: "68% chance of trigger in 12 days"
        end
    end
    end

    rect rgb(60,25,30)
    Note over F,DB: 6 · Trigger → payout
    T->>T: index 82mm < tier 90mm → payout_pct = 50
    T->>DB: payout(amount, status=pending) → approved → disbursed
    T->>DB: ledger_entry (append-only)
    A-->>F: "₹36,000 credited · UPI/CS/…"
    F->>W: Open audit view → exact values, source, timestamp
    end
```

### The journey in prose

1. **Onboard.** Phone number, OTP, in. No email, no password, no KYC wall. Two screens.
2. **Register farm.** The farmer drops a pin on a map — this is the entire geo input. Area is
   drawn or typed. Crop and sowing date follow. Behind the scenes the farm is snapped to a ~0.1°
   weather grid cell, which is what all downstream weather work keys on.
3. **Risk assessment.** The system loads 35 years of daily reanalysis weather for that cell,
   aligns each historical season to the same sowing calendar, computes the flowering-window
   rainfall index for each, and asks: *how often would this contract have paid?* Out comes a
   trigger probability, an expected loss ratio, a risk band, and an actuarially derived premium.
   Claude renders it into Tamil or English at a level a farmer can act on.
4. **Policy creation.** The farmer sees the payout rule stated as money and millimetres, not legal
   prose. On acceptance, the trigger definition is **frozen onto the policy** — the contract is now
   immutable, whatever happens to the product template.
5. **Monitoring.** Every day the engine re-ingests weather and re-evaluates every active policy.
   The dashboard tracks season-to-date rainfall against the threshold with days remaining. When the
   forecast plus historical analogues push trigger probability up, an **early warning** fires — the
   farmer learns about the drought *before* the loss, with time to irrigate or adjust. This is the
   step that makes the product about resilience rather than only compensation.
6. **Trigger and payout.** The index crosses a tier. A payout record is created automatically —
   no claim filed, no adjuster dispatched, no discretion applied. Status walks to disbursed, a
   mock UPI reference is issued, and the farmer sees the money. The audit view shows the exact
   millimetres, the dataset, and the engine version that produced the decision.

## 2. MUST HAVE — the demo does not exist without these

Ordered by build dependency. Item *n* generally unblocks item *n+1*.

| # | Feature | Definition of done | Owner |
|---|---------|--------------------|-------|
| M1 | Phone + OTP auth (mock code `123456`), JWT, roles | Farmer logs in and reaches a session-scoped dashboard | A |
| M2 | Farm registration — map pin, area, district; crop + sowing date | Farm and planting persisted, snapped to a grid cell | A + C |
| M3 | Weather ingestion + cache: ≥30 yrs daily for ≥4 demo districts | `weather_observation` populated; API reads **only** from cache; provider selected by `WEATHER_PROVIDER` | B |
| M4 | Crop calendar + phase-wise index computation | Given planting + year → cumulative rainfall, CDD, heat index for each phase | B |
| M5 | **Burn-analysis risk engine** → trigger probability, expected loss, risk band, pure + gross premium | `POST /risk/assess` returns a full, persisted assessment in < 3 s | B |
| M6 | Products + quote → **policy issuance with frozen trigger definition** | Policy row carries an immutable `trigger_definition` snapshot | A |
| M7 | **Deterministic trigger engine**, tiered payouts, idempotent, audited | Re-running evaluation changes nothing; every run writes `policy_evaluation` | B |
| M8 | Monitoring dashboard — season-to-date index vs threshold, days remaining | Farmer sees live position against their contract | C |
| M9 | **Admin weather-simulation endpoint + console** | One click injects a drought scenario and re-evaluates — *the demo lever* | B + D |
| M10 | Automatic payout creation, state machine, mock UPI disbursement | Trigger → payout → disbursed with no human input | B |
| M11 | Alert / notification feed | Early-warning, trigger, and payout events visible to the farmer | C |
| M12 | **Audit view** of an evaluation | Exact index values, data source, engine version, timestamp | C |
| M13 | Deployed public URL **or** rehearsed offline `docker-compose` demo | The 4:30 script runs start to finish, twice, without intervention | A |
| **M14** | **Offline fixture & replay system** — committed 35-yr weather, `FixtureProvider`, `make seed` / `demo-reset` / `demo-offline` | **The complete happy path runs with the network interface disabled.** Verified at H12, re-verified at H24 | **B** |
| **M15** | **Architectural fitness test** — build fails if `services/trigger` or `services/payout` imports any AI module | The separation is enforced by CI, not by intention | **B** |

**M9 deserves a note.** The simulation endpoint is not a hack bolted on at hour 28 — it is the
mechanism by which a 90-day insurance event becomes a 20-second stage moment. It is designed in
from the start, built by hour 16, and rehearsed. Treating it as a first-class MUST is the single
most important scoping decision in this document.

**M14 is the second.** Promoting the offline fixture system from a fallback to a MUST changes when
it gets built — H12, not H26 — and that is the entire point. A fallback built under pressure at
hour 26 has never been exercised; a default provider used hundreds of times during development
works when the venue Wi-Fi does not. Making `FixtureProvider` the *default* rather than the
*emergency* option is what makes the guarantee real.

**M15 makes principle 6 checkable.** An invariant nobody can verify is a comment. This one is a
failing build.

## 3. SHOULD HAVE — build after all MUSTs are green

| # | Feature | Value | Owner |
|---|---------|-------|-------|
| S1 | Claude plain-language risk explanation | Turns a number into a decision a farmer can act on | D |
| S2 | Tamil ⇄ English toggle (`next-intl`) | Credibility with a Tamil Nadu judging panel; genuine accessibility | D |
| S3 | Early-warning trigger probability (forecast + analogue years) | The *resilience* beat — warns before the loss, not after | B |
| S4 | Historical trigger-years chart (which of 35 years would have paid) | Makes the risk model legible in one glance | D |
| S5 | Monte Carlo pricing (10k draws over fitted distributions) | Smoother estimate than 35 samples | B |
| S6 | LightGBM threshold optimisation / basis-risk score | The strongest "real ML" claim available to us | B |
| S7 | Policy certificate (PDF + QR) | Tangible artifact; farmers trust paper | D |
| S8 | Admin portfolio view — exposure, expected loss, solvency | Shows we understand the *insurer* side, not just the farmer side | D |
| S9 | Unit tests on index-window arithmetic | The one place a silent wrong number would humiliate us on stage | B |
| S10 | Multi-peril: excess rainfall + heat stress alongside deficit | Breadth of cover | B |
| S11 | Rate limiting on OTP request | Basic abuse resistance | A |

## 4. NICE TO HAVE — only if genuinely ahead of schedule

N1 real SMS/WhatsApp delivery · N2 satellite NDVI cross-check for basis risk · N3 Razorpay test-mode
payments · N4 offline PWA with service worker · N5 Tamil voice/IVR interface · N6 reinsurance pool
solvency simulation · N7 multi-season portfolio backtesting UI · N8 DigiLocker KYC · N9 agent-assisted
enrolment role · N10 weather-station ground-truth comparison.

## 5. NON-GOALS — explicitly not building, and here is why

This list exists to be pointed at when someone has a great idea at 2am. It is a scope defence, and
using it is not defeat.

| Not building | Reason |
|--------------|--------|
| **Blockchain / smart-contract settlement** | Adds a wallet, a chain, gas, and a demo failure mode. Solves a trust problem our audit log already solves. The most common way this exact project gets worse. |
| **IoT soil sensors / drone imagery** | No hardware, no time, and satellite reanalysis is the right data layer anyway |
| **Native mobile app** | A responsive PWA is visually identical on stage and costs a fraction of the time |
| **Real money movement** | Payments compliance is not a 30-hour problem |
| **Real KYC (Aadhaar/PAN)** | We deliberately store no such data — see [01 §6](./01-architecture.md) |
| **IRDAI regulatory compliance** | Correct to acknowledge in the pitch, impossible to implement |
| **Multi-tenant insurer SaaS** | Distracts from the farmer story judges are evaluating |
| **Custom ML training infrastructure** | Burn analysis needs none; LightGBM trains in seconds on a laptop |
| **Microservices** | Four developers, thirty hours. A modular monolith is the correct architecture here and we should say so confidently. |

## 6. Scope discipline rules

0. **Nothing outside the MUST / SHOULD / NICE lists above gets built without explicit approval from
   the project owner.** This list is the agreed scope, ratified at sign-off. A good idea that is not
   on it is a good idea for after the hackathon. Anyone may *propose* an addition; only the owner
   can authorise one, and the proposal must state what it replaces and who stops working on what.
1. **No new MUST after H8.** The list above is frozen at kickoff.
2. **A SHOULD may only start when every MUST is merged to `main` and smoke-tested.**
3. **Nothing new after H26 (demo freeze).** Bug fixes only, on `hotfix/*`.
4. Any proposed addition must name **the feature it replaces**. Scope is a fixed-size container.
5. If a MUST is at risk at H20, cut a SHOULD immediately — do not compress the rehearsal window.
   Rehearsal time is not slack; it is the deliverable.

### Scope-change protocol

| Step | Who |
|------|-----|
| Propose in the team channel, naming the feature it replaces and the hours it costs | Anyone |
| Approve or decline | **Project owner only** |
| Record in `docs/09` as an amendment if approved | Dev D |

Rejecting a proposal under this protocol is not a judgement about the idea. Say "not this
hackathon" and move on — the list of things we deliberately did not build is in §5, and it is a
sign of discipline, not of limitation.

# 11 — Tier-1 Burn Analysis Risk Engine

> **Status: implemented.** Engine `burn-analysis-v1.0`, trigger semantics `trigger-v1.1`.
> Owner: Akhilesh ([#4](https://github.com/AkhileshSelvan/climate-shield/issues/4)).
> Design rationale lives in [05 §3](./05-ai-ml-design.md); this document is the contract.

## 1. Purpose

Estimate how often a given parametric trigger *would have fired* at a given location, by replaying
history season by season. It answers one question:

> Of the past N seasons at this grid cell, how many would have paid out under these exact terms?

Burn analysis is what reinsurers actually use to price weather-index products. It requires no
training data, cannot fail to produce an answer when data exists, and is explainable in one
sentence: *"8 of the last 35 seasons would have paid."*

**The engine estimates. It never settles.** No risk output authorises, creates or influences a
payout — the deterministic trigger and evaluation engine remains the sole authority. This is
enforced by `tests/test_architecture.py`, which fails the build on violation.

## 2. Pipeline

```
weather_observations (cache, offline)
        │
        ▼
build_season_windows()      one window per year, same calendar position
        │
        ▼
coverage check              incomplete seasons excluded, never zero-filled
        │
        ▼
trigger_engine.evaluate_trigger()   ← the SAME function that settles policies
        │
        ▼
burn count → trigger_frequency → risk_score → classify()
        │
        ▼
explainable result + per-year evidence
```

## 3. Inputs

| Input | Required | Notes |
|-------|----------|-------|
| `farm_id` **or** `latitude`+`longitude` | yes | Farm resolves to its grid cell; coordinates snap to one |
| `trigger_type` | yes | `drought` \| `excess_rain` — validated by the trigger engine |
| `threshold_mm` | yes | Millimetres of cumulative rainfall |
| `window_days` | yes | Window length; spans `window_days + 1` dates, inclusive |
| `season_end` | no | Anchor date. **Pin it for a reproducible result**; defaults to today |
| `lookback_years` | no | Default 35, max 100 |
| `min_coverage` | no | Default 0.8 — fraction of window days that must be present |

Crop is carried through from the farm record and echoed in `context`; it does not yet affect the
calculation. Crop-specific phase calendars are the natural next refinement.

## 4. Algorithm

For each year *y* from `season_end.year - lookback_years + 1` to `season_end.year`:

1. **Window.** `end = season_end.replace(year=y)`, `start = end - window_days`. Both ends inclusive.
   Aligning every season to the same calendar position is what makes years comparable; a 29 February
   anchor falls back to the 28th rather than dropping the season.
2. **Load.** Read cached observations in `[start, end]`. Cache only — no provider is consulted, so
   this runs offline.
3. **Coverage.** `coverage = observations_used / expected_days`. If `coverage < min_coverage`, the
   season is **ineligible**, recorded with a reason, and excluded from both numerator and
   denominator.
4. **Evaluate.** `total_mm = sum(precipitation)`, then
   `trigger_engine.evaluate_trigger(trigger_type, total_mm, threshold_mm)`.

Then:

```
eligible_years    = count of eligible seasons
triggered_years   = count of eligible seasons where the trigger fired
trigger_frequency = triggered_years / eligible_years        (4 dp)
risk_score        = trigger_frequency × 100                 (2 dp)
```

### Why the transformation is linear

`risk_score = trigger_frequency × 100` — no curve, no weighting, no tuning constants. A farmer told
"8 of 35 seasons, so 22.86" can check the arithmetic. Any smoothing belongs in a later tier and must
be declared as such.

**Precision is capped deliberately.** The input is a ratio of small integers; four decimals on the
frequency and two on the score is the honest limit. More digits would imply precision the sample
size cannot support.

## 5. Risk classification

| Score | Level | Meaning |
|-------|-------|---------|
| 0 – <10 | `LOW` | Historically reliable rainfall in this window |
| 10 – <25 | `MEDIUM` | Roughly one failure in every 4–10 seasons |
| 25 – <40 | `HIGH` | Roughly one failure in every 3 seasons |
| ≥40 | `SEVERE` | Marginal for this crop in this window |
| — | `UNKNOWN` | Not enough data to judge; `risk_score` is `null` |

Published at `GET /api/v1/risk/bands` so clients need not hard-code them.

## 6. Data quality states

The engine reports a state rather than manufacturing confidence.

| `data_quality` | Condition | `risk_score` |
|----------------|-----------|--------------|
| `sufficient` | ≥10 eligible seasons | produced |
| `limited` | 1–9 eligible seasons | produced, flagged |
| `insufficient` | 0 eligible seasons | **`null`**, level `UNKNOWN` |

`confidence` is derived: `high` (≥25 eligible), `medium` (≥10), `low` (≥1), `none` (0).

> **Missing days are never counted as zero rainfall.** A gap read as zero manufactures a drought
> that never happened. Incomplete seasons are excluded and reported.

## 7. Data honesty

Every result carries provenance:

- **`data_source`** — the source strings behind the observations used (e.g. `["fixture"]`)
- **`is_simulated`** — true if any observation was demo-injected
- **`factors`** — includes a `fixture_data` entry when fixtures were used, stating plainly that the
  bundled fixtures are **synthetic, generated from published regional normals — not measurements**

Synthetic history is never presented as real observation. Run `make fixtures-live` to replace the
bundled fixtures with real ERA5 data.

## 8. API contract

### `POST /api/v1/risk/analyze`

```jsonc
{ "farm_id": 1,                    // or latitude + longitude
  "trigger_type": "drought",
  "threshold_mm": 60.0,
  "window_days": 30,
  "season_end": "2026-08-17",      // pin for reproducibility
  "lookback_years": 35,
  "min_coverage": 0.8 }
```

### `POST /api/v1/risk/analyze/policy/{policy_id}`

Runs the same analysis using a policy's **frozen** trigger terms. Read-only; the policy is not
modified and no evaluation is recorded. Body is optional: `{ "season_end": …, "lookback_years": … }`.

### `GET /api/v1/risk/bands`

The classification table.

### Response

```jsonc
{ "risk_score": 22.86, "risk_level": "MEDIUM",
  "risk_level_meaning": "Roughly one failure in every 4-10 seasons",
  "trigger_frequency": 0.2286,
  "historical_years": 35, "eligible_years": 35, "triggered_years": 8,
  "triggered_year_labels": [1994, 2002, 2003, 2012, 2016, 2019, 2023, 2024],
  "total_observations_used": 1085,
  "trigger_definition": { "trigger_type": "drought", "threshold_mm": 120.0,
                          "window_days": 30, "season_end": "2026-08-17",
                          "semantics": "evaluated by trigger-v1.1 evaluate_trigger" },
  "data_source": ["fixture"], "is_simulated": false,
  "data_quality": "sufficient", "confidence": "high",
  "engine_version": "burn-analysis-v1.0",
  "context": { "grid_cell_id": 1, "latitude": 11.0, "longitude": 77.0,
               "farm_id": 1, "crop": "maize", "location": "Pollachi, Coimbatore",
               "period_start_year": 1992, "period_end_year": 2026 },
  "factors": [ { "factor": "…", "detail": "…", "direction": "…" } ],
  "years": [ { "year": 2026, "observed_mm": 42.6, "triggered": true,
               "eligible": true, "coverage": 1.0, "ineligible_reason": null } ] }
```

`years` is the evidence behind the score and drives the demo chart.

## 9. Worked example (real output, current fixtures)

Pollachi, maize, drought below 60 mm over 30 days, 35-year lookback:

```
risk_score        50.0            risk_level        SEVERE
trigger_frequency 0.5             data_quality      limited
historical_years  35              confidence        low
eligible_years    2               data_source       ["fixture"]
triggered_years   1               is_simulated      false
triggered years   [2026]          engine_version    burn-analysis-v1.0
```

**Read that carefully — it is the engine being honest, not the engine being wrong.** The bundled
fixtures span two years, so 33 of 35 seasons were excluded for incomplete records and the result is
flagged `limited` / `low`. A `SEVERE` label off two seasons is not a trustworthy number, and the
response says so in its factors.

The demo target — 35 eligible years, 8 triggered, 22.86%, MEDIUM — needs 35 years of real data.
That is `make fixtures-live`, not a code change. Until then, the numbers on screen must come from
whatever the dataset actually supports.

## 10. Assumptions

1. **Cumulative rainfall over a rolling window** is the index. No phase weighting, no crop calendar.
2. **Grid-cell resolution (~0.1°, ~11 km)** is adequate. Every farm in a cell shares its history.
3. **Calendar alignment** approximates a season. Real crop calendars anchor to sowing date; that
   requires a sowing date the model does not yet carry.
4. **Each season is independent.** Multi-year drought correlation is not modelled.
5. **The historical distribution is stationary.** It is not — climate is shifting. Trend weighting is
   documented in [05](./05-ai-ml-design.md) and deliberately excluded from v1.0.
6. **80 % coverage** makes a season representative. A configurable convention, not a derived value.

## 11. Limitations

- **Small samples are fragile.** With 35 seasons, one extra dry year moves the score by 2.86 points.
  A tail risk can be missed entirely. `data_quality` and `confidence` exist to say so.
- **No trend adjustment**, so the estimate under-weights recent warming.
- **Crop is carried but unused** in the calculation.
- **Not actuarially validated.** This is a technical estimate, not a filed premium basis.
- **Bundled fixtures are synthetic.** Every number is provisional until `make fixtures-live` runs.
- **Partial windows are scored against the full threshold.** *(known limitation — open for policy
  review)* A season passing the 80 % coverage gate has the sum of its *observed* days compared
  against the whole-window threshold, so the missing days behave as zero rainfall. A 31-day window
  at 4 mm/day reads as 100 mm over 25 observed days and breaches a 120 mm drought threshold, where
  the same regime fully observed reads 124 mm and does not. The bias runs both ways: it inflates
  drought frequency and suppresses excess-rain frequency. It does not affect the bundled demo,
  whose fixtures are contiguous so every season is at 100 % coverage, but it will affect any cache
  populated with real, gappy ingestion. Deliberately **not** changed in v1.0: the options are to
  require complete coverage for evaluation, to normalise the observed sum to the window, or to
  keep the current behaviour and disclose it. Each is a product decision about what a partially
  observed season *means*, not a bug fix, and the choice is owned by the product owner.

## 12. Architecture

```
services/risk/
├── burn_analysis.py     PURE — stdlib + trigger_engine only. No DB, no network, no ML.
├── classification.py    PURE — score and bands.
└── service.py           DB orchestration. Reads the cache; writes nothing.
```

Guaranteed by `tests/test_architecture.py`:

| Guarantee | Test |
|-----------|------|
| Risk cannot import `payout_engine` or `evaluation` | `test_risk_engine_cannot_reach_payout_or_settlement` |
| Risk never constructs `Payout` or `Trigger` | `test_risk_engine_never_constructs_a_payout_or_trigger` |
| The risk router performs no writes | `test_risk_api_exposes_no_write_endpoint` |
| The pure layer has no database dependency | `test_risk_pure_layer_has_no_database_dependency` |
| Burn analysis calls the trigger engine rather than restating it | `test_burn_analysis_reuses_the_trigger_engine` |
| No Tier-2/3 ML imports (sklearn, lightgbm, torch, …) | `test_risk_engine_cannot_reach_payout_or_settlement` |

The dependency runs one way only: risk → trigger engine. The trigger engine's own fitness test
forbids it importing risk, so the two can never become circular.

## 13. Version history

| Version | Change |
|---------|--------|
| `burn-analysis-v1.0` | Initial Tier-1: calendar-aligned windows, coverage gating, linear score, four-band classification, per-year evidence, provenance flags |

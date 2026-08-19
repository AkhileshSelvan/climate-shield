# 04 — Backend API Design

FastAPI, base path `/api/v1`. OpenAPI served at `/openapi.json`; the frontend generates its typed
client from it.

> **The contract is the coordination mechanism.** Pydantic schemas for every request and response
> are written and merged in the first two hours — *before* the handlers exist. Dev C then builds
> against a generated, typed client instead of waiting for Dev A. This single practice is what makes
> four-way parallelism work; everything else in [07](./07-execution-plan.md) depends on it.

## 1. Conventions

- **Auth:** `Authorization: Bearer <jwt>` on everything except `/auth/*` and `/healthz`.
- **Ownership is enforced server-side on every route.** A farmer requesting another farmer's policy
  gets `404`, not `403` — we do not confirm the existence of resources they cannot see.
- **Errors** are uniform and machine-readable:
  ```json
  { "error": { "code": "TRIGGER_WINDOW_NOT_ELAPSED",
               "message": "Policy cannot be evaluated before day 75.",
               "details": { "current_day": 62, "required_day": 75 } } }
  ```
- **Money** is serialised as a string decimal (`"2150.00"`) with an explicit `currency` field.
  Floats are never used for currency, in transit or at rest.
- **Lists** are paginated: `?page=1&page_size=20` → `{ items, total, page, page_size }`.
- **Idempotency:** `POST /policies` and `POST /payouts/{id}/disburse` accept `Idempotency-Key`.
- **Status codes:** `200` ok · `201` created · `400` validation · `401` unauthenticated ·
  `403` role denied · `404` not found/not owned · `409` state conflict · `422` Pydantic ·
  `429` rate-limited.

## 2. Endpoints

### 2.1 Auth

| Method | Path | Body → Response | Notes |
|--------|------|-----------------|-------|
| `POST` | `/auth/otp/request` | `{phone}` → `{request_id, expires_in}` | Dev mode returns `debug_code: "123456"` and never calls an SMS gateway |
| `POST` | `/auth/otp/verify` | `{phone, code}` → `{access_token, refresh_token, user}` | Creates the user on first verify |
| `POST` | `/auth/refresh` | `{refresh_token}` → `{access_token}` | |
| `GET` | `/auth/me` | → `{user, farmer_profile}` | |
| `PATCH` | `/auth/me` | `{full_name?, preferred_language?}` | Language toggle persists here |

### 2.2 Farms & plantings

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/farms` | `{name, latitude, longitude, area_ha, district, state, soil_type?, irrigation_type?}` → farm. **Server snaps to a grid cell and returns `grid_cell_id`** |
| `GET` | `/farms` | Caller's farms (admin/agent may filter by `owner_id`) |
| `GET` | `/farms/{id}` | Farm + latest planting + active policy summary |
| `PATCH` | `/farms/{id}` | Update; re-snaps the cell if coordinates change |
| `DELETE` | `/farms/{id}` | `409` if an active policy exists |
| `POST` | `/farms/{id}/plantings` | `{crop_id, season, sowing_date, sown_area_ha, expected_yield?}` → planting with derived `expected_harvest_date` |
| `GET` | `/farms/{id}/plantings` | History across seasons |
| `GET` | `/plantings/{id}` | Planting + crop phase calendar resolved to real dates |

### 2.3 Reference data

`GET /crops` · `GET /crops/{id}` (includes phase calendar) · `GET /products?crop_id=&district=` ·
`GET /products/{id}` · `GET /districts`.

### 2.4 Risk assessment — the AI surface

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/risk/assess` | `{planting_id, product_id?}` → full assessment. Runs burn analysis over cached weather, persists a `risk_assessment`, returns in < 3 s |
| `GET` | `/risk/assessments/{id}` | Retrieve, including cached explanations |
| `GET` | `/plantings/{id}/risk-history` | All assessments for a planting (model drift is visible) |
| `POST` | `/risk/explain` | `{assessment_id, language}` → Claude narrative. **Cache-first**: returns the stored explanation if present; generates and stores otherwise |

Response shape for `POST /risk/assess`:

```json
{
  "id": "…", "model_version": "burn-analysis-v1.2", "assessed_at": "2026-06-14T08:12:00Z",
  "trigger_probability": 0.2286,
  "expected_loss_ratio": 0.1143,
  "risk_band": "medium",
  "confidence": "high",
  "premium": { "pure": "6858.00", "risk_margin": "1029.00", "expense_loading": "788.00",
               "gross": "8675.00", "subsidy": "6506.00", "farmer_pays": "2169.00",
               "currency": "INR" },
  "basis": { "years_analysed": 35, "years_triggered": 8,
             "trigger_years": [1994, 2002, 2003, 2012, 2016, 2019, 2023, 2024],
             "mean_index_mm": 168.4, "std_index_mm": 52.1, "threshold_mm": 120,
             "data_completeness_pct": 99.8 },
  "drivers": [
    { "factor": "rainfed_irrigation", "impact": "+18%", "direction": "increases_risk" },
    { "factor": "flowering_window_overlaps_monsoon_break", "impact": "+11%",
      "direction": "increases_risk" },
    { "factor": "recent_decade_trend", "impact": "+7%", "direction": "increases_risk" }
  ],
  "explanation": { "en": "…", "ta": "…" }
}
```

`drivers` matters: a bare probability is not actionable. Naming *why* the number is what it is
turns a score into a decision — and it is computed from the burn analysis, not narrated by an LLM.

### 2.5 Quote & policy

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/quotes` | `{planting_id, product_id, sum_insured_per_ha?}` → premium breakdown + **resolved trigger definition** + plain-language contract. Does not persist a policy |
| `POST` | `/policies` | `{quote_id}` or `{planting_id, product_id, sum_insured}` → issues policy, **freezes `trigger_definition`**, `status=active`. Idempotent |
| `GET` | `/policies` | Caller's policies; `?status=` filter |
| `GET` | `/policies/{id}` | Full policy incl. frozen trigger and human-readable terms |
| `GET` | `/policies/{id}/evaluations` | **The audit trail** — every daily evaluation with index values, source, engine version |
| `GET` | `/policies/{id}/monitor` | Live season position (see below) |
| `POST` | `/policies/{id}/cancel` | Only while `status=active` and before coverage start |
| `GET` | `/policies/{id}/certificate` | PDF (SHOULD-HAVE S7) |

`GET /policies/{id}/monitor` — powers the dashboard and the early-warning banner:

```json
{
  "policy_id": "…", "status": "active",
  "season": { "day_of_season": 62, "total_days": 105, "phase": "flowering",
              "coverage_ends": "2026-09-28" },
  "index": { "name": "cumulative_rainfall_mm", "window_start_day": 45, "window_end_day": 75,
             "accumulated_to_date": 71.2, "days_remaining_in_window": 13,
             "nearest_threshold": 120, "shortfall_mm": 48.8, "pct_of_threshold": 59.3 },
  "forecast": { "next_16d_precip_mm": 22.4, "source": "open-meteo", "issued": "2026-08-15" },
  "projection": { "trigger_probability_now": 0.68, "method": "analogue-years-k12",
                  "projected_payout_pct": 50, "projected_amount": "36000.00" },
  "recent_evaluations": [ … ]
}
```

### 2.6 Weather

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/weather/observations` | `?farm_id=&from=&to=` → **cached** daily series. Never calls upstream |
| `GET` | `/weather/forecast` | `?farm_id=` → 16-day forecast from cache |
| `GET` | `/weather/summary` | `?farm_id=&season=` → season-to-date vs 35-year normal |

### 2.7 Payouts

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/payouts` | Caller's payouts |
| `GET` | `/payouts/{id}` | Detail + originating evaluation + ledger entries |
| `POST` | `/payouts/{id}/approve` | **admin** — auto-approval on by default in demo mode |
| `POST` | `/payouts/{id}/disburse` | **admin** — mock UPI, returns reference, idempotent |

There is deliberately **no endpoint to create a payout.** Payouts originate only inside the trigger
engine. Exposing creation would break the guarantee that every rupee traces to an evaluation.

### 2.8 Alerts

`GET /alerts?unread_only=` · `POST /alerts/{id}/read` · `POST /alerts/read-all`.

### 2.9 Admin & demo control

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/admin/simulate/weather` | **The demo lever.** Injects synthetic observations |
| `POST` | `/admin/evaluate` | `{policy_id?}` → force evaluation now, bypassing the schedule |
| `POST` | `/admin/demo/reset` | Deletes `is_simulated` rows, resets policies/payouts to pre-demo state |
| `GET` | `/admin/portfolio` | Aggregate exposure, expected loss, trigger counts (S8) |
| `GET` | `/admin/policies` | All policies across farmers |

```jsonc
// POST /admin/simulate/weather
{ "district": "Coimbatore",
  "scenario": "severe_rainfall_deficit",   // | "excess_rainfall" | "heat_wave" | "normal"
  "start_date": "2026-07-29", "end_date": "2026-08-28",
  "intensity": 0.85 }                       // 0–1; 0.85 ⇒ ~85 % below normal
```

Writes `weather_observation` rows with `source="simulated"`, `is_simulated=true`, then returns the
affected policies. Paired with `/admin/evaluate`, this is the entire on-stage trigger moment — and
because `is_simulated` is flagged, `/admin/demo/reset` unwinds it cleanly between rehearsals.

### 2.10 Operational

`GET /healthz` (liveness) · `GET /readyz` (DB + weather-cache freshness) · `GET /version`
(app + engine + model versions — the same versions stamped onto evaluations).

## 3. Background jobs (APScheduler)

| Job | Schedule | Does |
|-----|----------|------|
| `ingest_weather_observations` | 05:30 IST daily | Fetch yesterday's actuals for all active cells; upsert |
| `ingest_weather_forecasts` | 05:45 IST daily | Refresh 16-day forecast per cell |
| `evaluate_active_policies` | 06:00 IST daily | Deterministic evaluation → `policy_evaluation` → payout on trigger |
| `generate_early_warnings` | 06:15 IST daily | Analogue-year projection; alert when P(trigger) crosses 0.5 |
| `expire_policies` | 00:30 IST daily | Move past-coverage policies to `expired` |

Every job is manually invocable from the admin console — never wait for a cron on stage.

## 4. Build order (matches the 30-hour plan)

| Phase | Endpoints | By |
|-------|-----------|-----|
| 1 | `/healthz`, `/auth/*`, `/crops`, `/districts` | H6 |
| 2 | `/farms/*`, `/plantings/*`, `/products` | H10 |
| 3 | `/risk/assess`, `/risk/assessments/{id}` | H12 |
| 4 | `/quotes`, `/policies` (create + read) | H14 |
| 5 | `/policies/{id}/monitor`, `/weather/*` | H16 |
| 6 | `/admin/simulate/weather`, `/admin/evaluate`, `/payouts/*` | H18 |
| 7 | `/alerts/*`, `/risk/explain`, `/admin/portfolio` | H22 |

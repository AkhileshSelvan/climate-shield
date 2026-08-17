# 10 — Implementation Status

> **As-built record.** Where this document and documents 01–09 disagree, **this one is
> current** — 01–09 describe the approved target, this describes what exists in the
> repository today. Updated after each foundation change.

**Last updated:** 2026-08-17 · Backend `0.2.0` · Engines `trigger-v1.1` / `payout-v1.1`

## 1. What exists

The first backend (PR #2, merged to `main`) delivered a working FastAPI application:
farm registration, policy creation, trigger evaluation, payout creation, and a demo
simulator. That work is preserved. The foundation pass that followed corrected four
things that would have failed on stage or produced wrong money, and moved the code onto
the agreed structure.

```
Farm ──snap──▶ WeatherGridCell ◀──cache── WeatherObservation ◀── providers (ingestion only)
 │                                              │
 └── Policy ──────────────────────────▶ evaluate_policy() ──▶ Trigger ──▶ Payout
       (frozen terms)                  UNIQUE(policy, date)   audit row   UNIQUE(trigger)
```

## 2. Foundation corrections applied

| # | Correction | How |
|---|-----------|-----|
| 1 | **Weather off the request path** | `WeatherProvider` protocol with `FixtureProvider` (default), `OpenMeteoProvider` (opt-in). Evaluation reads `weather_observations` only. `POST /weather/ingest` is the sole endpoint permitted to reach a network. |
| 2 | **Payout idempotency** | `UNIQUE(policy_id, evaluation_date)` on `triggers`, `UNIQUE(trigger_id)` on `payouts`. One evaluation function, one creation site, `IntegrityError` handled as a reuse path for concurrent callers. |
| 3 | **Decimal money** | `Money` type decorator: `NUMERIC(14,2)` on PostgreSQL, zero-padded sortable text on SQLite. Both return `Decimal`. Serialised as strings so no client parses money into a float. |
| 4 | **PostgreSQL** | `DATABASE_URL` drives the engine; `docker-compose.yml` provides a local PostgreSQL 16 matching the deployment target. SQLite is retained for tests and quick runs only. |
| 5 | **`backend/app/` structure** | Package layout with `core/`, `api/v1/`, `services/`. Moved with `git mv`, so history follows the files. |
| 6 | **Dependencies** | Pinned `backend/requirements.txt`; `make install` from a clean machine. |
| 7 | **`.gitignore`** | Node.js coverage and `.env.local` / `.env.*.local` added. |

## 3. Deviations from documents 01–09, and why

Each is a deliberate, recorded choice — not drift.

| Area | Plan (01–09) | As built | Rationale |
|------|--------------|----------|-----------|
| Weather fixtures | Real ERA5, 35 years | **Synthetic, 2 years, labelled `"synthetic": true`** | Open-Meteo is unreachable from every environment available so far. ADR-014's honesty rule applies: generated numbers are labelled in the file header and surfaced by the API. `make fixtures-live` swaps in real ERA5 the moment one machine can reach the API. **This is the top remaining blocker.** |
| Trigger contract | `trigger_definition` JSONB snapshot | Typed columns on `policy` (`trigger_type`, `threshold_mm`, `window_days`) | Achieves the same protection — terms live on the policy, not behind a mutable product template, so an issued contract cannot be rewritten. Simpler, typed, and validated. JSONB becomes worthwhile only when products carry multiple perils. |
| Payout structure | Tiered 25/50/100 % | Flat 30 % of coverage | Carried over from the first backend; tiering was out of scope for the foundation pass. Still planned — see §7. |
| Identifiers | UUID | Integer autoincrement | Carried over. Not worth a migration during a hackathon; no external exposure depends on it. |
| Evaluation window | Day offsets from `sowing_date` | Rolling `window_days` back from evaluation date | The current model has no sowing date. Correct once crop calendars land. |
| Money precision | `NUMERIC(14,2)` everywhere | Same, plus a SQLite-safe representation | SQLite has no decimal type; the type decorator avoids the float round-trip SQLAlchemy would otherwise perform. |

## 4. Principles: enforcement status

| Principle | Status | Enforced by |
|-----------|--------|-------------|
| Modular monolith | ✅ Holding | One app, `services/` boundaries |
| **AI never authorises payouts** | ✅ **Enforced** | `tests/test_architecture.py` walks the import graph and **fails the build**. `trigger_engine.py` imports nothing at all. |
| Deterministic trigger engine | ✅ Enforced | Pure functions; determinism asserted in tests |
| Frozen policy trigger definitions | ⚠️ Partial | Terms live on the policy; no DB trigger yet blocks `UPDATE` after issuance |
| Offline-capable demo | ✅ Verified | Full happy path passes with sockets blocked |
| Shared PostgreSQL | ⚠️ Configured | `DATABASE_URL` + compose file ready; the team must actually point at one |
| Tier-1 burn analysis mandatory | ⛔ Not started | Next major workstream |
| ML / Claude optional | ✅ Holding | Nothing depends on them |
| Admin simulation MUST-HAVE | ✅ Built | `/simulate/*`, idempotent, with reset |

## 5. Test coverage

38 tests, all passing.

| File | Covers |
|------|--------|
| `test_trigger_engine.py` | Breach logic, threshold boundaries, unknown types, determinism |
| `test_idempotency.py` | Double-click, ten rapid calls, per-date separation, DB constraints, reset |
| `test_money.py` | Decimal round-trip, half-up rounding, float-input safety, API serialisation |
| `test_weather_offline.py` | Fixture provider, provenance labelling, full happy path with sockets blocked, live-failure containment |
| `test_architecture.py` | Import-graph fitness — the money path stays clean |

## 6. Commands

| Command | Does |
|---------|------|
| `make install` | Clean-machine setup |
| `make db-up` | Local PostgreSQL |
| `make migrate` | Apply Alembic migrations |
| `make seed-demo` | Weather fixtures + demo farm and policy (idempotent) |
| `make demo-reset` | Clear evaluations, payouts, simulated weather |
| `make demo-offline` | Full stack on fixtures — verify with the network off |
| `make test` | Test suite |
| `make fixtures-live` | **Only** networked target: refresh fixtures from Open-Meteo |

## 7. Remaining work, in priority order

1. **Replace synthetic fixtures with real ERA5** (`make fixtures-live` from a machine with access). Top blocker — everything else is honest engineering on placeholder data.
2. **Tier-1 burn analysis** (M5) — the mandatory risk engine, still entirely absent. The largest gap between plan and reality.
3. Tiered payouts (25/50/100) replacing the flat 30 %.
4. Point the team at one shared PostgreSQL instance.
5. Crop calendars and sowing-date-anchored windows.
6. DB trigger blocking `UPDATE` of policy trigger terms after issuance.
7. Authentication (M1), frontend (M2, M8), alerts (M11), audit view (M12).

# 11 — Weather Data Research & Demo Evidence

## Data source decision

**Chosen: Open-Meteo Historical Weather API (ERA5 reanalysis)**

- Free, no API key required
- Confirmed reachable from local development machines (tested 2026-08-19)
- Provides daily precipitation_sum in mm — matches the trigger engine's
  unit (mm) and window (days) model
- Coverage: global, historical archive available back decades

## Fixture generation

`backend/seeds/generate_fixtures.py` supports two modes:
- `--live`: fetches real ERA5 data via Open-Meteo (requires network)
- default: deterministic synthetic series from published regional
  monsoon normals, clearly labelled `"synthetic": true`

Demo cells (Tamil Nadu, 0.1° grid):

| Cell | Location |
|---|---|
| 11.0, 77.0 | Pollachi / Coimbatore |
| 11.3, 77.7 | Erode |
| 11.1, 77.3 | Tiruppur |
| 10.4, 77.9 | Dindigul |

## Historical evidence: real ERA5 data validation (2026-08-19, early session)

This was an early proof-of-concept run, done before the 35-year synthetic
demo dataset was calibrated. It confirms Open-Meteo is reachable and the
system correctly handles genuine measured data.

Ran `python seeds/generate_fixtures.py --live --years 2`. All 4 cells
returned 731 days of real data, synthetic=False.

Seeded a demo farm and policy against this real data: farm #2 (Murugan,
Pollachi, Coimbatore), policy #2 (drought below 120.0mm — an early,
uncalibrated threshold used only for this test).

Ran a real (non-simulated) evaluation: observed rainfall 134.7mm over 31
days, threshold 120.0mm, triggered=false. Correctly did NOT trigger, since
real rainfall was above the drought threshold — confirming the system
responds to genuine data rather than always triggering.

Ran the demo simulator: observed rainfall forced to 11.0mm, triggered=true,
payout amount 21600.00 INR, honestly labelled is_simulated=true.

At the time of this run, the test suite had 47 tests, all passing.

## Current demo configuration (as of PR #11, main branch)

The historical run above has since been superseded by a calibrated,
35-year demo dataset, merged via PR #10 (fixtures) and PR #11 (seeding
config). This is what the live demo now uses:

- **Data span:** 35 years (1992–2026), synthetic-regional-normals source,
  labelled `"synthetic": true`. Real ERA5 has not yet been regenerated at
  the 35-year span — `make fixtures-live` remains the path to do so before
  a fully "real data" demo.
- **Demo policy:** drought below **30.0mm** over a 30-day window (recalibrated
  from the earlier 120mm test value, to produce a realistic MEDIUM risk
  result rather than an extreme SEVERE result from a 2-year sample).
- **Verified risk analysis result:** 35 historical years, 35 eligible years,
  7 triggered years, risk_score 20.0, risk_level MEDIUM.
- **Verified demo simulation:** forced drought → triggered=true → payout
  ₹21,600.00, is_simulated=true. Repeated call → idempotent_reuse=true,
  same payout, no duplicate.

## Test coverage confirming correctness

As of `main` (post PR #11): **86 tests passing, 0 skipped**, including
trigger boundary tests, idempotency tests (no duplicate payouts on repeat
calls, including under concurrent-call simulation), money precision tests
(exact Decimal, no float errors), offline-capability tests, risk-engine
purity tests (no payout/trigger creation from risk analysis), and
demo-config safety tests (refuses to reseed over a policy with different
terms).

## Open item

The 35-year fixtures currently in `main` are synthetic (regional monsoon
normals), not real ERA5 measurements. The 2-year historical run above
proves real ERA5 data works correctly end-to-end; extending that to the
full 35-year span via `make fixtures-live` (or
`generate_fixtures.py --live --years 35`) remains open, blocked only on
confirming stable network access during the actual demo window.

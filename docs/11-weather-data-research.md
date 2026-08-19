# 11 — Weather Data Research & Demo Evidence

## Data source decision

**Chosen: Open-Meteo Historical Weather API (ERA5 reanalysis)**

- Free, no API key required
- Confirmed reachable from local development machines (tested 2026-08-19)
- Provides daily precipitation_sum in mm — matches our trigger engine's
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

## Evidence: real data validation (2026-08-19)

Ran `python seeds/generate_fixtures.py --live --years 2`. All 4 cells
returned 731 days of real data, synthetic=False.

Seeded a demo farm and policy against this real data: farm #2 (Murugan,
Pollachi, Coimbatore), policy #2 (drought below 120.0mm).

Ran a real (non-simulated) evaluation: observed rainfall 134.7mm over 31
days, threshold 120.0mm, triggered=false. Correctly did NOT trigger, since
real rainfall was above the drought threshold. Confirms the system responds
correctly to genuine data rather than always triggering.

Ran the demo simulator: observed rainfall forced to 11.0mm, triggered=true,
payout amount 21600.00 INR, honestly labelled is_simulated=true.

## Test coverage confirming correctness

47/47 tests passing, including trigger boundary tests, idempotency tests
(no duplicate payouts on repeat calls), money precision tests (exact
Decimal, no float errors), and offline-capability tests.

## Open item

A parallel branch extends fixtures to 35 years for proper burn-analysis
sample size, currently using synthetic data. Recommend regenerating with
--live --years 35 once network access is confirmed stable.

"""Tier-1 burn-analysis risk engine.

Scenarios 1-7 drive the pure engine directly, so the arithmetic is asserted
without a database in the way. Scenarios 8-10 go through the API, because
provenance flags and the no-payout guarantee are properties of the whole path.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from app import models
from app.services import trigger_engine
from app.services.risk.burn_analysis import (
    BURN_ENGINE_VERSION,
    DATA_QUALITY_INSUFFICIENT,
    DATA_QUALITY_LIMITED,
    DATA_QUALITY_SUFFICIENT,
    analyse,
    build_season_windows,
)
from app.services.risk.classification import classify, to_risk_score

ANCHOR = date(2026, 8, 17)
WINDOW_DAYS = 30
EXPECTED_DAYS = WINDOW_DAYS + 1  # both ends inclusive, matching evaluation.py

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "seeds" / "weather"


def _obs(count: int, mm_per_day: float, source: str = "fixture", simulated: bool = False):
    return [
        {"precipitation_mm": mm_per_day, "source": source, "is_simulated": simulated}
        for _ in range(count)
    ]


def _seasons(start_year: int, end_year: int, per_year_total_mm, days: int = EXPECTED_DAYS):
    """Pair each season window with observations summing to a chosen total.

    `per_year_total_mm` may be a scalar or a {year: total} mapping.
    """
    windows = build_season_windows(ANCHOR, WINDOW_DAYS, start_year, end_year)
    paired = []
    for w in windows:
        total = (
            per_year_total_mm[w.year]
            if isinstance(per_year_total_mm, dict)
            else per_year_total_mm
        )
        paired.append((w, _obs(days, total / days) if days else []))
    return paired


# --------------------------------------------------------------------------
# 1. Zero historical triggers
# --------------------------------------------------------------------------
def test_zero_historical_triggers():
    # 300mm every season against a 120mm drought threshold: never breached.
    result = analyse(_seasons(1992, 2026, 300.0), "drought", 120.0)

    assert result.historical_years == 35
    assert result.eligible_years == 35
    assert result.triggered_years == 0
    assert result.trigger_frequency == 0.0
    assert result.risk_score == 0.0
    assert classify(result.risk_score)[0] == "LOW"
    assert result.data_quality == DATA_QUALITY_SUFFICIENT


# --------------------------------------------------------------------------
# 2. All historical years trigger
# --------------------------------------------------------------------------
def test_all_historical_years_trigger():
    result = analyse(_seasons(1992, 2026, 20.0), "drought", 120.0)

    assert result.eligible_years == 35
    assert result.triggered_years == 35
    assert result.trigger_frequency == 1.0
    assert result.risk_score == 100.0
    assert classify(result.risk_score)[0] == "SEVERE"


# --------------------------------------------------------------------------
# 3. Partial trigger frequency — the demo case
# --------------------------------------------------------------------------
def test_partial_trigger_frequency_matches_demo_numbers():
    """8 of 35 seasons must produce 22.86% and MEDIUM."""
    dry_years = {1994, 2002, 2003, 2012, 2016, 2019, 2023, 2024}
    totals = {y: (20.0 if y in dry_years else 300.0) for y in range(1992, 2027)}

    result = analyse(_seasons(1992, 2026, totals), "drought", 120.0)

    assert result.eligible_years == 35
    assert result.triggered_years == 8
    assert result.trigger_frequency == 0.2286      # 8/35 to 4dp
    assert result.risk_score == 22.86              # and to 2dp on the 0-100 scale
    assert classify(result.risk_score)[0] == "MEDIUM"
    assert sorted(result.triggered_year_labels) == sorted(dry_years)


def test_excess_rain_uses_the_opposite_comparison():
    totals = {y: (500.0 if y % 5 == 0 else 100.0) for y in range(1992, 2027)}
    result = analyse(_seasons(1992, 2026, totals), "excess_rain", 300.0)

    assert result.triggered_years == sum(1 for y in range(1992, 2027) if y % 5 == 0)
    assert all(y.observed_mm > 300.0 for y in result.years if y.triggered)


# --------------------------------------------------------------------------
# 4. Exact threshold boundary
# --------------------------------------------------------------------------
def test_exact_threshold_is_not_a_breach():
    """Equal to the threshold pays nothing — the same rule the settlement engine applies."""
    result = analyse(_seasons(2020, 2026, 120.0), "drought", 120.0)
    assert result.triggered_years == 0

    excess = analyse(_seasons(2020, 2026, 120.0), "excess_rain", 120.0)
    assert excess.triggered_years == 0


def test_boundary_agrees_with_the_trigger_engine_exactly():
    """The risk engine must not hold a second definition of 'drought'."""
    for observed in (119.99, 120.0, 120.01):
        result = analyse(_seasons(2026, 2026, observed, days=EXPECTED_DAYS), "drought", 120.0)
        engine_says = trigger_engine.evaluate_trigger(
            "drought", result.years[0].observed_mm, 120.0
        )
        assert result.years[0].triggered is engine_says


def test_unknown_trigger_type_is_rejected():
    with pytest.raises(ValueError, match="Unknown trigger_type"):
        analyse(_seasons(2020, 2026, 100.0), "hailstorm", 50.0)


# --------------------------------------------------------------------------
# 5. Insufficient historical data
# --------------------------------------------------------------------------
def test_insufficient_data_returns_a_state_not_a_guess():
    result = analyse(_seasons(1992, 2026, 100.0, days=0), "drought", 120.0)

    assert result.eligible_years == 0
    assert result.trigger_frequency is None
    assert result.risk_score is None
    assert result.data_quality == DATA_QUALITY_INSUFFICIENT
    assert classify(result.risk_score)[0] == "UNKNOWN"
    assert all(y.ineligible_reason for y in result.years)


def test_few_eligible_years_is_flagged_as_limited():
    result = analyse(_seasons(2024, 2026, 20.0), "drought", 120.0)

    assert result.eligible_years == 3
    assert result.data_quality == DATA_QUALITY_LIMITED
    assert result.risk_score == 100.0  # a score is still produced, flagged as limited


# --------------------------------------------------------------------------
# 6. Missing observations
# --------------------------------------------------------------------------
def test_partial_coverage_years_are_excluded_not_zero_filled():
    """A gap must never be read as zero rainfall — that invents a drought."""
    windows = build_season_windows(ANCHOR, WINDOW_DAYS, 2022, 2026)
    paired = []
    for w in windows:
        # 2024 has only 10 of 31 days on record.
        days = 10 if w.year == 2024 else EXPECTED_DAYS
        paired.append((w, _obs(days, 300.0 / EXPECTED_DAYS)))

    result = analyse(paired, "drought", 120.0)

    assert result.historical_years == 5
    assert result.eligible_years == 4  # 2024 excluded
    partial = next(y for y in result.years if y.year == 2024)
    assert partial.eligible is False
    assert partial.observed_mm is None
    assert partial.triggered is None
    assert "incomplete record" in partial.ineligible_reason
    # Excluded from the denominator entirely, rather than counted as a dry year.
    assert result.triggered_years == 0
    assert result.trigger_frequency == 0.0


def test_coverage_threshold_is_configurable():
    windows = build_season_windows(ANCHOR, WINDOW_DAYS, 2026, 2026)
    paired = [(windows[0], _obs(16, 1.0))]  # 16/31 = 51.6%

    assert analyse(paired, "drought", 120.0, min_coverage=0.8).eligible_years == 0
    assert analyse(paired, "drought", 120.0, min_coverage=0.5).eligible_years == 1


# --------------------------------------------------------------------------
# 7. Deterministic repeated calculation
# --------------------------------------------------------------------------
def test_repeated_calculation_is_identical():
    totals = {y: (20.0 if y % 4 == 0 else 300.0) for y in range(1992, 2027)}
    runs = [analyse(_seasons(1992, 2026, totals), "drought", 120.0) for _ in range(50)]

    first = runs[0]
    for run in runs[1:]:
        assert run.risk_score == first.risk_score
        assert run.trigger_frequency == first.trigger_frequency
        assert run.triggered_years == first.triggered_years
        assert run.triggered_year_labels == first.triggered_year_labels
        assert [y.as_dict() for y in run.years] == [y.as_dict() for y in first.years]


def test_season_windows_are_calendar_aligned_and_reproducible():
    a = build_season_windows(ANCHOR, 30, 2020, 2026)
    b = build_season_windows(ANCHOR, 30, 2020, 2026)
    assert a == b
    assert all(w.end.month == ANCHOR.month and w.end.day == ANCHOR.day for w in a)
    assert all(w.expected_days == EXPECTED_DAYS for w in a)


def test_leap_day_anchor_does_not_drop_seasons():
    windows = build_season_windows(date(2024, 2, 29), 30, 2022, 2024)
    assert len(windows) == 3
    assert windows[0].end == date(2022, 2, 28)  # non-leap year falls back


def test_score_transformation_is_the_documented_linear_map():
    assert to_risk_score(0.0) == 0.0
    assert to_risk_score(0.2286) == 22.86
    assert to_risk_score(1.0) == 100.0
    with pytest.raises(ValueError):
        to_risk_score(1.5)


# --------------------------------------------------------------------------
# 8-10. Whole-path properties, through the API
# --------------------------------------------------------------------------
def _fixture_end_date() -> date:
    """Anchor API tests to the fixture's own range so they don't rot over time."""
    payload = json.loads((FIXTURE_DIR / "cell_11.0_77.0.json").read_text())
    return date.fromisoformat(payload["end_date"])


@pytest.fixture()
def cached_farm(client, farm):
    end = _fixture_end_date()
    response = client.post(
        "/api/v1/weather/ingest",
        json={"farm_id": farm["id"], "days": 400, "end_date": end.isoformat()},
    )
    assert response.status_code == 200, response.text
    return farm, end


def test_synthetic_data_flags_propagate_to_the_result(client, cached_farm):
    """Fixture provenance must reach the caller — never presented as measurement."""
    farm, end = cached_farm
    body = client.post(
        "/api/v1/risk/analyze",
        json={
            "farm_id": farm["id"], "trigger_type": "drought", "threshold_mm": 9999.0,
            "window_days": 30, "season_end": end.isoformat(), "lookback_years": 2,
        },
    ).json()

    assert body["data_source"] == ["fixture"]
    assert body["is_simulated"] is False  # cached fixture rows are not demo-injected
    provenance = [f for f in body["factors"] if f["factor"] == "fixture_data"]
    assert provenance, "fixture provenance must be surfaced as a factor"
    assert "synthetic" in provenance[0]["detail"].lower()


def test_simulated_observations_are_flagged(client, db_session, cached_farm):
    farm, end = cached_farm
    cell_id = client.get(f"/api/v1/farms/{farm['id']}").json()["grid_cell_id"]
    cell = db_session.query(models.WeatherGridCell).filter_by(id=cell_id).one()

    from app.services.weather import cache

    cache.upsert_observations(
        db_session, cell,
        [{"date": end.isoformat(), "precipitation_mm": 0.0}],
        source="simulated", is_simulated=True,
    )

    body = client.post(
        "/api/v1/risk/analyze",
        json={
            "farm_id": farm["id"], "trigger_type": "drought", "threshold_mm": 9999.0,
            "window_days": 30, "season_end": end.isoformat(), "lookback_years": 2,
        },
    ).json()

    assert body["is_simulated"] is True
    assert "simulated" in body["data_source"]
    assert any(f["factor"] == "simulated_observations" for f in body["factors"])


def test_engine_version_is_reported(client, cached_farm):
    farm, end = cached_farm
    body = client.post(
        "/api/v1/risk/analyze",
        json={
            "farm_id": farm["id"], "trigger_type": "drought", "threshold_mm": 9999.0,
            "window_days": 30, "season_end": end.isoformat(), "lookback_years": 2,
        },
    ).json()

    assert body["engine_version"] == BURN_ENGINE_VERSION
    assert body["engine_version"].startswith("burn-analysis-v")
    # The trigger semantics actually used are named in the result.
    assert trigger_engine.ENGINE_VERSION in body["trigger_definition"]["semantics"]


def test_risk_analysis_creates_no_payout_trigger_or_policy(client, db_session, cached_farm):
    """The engine estimates. It must never settle."""
    farm, end = cached_farm
    before = (
        db_session.query(models.Payout).count(),
        db_session.query(models.Trigger).count(),
        db_session.query(models.Policy).count(),
    )

    for _ in range(5):
        response = client.post(
            "/api/v1/risk/analyze",
            json={
                "farm_id": farm["id"], "trigger_type": "drought", "threshold_mm": 9999.0,
                "window_days": 30, "season_end": end.isoformat(), "lookback_years": 2,
            },
        )
        assert response.status_code == 200
        assert response.json()["triggered_years"] > 0  # it did find breaches...

    after = (
        db_session.query(models.Payout).count(),
        db_session.query(models.Trigger).count(),
        db_session.query(models.Policy).count(),
    )
    assert before == after == (0, 0, 0)  # ...and still wrote nothing


def test_policy_risk_endpoint_is_read_only(client, db_session, cached_farm, drought_policy):
    farm, end = cached_farm
    payouts_before = db_session.query(models.Payout).count()
    triggers_before = db_session.query(models.Trigger).count()

    body = client.post(
        f"/api/v1/risk/analyze/policy/{drought_policy['id']}",
        json={"season_end": end.isoformat(), "lookback_years": 2},
    ).json()

    assert body["trigger_definition"]["trigger_type"] == drought_policy["trigger_type"]
    assert body["trigger_definition"]["threshold_mm"] == drought_policy["threshold_mm"]
    assert body["context"]["policy_id"] == drought_policy["id"]
    assert db_session.query(models.Payout).count() == payouts_before
    assert db_session.query(models.Trigger).count() == triggers_before


def test_missing_weather_cache_reports_insufficient_data(client, farm):
    """No ingest at all: a data-quality state, not a fabricated score."""
    body = client.post(
        "/api/v1/risk/analyze",
        json={
            "farm_id": farm["id"], "trigger_type": "drought", "threshold_mm": 120.0,
            "window_days": 30, "season_end": "2026-08-17", "lookback_years": 5,
        },
    ).json()

    assert body["risk_score"] is None
    assert body["risk_level"] == "UNKNOWN"
    assert body["data_quality"] == "insufficient"
    assert body["confidence"] == "none"
    assert body["eligible_years"] == 0


def test_unknown_farm_is_404(client):
    response = client.post(
        "/api/v1/risk/analyze",
        json={
            "farm_id": 99999, "trigger_type": "drought", "threshold_mm": 120.0,
            "window_days": 30,
        },
    )
    assert response.status_code == 404


def test_bands_endpoint_publishes_the_classification(client):
    body = client.get("/api/v1/risk/bands").json()
    assert [b["level"] for b in body["bands"]] == ["LOW", "MEDIUM", "HIGH", "SEVERE"]


def test_farm_pointing_at_a_missing_grid_cell_is_a_structured_error(client, db_session, farm):
    """A dangling grid_cell_id must not surface as an unhandled AttributeError.

    PostgreSQL's foreign key rules this out; SQLite does not enforce one by
    default, so the lookup has to be guarded rather than assumed.
    """
    from app import models

    stored = db_session.query(models.Farm).filter_by(id=farm["id"]).one()
    stored.grid_cell_id = 99999  # no such cell
    db_session.commit()

    response = client.post(
        "/api/v1/risk/analyze",
        json={
            "farm_id": farm["id"], "trigger_type": "drought", "threshold_mm": 30.0,
            "window_days": 30,
        },
    )

    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "Farm's weather grid cell 99999 does not exist"

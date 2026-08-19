"""The Golden Demo's configuration is a product decision, so it is pinned here.

Two of these values were chosen deliberately against the committed *synthetic*
fixtures, and both would otherwise be easy to change by accident:

  * how much history the demo loads into the weather cache, which bounds how
    many seasons the risk engine can evaluate at all, and
  * the demo policy's drought threshold, which decides what risk band a judge
    sees on stage.

These tests exist so that a change to either is a conscious edit with a failing
test in front of it, not a silent drift.
"""
from datetime import date, timedelta
from pathlib import Path

import pytest

from seeds import seed_demo

SEED_SOURCE = Path(seed_demo.__file__)


def test_demo_loads_the_full_thirty_five_year_span():
    """The engine reads the cache, so seed depth caps the seasons available.

    At the previous 120 days exactly one season was complete and the demo
    reported SEVERE at 100% off a sample of one.
    """
    assert seed_demo.DEMO_LOOKBACK_DAYS == 365 * 35
    # The CLI and the function must agree, or `make seed-demo` and a direct
    # call would load different amounts of history.
    assert seed_demo.seed_weather.__defaults__[0] == seed_demo.DEMO_LOOKBACK_DAYS


def test_demo_policy_uses_the_calibrated_demo_threshold():
    assert seed_demo.DEMO_THRESHOLD_MM == 30.0
    assert seed_demo.DEMO_POLICY["threshold_mm"] == seed_demo.DEMO_THRESHOLD_MM
    assert seed_demo.DEMO_POLICY["trigger_type"] == "drought"
    assert seed_demo.DEMO_POLICY["window_days"] == 30


def test_the_demo_threshold_is_labelled_as_a_demo_value():
    """It must never read as an agronomic recommendation.

    30 mm was picked to make the demo exercise a realistic band on synthetic
    data. If that provenance stops being stated, someone will eventually quote
    the number as though it were derived from crop science.
    """
    # Strip comment markers and normalise whitespace, so re-wrapping the
    # disclaimer across lines cannot silently break the guard.
    prose = " ".join(
        line.lstrip().lstrip("#").strip() for line in SEED_SOURCE.read_text().splitlines()
    )
    prose = " ".join(prose.split())
    assert "NOT AN AGRONOMIC RECOMMENDATION" in prose
    assert "not scientifically validated" in prose


def test_fixtures_still_declare_themselves_synthetic():
    """Deeper history must not quietly become presented as measured weather."""
    import json

    fixture_dir = SEED_SOURCE.parent / "weather"
    files = sorted(fixture_dir.glob("cell_*.json"))
    assert files, "no weather fixtures found"
    for path in files:
        payload = json.loads(path.read_text())
        assert payload["synthetic"] is True, f"{path.name} is no longer flagged synthetic"
        assert "synthetic" in payload["note"].lower()


@pytest.mark.slow
def test_golden_demo_produces_the_expected_risk_result(db_session):
    """The number a judge sees, pinned.

    Ingests only the demo farm's own grid cell — the other three demo cells do
    not affect this policy and loading them would triple the runtime.
    """
    pytest.importorskip(
        "app.services.risk.service",
        reason="risk engine ships in a separate change; this asserts the combined result",
    )
    from app.services.risk.service import analyse_risk
    from app.services.weather import cache
    from app.services.weather.providers import FixtureProvider

    end = date.today()
    start = end - timedelta(days=seed_demo.DEMO_LOOKBACK_DAYS)
    cache.ingest(db_session, 11.0, 77.0, start, end, provider=FixtureProvider())
    farm, policy = seed_demo.seed_demo_entities(db_session)

    result = analyse_risk(
        db_session,
        trigger_type=policy.trigger_type,
        threshold_mm=policy.threshold_mm,
        window_days=policy.window_days,
        farm_id=farm.id,
    )

    assert result["historical_years"] == 35
    assert result["eligible_years"] == 35, "every season must be evaluable"
    assert result["triggered_years"] == 7
    assert result["risk_score"] == 20.0
    assert result["risk_level"] == "MEDIUM"
    assert result["data_quality"] == "sufficient"
    assert result["confidence"] == "high"
    # Provenance must survive all the way to the caller.
    assert result["data_source"] == ["synthetic-regional-normals"]


# --- Re-seeding an existing database -----------------------------------------
#
# Weather is upserted on every run, so a stale database refreshes its cache and
# looks healthy. Policy terms are not, and a policy left on the old 120 mm
# threshold would show SEVERE at 97.14% while the configuration here said
# MEDIUM at 20.0%. Seeding must refuse rather than rewrite a frozen contract.


def _seeded_farm_and_policy(db_session):
    """Seed once, from empty. Returns the created farm and policy."""
    return seed_demo.seed_demo_entities(db_session)


def test_a_fresh_seed_creates_the_configured_demo_policy(db_session):
    farm, policy = _seeded_farm_and_policy(db_session)

    assert farm.farmer_name == seed_demo.DEMO_FARM["farmer_name"]
    assert policy.farm_id == farm.id
    for field, expected in seed_demo.DEMO_POLICY.items():
        assert getattr(policy, field) == expected, field
    assert seed_demo.policy_mismatches(policy) == []


def test_re_seeding_a_matching_database_reuses_the_same_policy(db_session):
    """The ordinary case: nothing changed, so nothing is created or refused."""
    from app import models

    _, first = _seeded_farm_and_policy(db_session)
    _, second = seed_demo.seed_demo_entities(db_session)

    assert second.id == first.id
    assert db_session.query(models.Policy).count() == 1
    assert second.threshold_mm == seed_demo.DEMO_THRESHOLD_MM


def test_re_seeding_over_different_terms_refuses_and_says_why(db_session):
    """The trap this guards: a database seeded before the threshold changed.

    The old 120 mm policy must not survive silently, and must not be quietly
    rewritten either — an issued contract's terms are frozen.
    """
    from app import models

    _, policy = _seeded_farm_and_policy(db_session)

    # Simulate a database seeded under the previous demo configuration.
    policy.threshold_mm = 120.0
    policy.window_days = 45
    db_session.commit()

    with pytest.raises(seed_demo.DemoSeedError) as exc_info:
        seed_demo.seed_demo_entities(db_session)

    message = str(exc_info.value)
    # It must name what differs, or the operator cannot act on it.
    assert "threshold_mm" in message and "120.0" in message and "30.0" in message
    assert "window_days" in message and "45" in message
    # And say what to do, including the reset that does *not* fix it.
    assert "fresh" in message.lower()
    assert "demo-reset" in message

    # Nothing was mutated: refusing means refusing.
    db_session.refresh(policy)
    assert policy.threshold_mm == 120.0
    assert policy.window_days == 45
    assert db_session.query(models.Policy).count() == 1


def test_a_coverage_change_is_caught_too(db_session):
    """Not just the trigger terms — the insured amount matters as much."""
    from decimal import Decimal

    _, policy = _seeded_farm_and_policy(db_session)
    policy.coverage_amount = Decimal("50000.00")
    db_session.commit()

    mismatches = seed_demo.policy_mismatches(policy)
    assert [field for field, _, _ in mismatches] == ["coverage_amount"]

    with pytest.raises(seed_demo.DemoSeedError, match="coverage_amount"):
        seed_demo.seed_demo_entities(db_session)

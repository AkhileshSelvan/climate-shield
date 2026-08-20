"""Seed the database for local development and the demo.

Idempotent: running it twice produces the same database. Uses the fixture
weather provider only, so it never needs a network.

Idempotent is not the same as self-updating. Weather observations are upserted,
so re-seeding refreshes them. Policy terms are not: an issued contract is never
rewritten, so if the demo configuration here has changed since a database was
seeded, this refuses rather than leaving the two disagreeing.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from decimal import Decimal

from app import models
from app.core.database import SessionLocal
from app.services.weather import cache
from app.services.weather.providers import FixtureProvider

DEMO_CELLS = [(11.0, 77.0), (11.3, 77.7), (11.1, 77.3), (10.4, 77.9)]

# How much history the demo loads into the weather cache.
#
# The risk engine reads the cache, not the fixture files, so this bounds how
# many historical seasons a 35-year burn analysis can actually evaluate. At the
# previous 120 days exactly one season was complete, and the engine correctly
# reported SEVERE at 100% off a sample of one. Loading the full span the
# fixtures cover gives all 35 seasons and moves data_quality to `sufficient`.
DEMO_LOOKBACK_DAYS = 365 * 35

DEMO_FARM = {
    "farmer_name": "Murugan",
    "location": "Pollachi, Coimbatore",
    "latitude": 11.02,
    "longitude": 76.98,
    "crop": "maize",
    "area_acres": 3.0,
    "crop_stage": "flowering",
}

# DEMO THRESHOLD — NOT AN AGRONOMIC RECOMMENDATION.
#
# 30 mm is a demo calibration chosen against the *synthetic* fixture series, so
# that the Golden Demo exercises a realistic, non-degenerate risk band. It is
# not derived from crop water requirements and it is not scientifically
# validated. A real deployment would set this from published crop water
# requirements and district rainfall normals.
#
# Why 30 mm, measured on the committed fixtures for this farm and window
# (30-day window, 35 eligible seasons, totals ranging 15–137 mm, median 41 mm):
#
#     < 20 mm ->  1/35 =  2.86%  LOW      too rare to demonstrate a payout
#     < 25 mm ->  3/35 =  8.57%  LOW
#     < 30 mm ->  7/35 = 20.00%  MEDIUM   <- chosen
#     < 35 mm -> 13/35 = 37.14%  HIGH
#     < 40 mm -> 17/35 = 48.57%  SEVERE
#     <120 mm -> 34/35 = 97.14%  SEVERE   the previous value: fires nearly always
#
# 30 mm sits below the median of the distribution, so a breach represents a
# genuinely unusual dry season rather than a typical one, and it yields roughly
# one season in five — a frequency a parametric product could plausibly insure.
DEMO_THRESHOLD_MM = 30.0

# DEMO SEASON ANCHOR — pinned so the rehearsed number is reproducible.
#
# Burn analysis aligns every historical season to the same calendar position as
# `season_end`, so an anchor of `today` makes the result move by the day. It did:
# the same fixtures, threshold and window read 7 triggered seasons (20.00%) on
# 19 August and 8 (22.86%) on the 20th, because one more season crossed the
# threshold as the window slid forward. Both numbers are correct; neither is
# stable enough to rehearse against or to print in a slide.
#
# Pinning the anchor fixes the calendar position, not the analysis. The engine,
# its coverage rules, its bands and the fixtures are all untouched, and the
# request still travels through the ordinary `season_end` field of the public
# risk API — no demo-only code path exists in the engine.
#
# Measured at this anchor on the committed fixtures: 35 of 35 seasons eligible,
# 7 triggered, 20.00%, MEDIUM, sufficient/high. Neighbouring anchors stay inside
# the MEDIUM band (17.14%–22.86% over 17–21 August), so the pin is not balanced
# on a band boundary — only the exact score depends on it.
#
# The frontend carries the same date in DEMO_DEFAULTS.season_end and sends it
# with every demo risk request; tests/test_demo_config.py fails if the two drift.
DEMO_SEASON_END = date(2026, 8, 19)

DEMO_POLICY = {
    "coverage_amount": Decimal("72000.00"),
    "premium": Decimal("2169.00"),
    "trigger_type": "drought",
    "threshold_mm": DEMO_THRESHOLD_MM,
    "window_days": 30,
}


class DemoSeedError(RuntimeError):
    """The database already holds a demo policy written on different terms."""


def seed_weather(db, days: int = DEMO_LOOKBACK_DAYS) -> int:
    provider = FixtureProvider()
    end = date.today()
    start = end - timedelta(days=days)
    total = 0
    for lat, lon in DEMO_CELLS:
        result = cache.ingest(db, lat, lon, start, end, provider=provider)
        total += result["observations_written"]
        print(f"  cell {lat:.1f},{lon:.1f}: {result['observations_written']} observations")
    return total


def policy_mismatches(policy: models.Policy) -> list[tuple[str, object, object]]:
    """Fields where an existing policy disagrees with the current DEMO_POLICY.

    Returns (field, expected, found) in declaration order, empty when the two
    agree. Decimal and float compare numerically, so a Money column read back
    as 72000.0000 still matches Decimal("72000.00").
    """
    differences = []
    for field, expected in DEMO_POLICY.items():
        found = getattr(policy, field)
        if found != expected:
            differences.append((field, expected, found))
    return differences


def _stale_policy_message(
    policy: models.Policy, mismatches: list[tuple[str, object, object]]
) -> str:
    """Say what differs and what to do about it.

    Refusing is the point. Rewriting the terms would be the easy fix and the
    wrong one: a policy's trigger terms are frozen at issue precisely so that a
    contract cannot be changed underneath a farmer who already holds it. The
    seeder is not entitled to an exemption just because the database is a demo.
    """
    rows = "\n".join(
        f"      {field:<16} expected {expected!s:<12} found {found!s}"
        for field, expected, found in mismatches
    )
    return (
        f"Demo policy #{policy.id} already exists on different terms:\n\n"
        f"{rows}\n\n"
        "    Policy terms are frozen once issued, so seeding will not rewrite\n"
        "    them. The demo would otherwise run on the stored terms while the\n"
        "    configuration here claimed otherwise — a refreshed weather cache\n"
        "    makes that look healthy while showing the wrong risk band.\n\n"
        "    `make demo-reset` does not help: it clears evaluations, payouts\n"
        "    and simulated weather, not policy terms. Start from a fresh\n"
        "    database instead:\n\n"
        "      PostgreSQL:  docker compose down -v && make db-up\n"
        "      SQLite:      delete the database file\n"
        "      then:        make migrate && make seed-demo"
    )


def seed_demo_entities(db) -> tuple[models.Farm, models.Policy]:
    farm = db.query(models.Farm).filter_by(farmer_name=DEMO_FARM["farmer_name"]).first()
    if farm is None:
        farm = models.Farm(**DEMO_FARM)
        farm.grid_cell_id = cache.get_or_create_cell(db, farm.latitude, farm.longitude).id
        db.add(farm)
        db.commit()
        db.refresh(farm)
        print(f"  farm #{farm.id}: {farm.farmer_name}, {farm.location}")
    else:
        print(f"  farm #{farm.id}: already present")

    policy = db.query(models.Policy).filter_by(farm_id=farm.id).first()
    if policy is None:
        policy = models.Policy(farm_id=farm.id, **DEMO_POLICY)
        db.add(policy)
        db.commit()
        db.refresh(policy)
        print(f"  policy #{policy.id}: {policy.trigger_type} below {policy.threshold_mm}mm")
    else:
        mismatches = policy_mismatches(policy)
        if mismatches:
            raise DemoSeedError(_stale_policy_message(policy, mismatches))
        print(f"  policy #{policy.id}: already present")
    return farm, policy


def reset(db) -> None:
    from app.services.evaluation import reset_policy

    for policy in db.query(models.Policy).all():
        result = reset_policy(db, policy.id)
        print(
            f"  policy #{policy.id}: -{result['triggers_deleted']} evaluations, "
            f"-{result['payouts_deleted']} payouts, "
            f"-{result['simulated_observations_deleted']} simulated observations"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weather-only", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument(
        "--days",
        type=int,
        default=DEMO_LOOKBACK_DAYS,
        help=(
            "days of history to load into the weather cache "
            f"(default {DEMO_LOOKBACK_DAYS}, i.e. 35 years — the risk engine "
            "reads the cache, so this bounds how many seasons it can evaluate)"
        ),
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.reset:
            print("Resetting demo state...")
            reset(db)
            print("Done. Rehearse again.")
            return
        print("Seeding weather cache from fixtures...")
        total = seed_weather(db, args.days)
        print(f"  {total} observations cached")
        if not args.weather_only:
            print("Seeding demo entities...")
            try:
                seed_demo_entities(db)
            except DemoSeedError as exc:
                # An actionable message beats a traceback: whoever runs this is
                # setting up a demo, not debugging the seeder.
                raise SystemExit(f"\nSeeding stopped.\n\n  {exc}\n") from None
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

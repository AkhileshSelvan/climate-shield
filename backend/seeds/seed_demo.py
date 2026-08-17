"""Seed the database for local development and the demo.

Idempotent: running it twice produces the same database. Uses the fixture
weather provider only, so it never needs a network.
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

DEMO_FARM = {
    "farmer_name": "Murugan",
    "location": "Pollachi, Coimbatore",
    "latitude": 11.02,
    "longitude": 76.98,
    "crop": "maize",
    "area_acres": 3.0,
    "crop_stage": "flowering",
}

DEMO_POLICY = {
    "coverage_amount": Decimal("72000.00"),
    "premium": Decimal("2169.00"),
    "trigger_type": "drought",
    "threshold_mm": 120.0,
    "window_days": 30,
}


def seed_weather(db, days: int = 120) -> int:
    provider = FixtureProvider()
    end = date.today()
    start = end - timedelta(days=days)
    total = 0
    for lat, lon in DEMO_CELLS:
        result = cache.ingest(db, lat, lon, start, end, provider=provider)
        total += result["observations_written"]
        print(f"  cell {lat:.1f},{lon:.1f}: {result['observations_written']} observations")
    return total


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
    parser.add_argument("--days", type=int, default=120)
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
            seed_demo_entities(db)
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

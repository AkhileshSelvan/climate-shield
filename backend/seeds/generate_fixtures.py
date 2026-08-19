"""Generate offline weather fixtures.

Preferred path: fetch real ERA5 data from Open-Meteo and commit it.
    python seeds/generate_fixtures.py --live

Fallback: deterministic synthetic series from published regional monsoon
normals, used only when no developer machine can reach the API. Synthetic files
are labelled `"synthetic": true` and the API surfaces that label, so generated
numbers are never presented as measurements.
    python seeds/generate_fixtures.py
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent / "weather"

# Demo cells: Tamil Nadu districts, snapped to the 0.1 degree grid.
CELLS = [
    {"lat": 11.0, "lon": 77.0, "label": "Pollachi / Coimbatore"},
    {"lat": 11.3, "lon": 77.7, "label": "Erode"},
    {"lat": 11.1, "lon": 77.3, "label": "Tiruppur"},
    {"lat": 10.4, "lon": 77.9, "label": "Dindigul"},
]

# Mean daily rainfall (mm) by calendar month for the interior Tamil Nadu
# plains: dry Jan-May, south-west monsoon Jun-Sep, north-east monsoon Oct-Dec.
MONTHLY_MEAN_MM = {
    1: 0.4, 2: 0.3, 3: 0.5, 4: 1.5, 5: 2.0, 6: 1.4,
    7: 1.6, 8: 1.9, 9: 2.4, 10: 5.0, 11: 5.5, 12: 2.2,
}


def synthetic_series(lat: float, lon: float, start: date, end: date) -> list[dict]:
    # Seeded on the cell so regenerating always produces identical fixtures.
    rng = random.Random(f"climateshield:{lat}:{lon}")
    rows, day = [], start
    while day <= end:
        mean = MONTHLY_MEAN_MM[day.month]
        # Rainfall is intermittent: most days dry, occasional heavy day.
        if rng.random() < 0.72:
            value = 0.0
        else:
            value = round(rng.expovariate(1.0 / (mean * 3.2)), 2)
        rows.append({"date": day.isoformat(), "precipitation_mm": value})
        day += timedelta(days=1)
    return rows


def live_series(lat: float, lon: float, start: date, end: date) -> list[dict]:
    import requests

    response = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": lat, "longitude": lon,
            "start_date": start.isoformat(), "end_date": end.isoformat(),
            "daily": "precipitation_sum", "timezone": "auto",
        },
        timeout=60,
    )
    response.raise_for_status()
    daily = response.json()["daily"]
    return [
        {"date": d, "precipitation_mm": float(v or 0.0)}
        for d, v in zip(daily["time"], daily["precipitation_sum"])
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="fetch real ERA5 data")
    parser.add_argument("--years", type=int, default=2)
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        default=None,
        help=(
            "first day, ISO format (default: --years back from today). Pin this to "
            "the existing start_date when extending fixtures: the series is seeded "
            "per cell and walked forward, so an unchanged start reproduces every "
            "committed value exactly and only appends new days."
        ),
    )
    parser.add_argument(
        "--forward-days",
        type=int,
        default=120,
        help=(
            "days of synthetic coverage past today. Evaluation requires a complete "
            "window, so fixtures that stop on their generation date start refusing "
            "to settle the day after. Ignored with --live: there are no real "
            "observations for days that have not happened yet."
        ),
    )
    args = parser.parse_args()

    today = date.today()
    start = args.start or today - timedelta(days=365 * args.years)
    end = today if args.live else today + timedelta(days=args.forward_days)
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    for cell in CELLS:
        lat, lon = cell["lat"], cell["lon"]
        if args.live:
            rows = live_series(lat, lon, start, end)
            source, synthetic = "open-meteo-era5", False
        else:
            rows = synthetic_series(lat, lon, start, end)
            source, synthetic = "synthetic-regional-normals", True

        path = FIXTURE_DIR / f"cell_{lat:.1f}_{lon:.1f}.json"
        path.write_text(
            json.dumps(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "label": cell["label"],
                    "source": source,
                    "synthetic": synthetic,
                    "generated_on": today.isoformat(),
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "note": (
                        "Synthetic series from published regional monsoon normals. "
                        "Days after generated_on are placeholder values, not "
                        "forecasts: they exist so an offline demo run on a later "
                        "date still has a complete evaluation window. "
                        "Replace with real ERA5 via --live before the demo."
                        if synthetic
                        else "Real ERA5 daily precipitation via Open-Meteo archive."
                    ),
                    "daily": rows,
                },
                indent=1,
            )
        )
        print(f"wrote {path.name}: {len(rows)} days, synthetic={synthetic}")


if __name__ == "__main__":
    main()

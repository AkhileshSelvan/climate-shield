"""Weather providers.

A provider is an *ingestion* source. It is never called from a request that
evaluates a trigger — those read from the `weather_observations` cache. This is
what lets the whole demo path run with the network disconnected, and what makes
a settled policy reproducible from stored data alone.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class WeatherProviderError(RuntimeError):
    pass


# Any source name beginning with this prefix is generated data, not measurement.
# The convention lets provenance survive into the cache as a single string, so no
# extra column is needed to tell a reader that a number was not observed.
SYNTHETIC_SOURCE_PREFIX = "synthetic-"


def is_synthetic_source(source: str) -> bool:
    return source.startswith(SYNTHETIC_SOURCE_PREFIX)


class WeatherProvider(Protocol):
    """Returns [{"date": "YYYY-MM-DD", "precipitation_mm": float}, ...]."""

    name: str

    def fetch_daily_precipitation(
        self, latitude: float, longitude: float, start: date, end: date
    ) -> list[dict]: ...

    def source_for(self, latitude: float, longitude: float) -> str:
        """The provenance to record for data this provider is about to return.

        Usually the provider's own name. FixtureProvider is the exception: a
        fixture file is a container, and what matters is who produced what is
        inside it — regenerating with `--live` puts real ERA5 measurements in
        the same file a synthetic series occupied before.
        """
        ...


class FixtureProvider:
    """Reads committed JSON fixtures. The default in development, test and demo.

    Because this is the default rather than the emergency path, the offline
    route is the one exercised hundreds of times during the build.
    """

    name = "fixture"

    def __init__(self, fixture_dir: Path | None = None):
        self.fixture_dir = Path(fixture_dir or get_settings().fixture_dir)

    def _path_for(self, latitude: float, longitude: float) -> Path:
        return self.fixture_dir / f"cell_{latitude:.1f}_{longitude:.1f}.json"

    def load_cell(self, latitude: float, longitude: float) -> dict:
        path = self._path_for(latitude, longitude)
        if not path.exists():
            raise WeatherProviderError(
                f"No weather fixture for cell ({latitude:.1f}, {longitude:.1f}). "
                f"Expected {path}. Run `make seed` or add the fixture."
            )
        return json.loads(path.read_text())

    def fetch_daily_precipitation(
        self, latitude: float, longitude: float, start: date, end: date
    ) -> list[dict]:
        payload = self.load_cell(latitude, longitude)
        rows = payload.get("daily", [])
        return [
            r for r in rows if start.isoformat() <= r["date"] <= end.isoformat()
        ]

    def source_for(self, latitude: float, longitude: float) -> str:
        """The producer named in the fixture header, not "fixture".

        A file refreshed by `make fixtures-live` holds real ERA5 measurements.
        Recording it as "fixture" would let the risk API describe measured
        weather as synthetic, which is the opposite of the truth.
        """
        payload = self.load_cell(latitude, longitude)
        source = payload.get("source")
        if source:
            return str(source)
        # No header to trust: assume generated, which is the safe direction.
        return f"{SYNTHETIC_SOURCE_PREFIX}unlabelled"


class OpenMeteoProvider:
    """Live ERA5 archive. Opt-in, used only by explicit ingestion."""

    name = "open-meteo-era5"

    def fetch_daily_precipitation(
        self, latitude: float, longitude: float, start: date, end: date
    ) -> list[dict]:
        import requests  # imported lazily: offline runs never need it

        settings = get_settings()
        try:
            response = requests.get(
                settings.open_meteo_archive_url,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "daily": "precipitation_sum",
                    "timezone": "auto",
                },
                timeout=settings.open_meteo_timeout_seconds,
            )
            response.raise_for_status()
        except Exception as exc:  # network, DNS, HTTP, proxy policy
            raise WeatherProviderError(f"Open-Meteo request failed: {exc}") from exc

        daily = response.json().get("daily", {})
        dates = daily.get("time", []) or []
        values = daily.get("precipitation_sum", []) or []
        return [
            {"date": d, "precipitation_mm": float(v)}
            for d, v in zip(dates, values)
            if v is not None
        ]

    def source_for(self, latitude: float, longitude: float) -> str:
        """Fetched live, so the provider name is the provenance."""
        return self.name


_PROVIDERS = {
    "fixture": FixtureProvider,
    "open-meteo": OpenMeteoProvider,
    "open-meteo-era5": OpenMeteoProvider,
}


def get_provider(name: str | None = None) -> WeatherProvider:
    key = (name or get_settings().weather_provider).lower()
    if key not in _PROVIDERS:
        raise WeatherProviderError(
            f"Unknown weather provider {key!r}. Known: {sorted(_PROVIDERS)}"
        )
    return _PROVIDERS[key]()


def default_window(days: int, end: date | None = None) -> tuple[date, date]:
    end = end or date.today()
    return end - timedelta(days=days), end

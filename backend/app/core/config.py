"""Application settings, sourced from the environment."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # PostgreSQL is the approved architecture. SQLite remains available for
    # tests and quick local runs, but it is not the deployment target.
    database_url: str = "postgresql+psycopg2://climateshield:climateshield@localhost:5432/climateshield"

    # Which WeatherProvider the app uses. "fixture" is the default so that the
    # offline path is the one exercised during development.
    weather_provider: str = "fixture"

    fixture_dir: Path = BACKEND_DIR / "seeds" / "weather"

    # Grid resolution used to snap farms to shared weather cells (degrees).
    grid_resolution_deg: float = 0.1

    open_meteo_archive_url: str = "https://archive-api.open-meteo.com/v1/archive"
    open_meteo_timeout_seconds: float = 10.0


@lru_cache
def get_settings() -> Settings:
    return Settings()

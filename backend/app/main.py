from fastapi import FastAPI

from app.api.v1 import farms, payouts, policies, risk, simulate, triggers, weather
from app.core.config import get_settings
from app.core.database import Base, engine

settings = get_settings()

app = FastAPI(
    title="ClimateShield API",
    description=(
        "Parametric climate-risk insurance for smallholder farmers. "
        "Trigger evaluation is deterministic and reads only from the local "
        "weather cache, so the full path runs without network access."
    ),
    version="0.2.0",
)

# Schema is created by Alembic in any real environment; this keeps a fresh
# SQLite dev database usable without a migration step.
Base.metadata.create_all(bind=engine)

API_PREFIX = "/api/v1"
ROUTERS = (farms, weather, policies, triggers, payouts, simulate, risk)

for module in ROUTERS:
    app.include_router(module.router, prefix=API_PREFIX)
    # Legacy unprefixed paths from the first backend, kept working so nobody's
    # in-flight work breaks. Hidden from the schema; /api/v1 is canonical.
    app.include_router(module.router, include_in_schema=False)


@app.get("/health", tags=["Ops"])
def health():
    return {
        "status": "ok",
        "message": "ClimateShield backend is running",
        "weather_provider": settings.weather_provider,
        "database": settings.database_url.split("://", 1)[0],
    }

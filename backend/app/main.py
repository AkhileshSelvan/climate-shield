from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Alembic owns the schema everywhere it can. Creating tables here against a
# PostgreSQL database would leave them unstamped — no alembic_version row — so a
# later `alembic upgrade head` fails trying to create tables that already exist.
# SQLite is the quick-start and test path, so keep the convenience there only.
if engine.dialect.name == "sqlite":
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

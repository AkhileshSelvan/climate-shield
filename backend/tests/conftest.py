"""Test fixtures.

Tests run against SQLite for speed and zero setup. The Money type is dialect-
aware, so decimal behaviour is verified on the same code path PostgreSQL uses.
"""
import os
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("WEATHER_PROVIDER", "fixture")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = BACKEND_DIR / "seeds" / "weather"


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def farm(client):
    response = client.post(
        "/api/v1/farms/",
        json={
            "farmer_name": "Murugan",
            "location": "Pollachi, Coimbatore",
            "latitude": 11.0,
            "longitude": 77.0,
            "crop": "maize",
            "area_acres": 3.0,
            "crop_stage": "flowering",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture()
def drought_policy(client, farm):
    response = client.post(
        "/api/v1/policies/",
        json={
            "farm_id": farm["id"],
            "coverage_amount": "72000.00",
            "premium": "2169.00",
            "trigger_type": "drought",
            "threshold_mm": 120.0,
            "window_days": 30,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()

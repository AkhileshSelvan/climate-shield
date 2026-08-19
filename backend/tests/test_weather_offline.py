"""(e) Offline weather fixture — the demo must work with no network."""
import socket
from datetime import date, timedelta

import pytest

from app.services.weather import cache
from app.services.weather.providers import (
    FixtureProvider,
    OpenMeteoProvider,
    WeatherProviderError,
    get_provider,
)


@pytest.fixture()
def no_network(monkeypatch):
    """Block outbound connections while leaving in-process plumbing intact.

    Patching socket.socket wholesale would break asyncio's self-pipe (built with
    socket.socketpair) and the test client with it. Blocking connect() and
    create_connection stops real egress without touching anything local.
    """
    def _blocked_connect(self, address, *args, **kwargs):
        raise AssertionError(f"Network access attempted during an offline test: {address}")

    def _blocked(*args, **kwargs):
        raise AssertionError("Network access attempted during an offline test")

    monkeypatch.setattr(socket.socket, "connect", _blocked_connect)
    monkeypatch.setattr(socket, "create_connection", _blocked)

    import requests
    monkeypatch.setattr(requests.sessions.Session, "request", _blocked)
    return True


def test_default_provider_is_the_offline_one():
    """The offline path is the default, so it is the one that gets exercised."""
    assert isinstance(get_provider(), FixtureProvider)


def test_fixture_provider_reads_committed_data(no_network):
    provider = FixtureProvider()
    end = date.today()
    rows = provider.fetch_daily_precipitation(11.0, 77.0, end - timedelta(days=30), end)
    assert len(rows) > 0
    assert all("date" in r and "precipitation_mm" in r for r in rows)


def test_fixture_provenance_is_labelled(no_network):
    """Synthetic data must never be presented as a measurement."""
    payload = FixtureProvider().load_cell(11.0, 77.0)
    assert "source" in payload and "synthetic" in payload
    if payload["synthetic"]:
        assert "synthetic" in payload["note"].lower()


def test_missing_fixture_fails_with_a_useful_message(no_network):
    with pytest.raises(WeatherProviderError, match="No weather fixture"):
        FixtureProvider().fetch_daily_precipitation(0.0, 0.0, date.today(), date.today())


def test_full_happy_path_with_network_disabled(client, db_session, no_network):
    """Register a farm, ingest from fixtures, evaluate, get paid — offline."""
    farm = client.post(
        "/api/v1/farms/",
        json={
            "farmer_name": "Murugan", "location": "Pollachi", "latitude": 11.0,
            "longitude": 77.0, "crop": "maize", "area_acres": 3.0,
        },
    ).json()
    assert farm["grid_cell_id"] is not None

    ingest = client.post(
        "/api/v1/weather/ingest", json={"farm_id": farm["id"], "days": 60}
    ).json()
    assert ingest["provider"] == "fixture"
    assert ingest["observations_written"] > 0

    weather = client.get(f"/api/v1/weather/{farm['id']}?days=30").json()
    assert weather["observations_used"] > 0

    policy = client.post(
        "/api/v1/policies/",
        json={
            "farm_id": farm["id"], "coverage_amount": "72000.00", "premium": "2169.00",
            # Threshold set high so cached rainfall is certain to breach it.
            "trigger_type": "drought", "threshold_mm": 9999.0, "window_days": 30,
        },
    ).json()

    result = client.post(f"/api/v1/triggers/check/{policy['id']}").json()
    assert result["triggered"] is True
    assert result["observations_used"] > 0
    # The producer named in the fixture header, not "fixture" the container.
    assert result["data_source"] == "synthetic-regional-normals"
    assert result["payout"]["amount"] == "21600.00"

    payouts = client.get(f"/api/v1/payouts/?policy_id={policy['id']}").json()
    assert len(payouts) == 1


def test_evaluation_never_calls_the_network(client, farm, drought_policy, no_network):
    """Trigger evaluation reads the cache only — proven by the socket block."""
    client.post("/api/v1/weather/ingest", json={"farm_id": farm["id"], "days": 60})
    response = client.post(f"/api/v1/triggers/check/{drought_policy['id']}")
    assert response.status_code == 200


def test_missing_cache_refuses_rather_than_assuming_zero_rain(client, drought_policy, no_network):
    """A gap read as zero rainfall would manufacture a drought. Refuse instead."""
    response = client.post(f"/api/v1/triggers/check/{drought_policy['id']}")
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "Incomplete weather cache" in detail
    # The message must name the shortfall, so an operator knows what to ingest.
    assert "0 of 31 days present" in detail


def test_live_provider_failure_is_contained(monkeypatch):
    """A dead API surfaces as a provider error, never as an unhandled crash."""
    import requests

    def _boom(*args, **kwargs):
        raise requests.exceptions.ConnectionError("proxy denied")

    monkeypatch.setattr(requests, "get", _boom)
    with pytest.raises(WeatherProviderError, match="Open-Meteo request failed"):
        OpenMeteoProvider().fetch_daily_precipitation(11.0, 77.0, date.today(), date.today())


def test_simulated_observations_take_precedence(client, db_session, farm, no_network):
    """Injected demo weather overrides history without destroying it."""
    client.post("/api/v1/weather/ingest", json={"farm_id": farm["id"], "days": 30})
    cell_id = client.get(f"/api/v1/farms/{farm['id']}").json()["grid_cell_id"]
    today = date.today()

    cell = db_session.query(cache.models.WeatherGridCell).filter_by(id=cell_id).one()
    cache.upsert_observations(
        db_session, cell,
        [{"date": today.isoformat(), "precipitation_mm": 999.0}],
        source=cache.SIMULATED_SOURCE, is_simulated=True,
    )
    summary = cache.summarise_window(db_session, cell_id, today, today)
    assert summary["total_rainfall_mm"] == 999.0
    assert summary["is_simulated"] is True

    assert cache.clear_simulated(db_session, cell_id) == 1
    assert cache.summarise_window(db_session, cell_id, today, today)["is_simulated"] is False


def _drought_policy_for(client, farm_id, threshold_mm=9999.0):
    return client.post(
        "/api/v1/policies/",
        json={
            "farm_id": farm_id, "coverage_amount": "72000.00", "premium": "2169.00",
            "trigger_type": "drought", "threshold_mm": threshold_mm, "window_days": 30,
        },
    ).json()


def test_complete_window_settles_normally(client, farm, no_network):
    """Positive control: the strict completeness check must not block good data."""
    client.post("/api/v1/weather/ingest", json={"farm_id": farm["id"], "days": 60})
    policy = _drought_policy_for(client, farm["id"])

    response = client.post(f"/api/v1/triggers/check/{policy['id']}")
    assert response.status_code == 200, response.text
    # window_days=30 spans 31 inclusive days, and all of them are cached.
    assert response.json()["observations_used"] == 31


def test_a_gap_in_the_window_refuses_to_settle(client, db_session, farm, no_network):
    """A missing day is not a dry day.

    Dropping days from a drought window lowers the observed total, so partial
    data can breach a threshold that complete data would not. That is a payout
    manufactured by a gap in ingestion. Refuse instead of settling.
    """
    from app import models

    client.post("/api/v1/weather/ingest", json={"farm_id": farm["id"], "days": 60})
    policy = _drought_policy_for(client, farm["id"])

    # Punch a single day out of the middle of the window.
    missing = date.today() - timedelta(days=15)
    deleted = (
        db_session.query(models.WeatherObservation)
        .filter(models.WeatherObservation.obs_date == missing)
        .delete(synchronize_session=False)
    )
    db_session.commit()
    assert deleted == 1

    response = client.post(f"/api/v1/triggers/check/{policy['id']}")
    assert response.status_code == 409
    assert "30 of 31 days present" in response.json()["detail"]
    # Nothing was settled on the partial window.
    assert db_session.query(models.Trigger).filter_by(policy_id=policy["id"]).count() == 0


def test_a_window_reaching_past_the_cache_refuses_to_settle(client, farm, no_network):
    """The trailing-edge case: ingestion stops short of the evaluation date."""
    client.post("/api/v1/weather/ingest", json={"farm_id": farm["id"], "days": 10})
    policy = _drought_policy_for(client, farm["id"])

    response = client.post(f"/api/v1/triggers/check/{policy['id']}")
    assert response.status_code == 409
    assert "11 of 31 days present" in response.json()["detail"]


def test_snap_returns_storable_decimals():
    """Coordinates must snap to the precision they are stored at."""
    from decimal import Decimal

    from app.services.weather import grid

    lat, lon = grid.snap(11.02, 76.98)
    assert isinstance(lat, Decimal) and isinstance(lon, Decimal)
    assert (lat, lon) == (Decimal("11.000000"), Decimal("77.000000"))


def test_a_stored_coordinate_still_finds_its_own_cell(client, db_session, farm):
    """The round-trip that a float comparison can lose.

    A farm's coordinates come back from the database as Decimal. Re-snapping
    those stored values must find the cell the farm already points at, not miss
    it and try to insert a duplicate.
    """
    from app import models
    from app.services.weather import cache

    stored = db_session.query(models.Farm).filter_by(id=farm["id"]).one()
    cells_before = db_session.query(models.WeatherGridCell).count()

    again = cache.get_or_create_cell(db_session, stored.latitude, stored.longitude)

    assert again.id == stored.grid_cell_id
    assert db_session.query(models.WeatherGridCell).count() == cells_before


def test_two_pins_in_one_cell_share_a_single_grid_row(client, db_session):
    """The point of the shared grid: neighbours reuse one weather row."""
    from app import models

    def make(name, lat, lon):
        return client.post(
            "/api/v1/farms/",
            json={
                "farmer_name": name, "location": "Pollachi", "latitude": lat,
                "longitude": lon, "crop": "maize", "area_acres": 2.0,
            },
        ).json()

    a = make("Murugan", 11.02, 76.98)
    b = make("Selvi", 11.04, 76.96)

    assert a["grid_cell_id"] == b["grid_cell_id"]
    assert db_session.query(models.WeatherGridCell).count() == 1

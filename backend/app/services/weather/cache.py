"""The weather cache: the single source of truth for trigger evaluation.

Reads never touch the network. Providers write here; evaluation reads here.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app import models
from app.services.weather import grid
from app.services.weather.providers import WeatherProvider, get_provider

SIMULATED_SOURCE = "simulated"


def get_or_create_cell(db: Session, latitude: float, longitude: float) -> models.WeatherGridCell:
    lat, lon = grid.snap(latitude, longitude)
    cell = (
        db.query(models.WeatherGridCell)
        .filter(models.WeatherGridCell.latitude == lat)
        .filter(models.WeatherGridCell.longitude == lon)
        .first()
    )
    if cell is None:
        cell = models.WeatherGridCell(latitude=lat, longitude=lon, label=f"{lat:.1f},{lon:.1f}")
        db.add(cell)
        db.commit()
        db.refresh(cell)
    return cell


def upsert_observations(
    db: Session,
    cell: models.WeatherGridCell,
    rows: list[dict],
    source: str,
    is_simulated: bool = False,
) -> int:
    """Insert or update daily rows. Idempotent: re-ingesting the same range
    updates in place rather than duplicating."""
    written = 0
    for row in rows:
        obs_date = row["date"]
        if isinstance(obs_date, str):
            obs_date = date.fromisoformat(obs_date)
        existing = (
            db.query(models.WeatherObservation)
            .filter(models.WeatherObservation.grid_cell_id == cell.id)
            .filter(models.WeatherObservation.obs_date == obs_date)
            .filter(models.WeatherObservation.source == source)
            .first()
        )
        if existing:
            existing.precipitation_mm = float(row["precipitation_mm"])
            existing.is_simulated = is_simulated
        else:
            db.add(
                models.WeatherObservation(
                    grid_cell_id=cell.id,
                    obs_date=obs_date,
                    source=source,
                    precipitation_mm=float(row["precipitation_mm"]),
                    is_simulated=is_simulated,
                )
            )
        written += 1
    db.commit()
    return written


def ingest(
    db: Session,
    latitude: float,
    longitude: float,
    start: date,
    end: date,
    provider: WeatherProvider | None = None,
) -> dict:
    """Populate the cache from a provider. The ONLY path that may hit a network."""
    provider = provider or get_provider()
    cell = get_or_create_cell(db, latitude, longitude)
    rows = provider.fetch_daily_precipitation(float(cell.latitude), float(cell.longitude), start, end)
    written = upsert_observations(db, cell, rows, source=provider.name)
    return {
        "grid_cell_id": cell.id,
        "latitude": float(cell.latitude),
        "longitude": float(cell.longitude),
        "provider": provider.name,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "observations_written": written,
    }


def read_window(db: Session, cell_id: int, start: date, end: date) -> list[models.WeatherObservation]:
    """Cached observations in [start, end]. Simulated rows take precedence over
    real ones for the same day, so an injected demo scenario overrides history
    without destroying it."""
    rows = (
        db.query(models.WeatherObservation)
        .filter(models.WeatherObservation.grid_cell_id == cell_id)
        .filter(models.WeatherObservation.obs_date >= start)
        .filter(models.WeatherObservation.obs_date <= end)
        .order_by(models.WeatherObservation.obs_date)
        .all()
    )
    by_date: dict[date, models.WeatherObservation] = {}
    for row in rows:
        current = by_date.get(row.obs_date)
        if current is None or (row.is_simulated and not current.is_simulated):
            by_date[row.obs_date] = row
    return [by_date[d] for d in sorted(by_date)]


def summarise_window(db: Session, cell_id: int, start: date, end: date) -> dict:
    rows = read_window(db, cell_id, start, end)
    total = round(sum(r.precipitation_mm for r in rows), 2)
    sources = sorted({r.source for r in rows})
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "total_rainfall_mm": total,
        "observations_used": len(rows),
        "expected_days": (end - start).days + 1,
        "is_simulated": any(r.is_simulated for r in rows),
        "sources": sources,
        "daily_breakdown": [
            {"date": r.obs_date.isoformat(), "precipitation_mm": r.precipitation_mm}
            for r in rows
        ],
    }


def clear_simulated(db: Session, cell_id: int | None = None) -> int:
    q = db.query(models.WeatherObservation).filter(models.WeatherObservation.is_simulated.is_(True))
    if cell_id is not None:
        q = q.filter(models.WeatherObservation.grid_cell_id == cell_id)
    deleted = q.delete(synchronize_session=False)
    db.commit()
    return deleted

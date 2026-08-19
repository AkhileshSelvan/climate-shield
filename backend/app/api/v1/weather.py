from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db
from app.services.weather import cache
from app.services.weather.providers import (
    WeatherProviderError,
    default_window,
    get_provider,
)

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/{farm_id}")
def get_farm_weather(farm_id: int, days: int = 14, db: Session = Depends(get_db)):
    """Read cached weather for a farm. Never calls an external API."""
    farm = db.query(models.Farm).filter(models.Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if farm.grid_cell_id is None:
        raise HTTPException(status_code=400, detail="Farm has no coordinates set")

    start, end = default_window(days)
    summary = cache.summarise_window(db, farm.grid_cell_id, start, end)
    return {"farm_id": farm_id, "location": farm.location, "days": days, **summary}


@router.post("/ingest")
def ingest_weather(payload: schemas.WeatherIngestRequest, db: Session = Depends(get_db)):
    """Populate the weather cache. The only endpoint permitted to reach a
    network, and only when a live provider is explicitly selected."""
    if payload.farm_id is not None:
        farm = db.query(models.Farm).filter(models.Farm.id == payload.farm_id).first()
        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found")
        if farm.latitude is None or farm.longitude is None:
            raise HTTPException(status_code=400, detail="Farm has no coordinates set")
        latitude, longitude = farm.latitude, farm.longitude
    elif payload.latitude is not None and payload.longitude is not None:
        latitude, longitude = payload.latitude, payload.longitude
    else:
        raise HTTPException(
            status_code=400, detail="Provide either farm_id or latitude+longitude"
        )

    start, end = default_window(payload.days, payload.end_date or date.today())
    try:
        provider = get_provider(payload.provider)
        return cache.ingest(db, latitude, longitude, start, end, provider=provider)
    except WeatherProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

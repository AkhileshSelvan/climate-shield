from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from services.weather_service import get_rainfall_data

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/{farm_id}")
def get_farm_weather(farm_id: int, days: int = 14, db: Session = Depends(get_db)):
    farm = db.query(models.Farm).filter(models.Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if farm.latitude is None or farm.longitude is None:
        raise HTTPException(status_code=400, detail="Farm has no coordinates set")

    weather = get_rainfall_data(farm.latitude, farm.longitude, days=days)
    return {"farm_id": farm_id, "location": farm.location, **weather}

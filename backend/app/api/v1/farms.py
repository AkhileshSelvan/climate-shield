from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db
from app.services.weather import cache

router = APIRouter(prefix="/farms", tags=["Farms"])


@router.post("/", response_model=schemas.FarmResponse)
def create_farm(farm: schemas.FarmCreate, db: Session = Depends(get_db)):
    db_farm = models.Farm(**farm.model_dump())
    # Snap to a shared weather cell at creation so every downstream weather
    # lookup keys on the cell rather than on the farm.
    if db_farm.latitude is not None and db_farm.longitude is not None:
        db_farm.grid_cell_id = cache.get_or_create_cell(db, db_farm.latitude, db_farm.longitude).id
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm


@router.get("/{farm_id}", response_model=schemas.FarmResponse)
def get_farm(farm_id: int, db: Session = Depends(get_db)):
    farm = db.query(models.Farm).filter(models.Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.get("/", response_model=list[schemas.FarmResponse])
def list_farms(db: Session = Depends(get_db)):
    return db.query(models.Farm).all()

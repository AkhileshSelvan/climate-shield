from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.post("/", response_model=schemas.PolicyResponse)
def create_policy(policy: schemas.PolicyCreate, db: Session = Depends(get_db)):
    farm = db.query(models.Farm).filter(models.Farm.id == policy.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    db_policy = models.Policy(**policy.model_dump())
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy


@router.get("/{policy_id}", response_model=schemas.PolicyResponse)
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.get("/", response_model=list[schemas.PolicyResponse])
def list_policies(db: Session = Depends(get_db)):
    return db.query(models.Policy).all()

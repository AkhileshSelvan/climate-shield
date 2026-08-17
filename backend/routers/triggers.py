from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from services.weather_service import get_rainfall_data
from services.trigger_engine import evaluate_trigger
from services.payout_engine import calculate_payout

router = APIRouter(prefix="/triggers", tags=["Triggers"])


@router.post("/check/{policy_id}")
def check_trigger(policy_id: int, db: Session = Depends(get_db)):
    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    farm = db.query(models.Farm).filter(models.Farm.id == policy.farm_id).first()
    if not farm or farm.latitude is None or farm.longitude is None:
        raise HTTPException(status_code=400, detail="Farm has no coordinates set")

    weather = get_rainfall_data(farm.latitude, farm.longitude, days=policy.window_days)
    observed_rainfall = weather["total_rainfall_mm"]

    triggered = evaluate_trigger(policy.trigger_type, observed_rainfall, policy.threshold_mm)

    db_trigger = models.Trigger(
        policy_id=policy.id,
        observed_value=observed_rainfall,
        threshold_value=policy.threshold_mm,
        triggered=1 if triggered else 0,
    )
    db.add(db_trigger)
    db.commit()
    db.refresh(db_trigger)

    result = {
        "trigger_id": db_trigger.id,
        "policy_id": policy.id,
        "trigger_type": policy.trigger_type,
        "observed_rainfall_mm": observed_rainfall,
        "threshold_mm": policy.threshold_mm,
        "triggered": triggered,
    }

    if triggered:
        payout_amount = calculate_payout(policy.coverage_amount)
        db_payout = models.Payout(
            trigger_id=db_trigger.id,
            amount=payout_amount,
            status="initiated",
        )
        db.add(db_payout)
        db.commit()
        db.refresh(db_payout)
        result["payout"] = {
            "payout_id": db_payout.id,
            "amount": payout_amount,
            "status": db_payout.status,
        }

    return result

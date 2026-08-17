from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from services.trigger_engine import evaluate_trigger
from services.payout_engine import calculate_payout

router = APIRouter(prefix="/simulate", tags=["Simulator"])


def _run_simulation(policy_id: int, fake_rainfall_mm: float, db: Session):
    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    triggered = evaluate_trigger(policy.trigger_type, fake_rainfall_mm, policy.threshold_mm)

    db_trigger = models.Trigger(
        policy_id=policy.id,
        observed_value=fake_rainfall_mm,
        threshold_value=policy.threshold_mm,
        triggered=1 if triggered else 0,
    )
    db.add(db_trigger)
    db.commit()
    db.refresh(db_trigger)

    result = {
        "simulated": True,
        "trigger_id": db_trigger.id,
        "policy_id": policy.id,
        "trigger_type": policy.trigger_type,
        "observed_rainfall_mm": fake_rainfall_mm,
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


@router.post("/drought/{policy_id}")
def simulate_drought(policy_id: int, db: Session = Depends(get_db)):
    # Force a low rainfall value, matching the doc's demo example (11mm)
    return _run_simulation(policy_id, fake_rainfall_mm=11.0, db=db)


@router.post("/excess_rain/{policy_id}")
def simulate_excess_rain(policy_id: int, db: Session = Depends(get_db)):
    # Force a high rainfall value to breach an excess-rain threshold
    return _run_simulation(policy_id, fake_rainfall_mm=150.0, db=db)

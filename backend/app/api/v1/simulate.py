"""Admin weather simulation — the on-stage demo lever.

Compresses a season-long weather event into one click. Runs through exactly the
same evaluation and payout code as a real settlement, so what the audience sees
is the production path, not a mock.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.evaluation import EvaluationError, evaluate_policy, reset_policy

router = APIRouter(prefix="/simulate", tags=["Simulator"])

DROUGHT_RAINFALL_MM = 11.0
EXCESS_RAIN_RAINFALL_MM = 150.0


def _simulate(policy_id: int, rainfall_mm: float, evaluation_date: date | None, db: Session):
    try:
        result = evaluate_policy(
            db,
            policy_id,
            evaluation_date=evaluation_date,
            forced_rainfall_mm=rainfall_mm,
            is_simulated=True,
        )
    except EvaluationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    result["simulated"] = True
    return result


@router.post("/drought/{policy_id}")
def simulate_drought(
    policy_id: int, evaluation_date: date | None = None, db: Session = Depends(get_db)
):
    """Force a severe rainfall deficit. Idempotent for a given date."""
    return _simulate(policy_id, DROUGHT_RAINFALL_MM, evaluation_date, db)


@router.post("/excess_rain/{policy_id}")
def simulate_excess_rain(
    policy_id: int, evaluation_date: date | None = None, db: Session = Depends(get_db)
):
    """Force an excess-rainfall event. Idempotent for a given date."""
    return _simulate(policy_id, EXCESS_RAIN_RAINFALL_MM, evaluation_date, db)


@router.post("/reset/{policy_id}")
def reset(policy_id: int, db: Session = Depends(get_db)):
    """Clear evaluations, payouts and simulated weather so a rehearsal can be
    repeated. Real observations are preserved."""
    try:
        return reset_policy(db, policy_id)
    except EvaluationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

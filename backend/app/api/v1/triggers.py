from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.evaluation import EvaluationError, evaluate_policy

router = APIRouter(prefix="/triggers", tags=["Triggers"])


@router.post("/check/{policy_id}")
def check_trigger(
    policy_id: int,
    evaluation_date: date | None = None,
    db: Session = Depends(get_db),
):
    """Evaluate a policy against cached weather.

    Idempotent: one evaluation per policy per date. Calling this twice returns
    the same result and never creates a second payout.
    """
    try:
        return evaluate_policy(db, policy_id, evaluation_date=evaluation_date)
    except EvaluationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

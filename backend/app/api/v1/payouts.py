"""Read-only payout views.

There is deliberately no endpoint that creates a payout. Payouts originate only
inside the evaluation service, so every rupee traces to a stored evaluation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.core.database import get_db

router = APIRouter(prefix="/payouts", tags=["Payouts"])


def _serialise(payout: models.Payout) -> dict:
    return {
        "payout_id": payout.id,
        "trigger_id": payout.trigger_id,
        "policy_id": payout.trigger.policy_id if payout.trigger else None,
        "amount": str(payout.amount),
        "currency": "INR",
        "status": payout.status,
        "created_at": payout.created_at.isoformat() if payout.created_at else None,
    }


@router.get("/")
def list_payouts(policy_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Payout)
    if policy_id is not None:
        query = query.join(models.Trigger).filter(models.Trigger.policy_id == policy_id)
    return [_serialise(p) for p in query.all()]


@router.get("/{payout_id}")
def get_payout(payout_id: int, db: Session = Depends(get_db)):
    payout = db.query(models.Payout).filter(models.Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    return _serialise(payout)

"""The single idempotent path from policy to payout.

Both the real evaluation endpoint and the demo simulator call `evaluate_policy`.
There is exactly one place in the codebase that creates a Payout row, and it is
guarded by a uniqueness constraint on (policy_id, evaluation_date). Calling it
twice for the same day returns the first result and creates nothing.
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.services import trigger_engine
from app.services.payout_engine import PAYOUT_ENGINE_VERSION, calculate_payout
from app.services.weather import cache


class EvaluationError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _serialise(trigger: models.Trigger, payout: models.Payout | None, reused: bool) -> dict:
    result = {
        "trigger_id": trigger.id,
        "policy_id": trigger.policy_id,
        "evaluation_date": trigger.evaluation_date.isoformat(),
        "trigger_type": trigger.policy.trigger_type if trigger.policy else None,
        "observed_rainfall_mm": trigger.observed_value,
        "threshold_mm": trigger.threshold_value,
        "triggered": bool(trigger.triggered),
        "window_start": trigger.window_start.isoformat() if trigger.window_start else None,
        "window_end": trigger.window_end.isoformat() if trigger.window_end else None,
        "observations_used": trigger.observations_used,
        "data_source": trigger.data_source,
        "is_simulated": trigger.is_simulated,
        "engine_version": trigger.engine_version,
        "idempotent_reuse": reused,
    }
    if payout is not None:
        result["payout"] = {
            "payout_id": payout.id,
            "amount": str(payout.amount),
            "currency": "INR",
            "status": payout.status,
        }
    return result


def _existing(db: Session, policy_id: int, evaluation_date: date) -> models.Trigger | None:
    return (
        db.query(models.Trigger)
        .filter(models.Trigger.policy_id == policy_id)
        .filter(models.Trigger.evaluation_date == evaluation_date)
        .first()
    )


def _ensure_payout(
    db: Session, trigger: models.Trigger, policy: models.Policy
) -> models.Payout | None:
    """Return the payout for a triggered evaluation, creating it if it is missing.

    A trigger and its payout are committed separately, so a crash between the
    two, or a concurrent request reading in the gap, can leave a triggered
    evaluation with no payout. Every later call then takes the reuse path in
    `evaluate_policy`, so without this repair a valid claim would stay unpaid
    for good. Creating the payout is safe to retry: uq_payout_trigger allows
    only one per trigger, and losing that race just means reading the winner.
    """
    if not trigger.triggered:
        return None
    if trigger.payout is not None:
        return trigger.payout

    payout = models.Payout(
        trigger_id=trigger.id,
        amount=calculate_payout(policy.coverage_amount),
        status="initiated",
    )
    db.add(payout)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request created it first. Its row is the one that counts.
        db.rollback()
        return (
            db.query(models.Payout)
            .filter(models.Payout.trigger_id == trigger.id)
            .first()
        )
    db.refresh(payout)
    return payout


def evaluate_policy(
    db: Session,
    policy_id: int,
    evaluation_date: date | None = None,
    forced_rainfall_mm: float | None = None,
    is_simulated: bool = False,
) -> dict:
    """Evaluate one policy for one date, at most once.

    `forced_rainfall_mm` is used by the demo simulator to bypass the cache read;
    the comparison and payout logic are otherwise identical, so the simulated
    path exercises the same code that settles a real policy.
    """
    evaluation_date = evaluation_date or date.today()

    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()
    if not policy:
        raise EvaluationError("Policy not found", status_code=404)

    # Idempotency, fast path: already evaluated for this date.
    existing = _existing(db, policy_id, evaluation_date)
    if existing is not None:
        return _serialise(existing, _ensure_payout(db, existing, policy), reused=True)

    window_start = evaluation_date - timedelta(days=policy.window_days)
    window_end = evaluation_date

    if forced_rainfall_mm is not None:
        observed = float(forced_rainfall_mm)
        observations_used = 0
        data_source = "simulated"
    else:
        farm = db.query(models.Farm).filter(models.Farm.id == policy.farm_id).first()
        if not farm or farm.grid_cell_id is None:
            raise EvaluationError("Farm has no weather grid cell assigned", status_code=400)
        summary = cache.summarise_window(db, farm.grid_cell_id, window_start, window_end)
        expected_days = summary["expected_days"]
        if summary["observations_used"] < expected_days:
            # Settle on a complete window or not at all. A missing day is not a
            # dry day: counting gaps as zero rainfall manufactures a drought
            # that never happened, and the same gap hides a flood. Partial data
            # must fail loudly rather than quietly decide someone's claim.
            raise EvaluationError(
                f"Incomplete weather cache for {window_start.isoformat()} to "
                f"{window_end.isoformat()}: {summary['observations_used']} of "
                f"{expected_days} days present. Ingest the full window first "
                "(POST /api/v1/weather/ingest).",
                status_code=409,
            )
        observed = summary["total_rainfall_mm"]
        observations_used = summary["observations_used"]
        data_source = ",".join(summary["sources"])

    triggered = trigger_engine.evaluate_trigger(
        policy.trigger_type, observed, policy.threshold_mm
    )

    trigger = models.Trigger(
        policy_id=policy.id,
        evaluation_date=evaluation_date,
        observed_value=observed,
        threshold_value=policy.threshold_mm,
        triggered=1 if triggered else 0,
        window_start=window_start,
        window_end=window_end,
        observations_used=observations_used,
        data_source=data_source,
        is_simulated=is_simulated,
        engine_version=f"{trigger_engine.ENGINE_VERSION}/{PAYOUT_ENGINE_VERSION}",
    )
    db.add(trigger)
    try:
        db.commit()
    except IntegrityError:
        # Idempotency, race path: a concurrent request won. Return its result.
        db.rollback()
        winner = _existing(db, policy_id, evaluation_date)
        if winner is None:
            raise
        return _serialise(winner, _ensure_payout(db, winner, policy), reused=True)
    db.refresh(trigger)

    return _serialise(trigger, _ensure_payout(db, trigger, policy), reused=False)


def reset_policy(db: Session, policy_id: int) -> dict:
    """Clear evaluations, payouts and simulated weather for one policy.

    Rehearsal tooling: a demo you cannot repeat is not a rehearsal. Real
    (non-simulated) observations are left untouched.
    """
    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()
    if not policy:
        raise EvaluationError("Policy not found", status_code=404)

    triggers = db.query(models.Trigger).filter(models.Trigger.policy_id == policy_id).all()
    trigger_ids = [t.id for t in triggers]
    payouts_deleted = 0
    if trigger_ids:
        payouts_deleted = (
            db.query(models.Payout)
            .filter(models.Payout.trigger_id.in_(trigger_ids))
            .delete(synchronize_session=False)
        )
    triggers_deleted = (
        db.query(models.Trigger)
        .filter(models.Trigger.policy_id == policy_id)
        .delete(synchronize_session=False)
    )
    db.commit()

    farm = db.query(models.Farm).filter(models.Farm.id == policy.farm_id).first()
    simulated_deleted = cache.clear_simulated(db, farm.grid_cell_id if farm else None)

    return {
        "policy_id": policy_id,
        "triggers_deleted": triggers_deleted,
        "payouts_deleted": payouts_deleted,
        "simulated_observations_deleted": simulated_deleted,
    }

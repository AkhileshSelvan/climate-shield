"""Risk analysis endpoints — read-only.

These endpoints estimate risk. They never create a policy, an evaluation or a
payout; settlement remains the sole authority of the deterministic trigger and
evaluation engine. There is deliberately no write endpoint in this router.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.core.database import get_db
from app.services.risk.service import (
    RiskAnalysisError,
    analyse_policy_risk,
    analyse_risk,
)

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.post("/analyze", response_model=schemas.RiskAnalysisResponse)
def analyze_risk(payload: schemas.RiskAnalysisRequest, db: Session = Depends(get_db)):
    """Tier-1 burn analysis for a location and trigger definition.

    Replays each historical season over the same calendar window, evaluates the
    same deterministic trigger the policy engine uses, and counts how often it
    would have fired. Reads only cached weather, so it works offline.
    """
    try:
        return analyse_risk(
            db,
            trigger_type=payload.trigger_type,
            threshold_mm=payload.threshold_mm,
            window_days=payload.window_days,
            farm_id=payload.farm_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            season_end=payload.season_end,
            lookback_years=payload.lookback_years,
            min_coverage=payload.min_coverage,
        )
    except RiskAnalysisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/analyze/policy/{policy_id}", response_model=schemas.RiskAnalysisResponse)
def analyze_policy_risk(
    policy_id: int,
    payload: schemas.PolicyRiskAnalysisRequest | None = None,
    db: Session = Depends(get_db),
):
    """Burn analysis using an existing policy's frozen trigger terms.

    Read-only: the policy is not modified and no evaluation is recorded.
    """
    payload = payload or schemas.PolicyRiskAnalysisRequest()
    try:
        return analyse_policy_risk(
            db,
            policy_id=policy_id,
            season_end=payload.season_end,
            lookback_years=payload.lookback_years,
        )
    except RiskAnalysisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/bands")
def risk_bands():
    """The risk classification bands, so clients need not hard-code them."""
    from app.services.risk.classification import RISK_BANDS

    return {
        "score_scale": "0-100 (trigger_frequency x 100)",
        "bands": [
            {"level": label, "min_score": low, "max_score": high, "meaning": meaning}
            for low, high, label, meaning in RISK_BANDS
        ],
    }

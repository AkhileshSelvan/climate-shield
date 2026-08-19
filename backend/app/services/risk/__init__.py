"""Tier-1 burn-analysis risk engine.

Estimates climate-trigger risk by replaying history: for each past season, ask
whether *this* policy's trigger would have fired, then count. Deterministic,
explainable, and requires no training data.

The engine is strictly read-only. It never creates policies, evaluations or
payouts — the deterministic trigger/evaluation engine remains the sole authority
for settlement. Enforced by tests/test_architecture.py.
"""
from app.services.risk.burn_analysis import (
    BURN_ENGINE_VERSION,
    BurnAnalysisResult,
    YearResult,
    analyse,
    build_season_windows,
)
from app.services.risk.classification import (
    RISK_BANDS,
    classify,
    to_risk_score,
)

__all__ = [
    "BURN_ENGINE_VERSION",
    "BurnAnalysisResult",
    "YearResult",
    "analyse",
    "build_season_windows",
    "RISK_BANDS",
    "classify",
    "to_risk_score",
]

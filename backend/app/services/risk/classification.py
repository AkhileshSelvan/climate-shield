"""Risk score and classification.

The transformation from trigger frequency to score is deliberately linear:

    risk_score = trigger_frequency x 100

No curve, no weighting, no tuning constants. A farmer told "8 of the last 35
seasons would have paid out, so your risk score is 22.86" can check the
arithmetic themselves. Any smoothing belongs in a later tier, declared as such.

Band thresholds follow docs/05-ai-ml-design.md and are expressed on the 0-100
score scale.
"""
from __future__ import annotations

# (inclusive lower bound, exclusive upper bound, label, meaning)
RISK_BANDS: tuple[tuple[float, float, str, str], ...] = (
    (0.0, 10.0, "LOW", "Historically reliable rainfall in this window"),
    (10.0, 25.0, "MEDIUM", "Roughly one failure in every 4-10 seasons"),
    (25.0, 40.0, "HIGH", "Roughly one failure in every 3 seasons"),
    (40.0, 100.01, "SEVERE", "Marginal for this crop in this window"),
)

UNKNOWN = "UNKNOWN"
SCORE_DECIMALS = 2
FREQUENCY_DECIMALS = 4


def to_risk_score(trigger_frequency: float) -> float:
    """Frequency in [0,1] to a 0-100 score, rounded to two places.

    Two decimals is the honest limit: the input is a ratio of small integers,
    so more digits would imply precision the sample size cannot support.
    """
    if not 0.0 <= trigger_frequency <= 1.0:
        raise ValueError(f"trigger_frequency must be in [0,1], got {trigger_frequency}")
    return round(trigger_frequency * 100.0, SCORE_DECIMALS)


def classify(risk_score: float | None) -> tuple[str, str]:
    """Score to (level, meaning). None means there was not enough data to judge."""
    if risk_score is None:
        return UNKNOWN, "Not enough historical data to estimate risk"
    for low, high, label, meaning in RISK_BANDS:
        if low <= risk_score < high:
            return label, meaning
    raise ValueError(f"risk_score outside 0-100: {risk_score}")

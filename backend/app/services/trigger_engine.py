"""Deterministic parametric trigger evaluation.

This module is pure arithmetic over values supplied by the caller. It imports
nothing but the standard library — no models, no network, no ML, no LLM. Given
the same inputs it returns the same answer today and in ten years, which is what
makes a payout defensible.

Do not add imports here without reading tests/test_architecture.py first.
"""

ENGINE_VERSION = "trigger-v1.1"


def check_drought_trigger(observed_rainfall_mm: float, threshold_mm: float) -> bool:
    """Drought trigger: breached if observed rainfall is BELOW the threshold."""
    return observed_rainfall_mm < threshold_mm


def check_excess_rain_trigger(observed_rainfall_mm: float, threshold_mm: float) -> bool:
    """Excess rain trigger: breached if observed rainfall is ABOVE the threshold."""
    return observed_rainfall_mm > threshold_mm


def evaluate_trigger(trigger_type: str, observed_rainfall_mm: float, threshold_mm: float) -> bool:
    if trigger_type == "drought":
        return check_drought_trigger(observed_rainfall_mm, threshold_mm)
    elif trigger_type == "excess_rain":
        return check_excess_rain_trigger(observed_rainfall_mm, threshold_mm)
    else:
        raise ValueError(f"Unknown trigger_type: {trigger_type}")

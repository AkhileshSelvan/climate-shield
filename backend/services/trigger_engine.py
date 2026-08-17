def check_drought_trigger(observed_rainfall_mm: float, threshold_mm: float) -> bool:
    """
    Drought trigger: breached if observed rainfall is BELOW the threshold.
    """
    return observed_rainfall_mm < threshold_mm


def check_excess_rain_trigger(observed_rainfall_mm: float, threshold_mm: float) -> bool:
    """
    Excess rain trigger: breached if observed rainfall is ABOVE the threshold.
    """
    return observed_rainfall_mm > threshold_mm


def evaluate_trigger(trigger_type: str, observed_rainfall_mm: float, threshold_mm: float) -> bool:
    if trigger_type == "drought":
        return check_drought_trigger(observed_rainfall_mm, threshold_mm)
    elif trigger_type == "excess_rain":
        return check_excess_rain_trigger(observed_rainfall_mm, threshold_mm)
    else:
        raise ValueError(f"Unknown trigger_type: {trigger_type}")
    
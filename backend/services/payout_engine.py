def calculate_payout(coverage_amount: float, severity_ratio: float = 0.3) -> float:
    """
    Simple prototype payout calculation.
    severity_ratio is a placeholder for how severe the breach was —
    for the hackathon MVP we use a flat ratio of coverage amount.
    """
    payout = round(coverage_amount * severity_ratio, 2)
    return payout

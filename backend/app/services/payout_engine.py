"""Payout calculation. Exact decimal arithmetic, no floats.

Like the trigger engine, this is pure and importable without a database.
"""
from decimal import Decimal

from app.core.types import quantize_money

PAYOUT_ENGINE_VERSION = "payout-v1.1"

# Flat severity ratio for the current MVP. Tiered payouts (25/50/100 by
# severity band) are a planned follow-up and deliberately not in this change.
DEFAULT_SEVERITY_RATIO = Decimal("0.3")


def calculate_payout(coverage_amount, severity_ratio=DEFAULT_SEVERITY_RATIO) -> Decimal:
    """Payout = coverage x severity ratio, rounded half-up to 2 places.

    Accepts Decimal, int or str. Floats are converted via str() so a caller
    passing 0.1 cannot smuggle binary rounding error into a monetary result.
    """
    coverage = coverage_amount if isinstance(coverage_amount, Decimal) else Decimal(str(coverage_amount))
    ratio = severity_ratio if isinstance(severity_ratio, Decimal) else Decimal(str(severity_ratio))
    if coverage < 0:
        raise ValueError("coverage_amount must not be negative")
    if not (Decimal("0") <= ratio <= Decimal("1")):
        raise ValueError("severity_ratio must be between 0 and 1")
    return quantize_money(coverage * ratio)

"""(d) Decimal money calculations."""
from decimal import Decimal

import pytest

from app.core.types import quantize_money
from app.services.payout_engine import calculate_payout


def test_payout_returns_decimal_not_float():
    result = calculate_payout(Decimal("72000.00"))
    assert isinstance(result, Decimal)
    assert result == Decimal("21600.00")


def test_no_binary_float_error():
    """The classic float failure: 0.1 + 0.2 != 0.3. Decimal must not do this."""
    assert calculate_payout(Decimal("0.30"), Decimal("1")) == Decimal("0.30")
    total = quantize_money("0.1") + quantize_money("0.2")
    assert total == Decimal("0.3")
    # Decimal lands on exactly 0.3; binary float overshoots to 0.30000000000000004.
    assert float(Decimal("0.1") + Decimal("0.2")) != 0.1 + 0.2


def test_float_input_does_not_smuggle_error():
    # Decimal(0.1) would be 0.1000000000000000055511151231257827; str() first.
    assert calculate_payout(0.1, Decimal("1")) == Decimal("0.10")


def test_rounding_is_half_up():
    # 12345.67 * 0.3 = 3703.701 -> 3703.70
    assert calculate_payout(Decimal("12345.67")) == Decimal("3703.70")
    # 0.125 rounds up, not to-even
    assert quantize_money(Decimal("0.125")) == Decimal("0.13")


def test_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_payout(Decimal("-1"))
    with pytest.raises(ValueError):
        calculate_payout(Decimal("100"), Decimal("1.5"))


def test_money_survives_database_round_trip(db_session):
    """Value stored and re-read must be identical, not merely close."""
    from app import models

    cell = models.WeatherGridCell(latitude=11.0, longitude=77.0)
    db_session.add(cell)
    db_session.commit()
    farm = models.Farm(
        farmer_name="M", location="Pollachi", latitude=11.0, longitude=77.0,
        crop="maize", area_acres=3.0, grid_cell_id=cell.id,
    )
    db_session.add(farm)
    db_session.commit()

    policy = models.Policy(
        farm_id=farm.id,
        coverage_amount=Decimal("72000.55"),
        premium=Decimal("2169.45"),
        trigger_type="drought", threshold_mm=120.0, window_days=30,
    )
    db_session.add(policy)
    db_session.commit()
    db_session.expire_all()

    reloaded = db_session.query(models.Policy).filter_by(id=policy.id).one()
    assert isinstance(reloaded.coverage_amount, Decimal)
    assert reloaded.coverage_amount == Decimal("72000.55")
    assert reloaded.premium == Decimal("2169.45")
    assert reloaded.coverage_amount + reloaded.premium == Decimal("74170.00")


def test_api_serialises_money_as_string(drought_policy):
    """A JSON float would be re-parsed as a float by every client."""
    assert drought_policy["coverage_amount"] == "72000.00"
    assert isinstance(drought_policy["coverage_amount"], str)

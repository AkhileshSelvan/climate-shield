"""(a) Trigger evaluation."""
import pytest

from app.services.trigger_engine import (
    ENGINE_VERSION,
    check_drought_trigger,
    check_excess_rain_trigger,
    evaluate_trigger,
)


@pytest.mark.parametrize(
    "observed,threshold,expected",
    [(82.4, 120.0, True), (150.0, 120.0, False), (120.0, 120.0, False)],
)
def test_drought(observed, threshold, expected):
    assert check_drought_trigger(observed, threshold) is expected


@pytest.mark.parametrize(
    "observed,threshold,expected",
    [(150.0, 120.0, True), (82.4, 120.0, False), (120.0, 120.0, False)],
)
def test_excess_rain(observed, threshold, expected):
    assert check_excess_rain_trigger(observed, threshold) is expected


def test_boundary_is_not_a_breach():
    """Exactly at the threshold pays nothing, in both directions."""
    assert evaluate_trigger("drought", 120.0, 120.0) is False
    assert evaluate_trigger("excess_rain", 120.0, 120.0) is False


def test_unknown_trigger_type_raises():
    with pytest.raises(ValueError, match="Unknown trigger_type"):
        evaluate_trigger("hailstorm", 10.0, 20.0)


def test_engine_is_deterministic():
    results = {evaluate_trigger("drought", 82.4, 120.0) for _ in range(100)}
    assert results == {True}


def test_engine_version_is_recorded():
    assert ENGINE_VERSION.startswith("trigger-v")

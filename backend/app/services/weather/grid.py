"""Snap farm coordinates to a shared weather grid cell."""
from decimal import ROUND_HALF_EVEN, Decimal

from app.core.config import get_settings

# The precision of the NUMERIC(9, 6) coordinate columns.
COORD_PLACES = Decimal("0.000001")


def _to_decimal(value: float | Decimal) -> Decimal:
    # str() first: Decimal(0.1) would carry the binary float's error in with it.
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _snap_one(value: float | Decimal, resolution: Decimal) -> Decimal:
    # ROUND_HALF_EVEN matches Python's round(), which this replaced.
    cells = (_to_decimal(value) / resolution).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
    return (cells * resolution).quantize(COORD_PLACES)


def snap(
    latitude: float | Decimal,
    longitude: float | Decimal,
    resolution_deg: float | None = None,
) -> tuple[Decimal, Decimal]:
    """Round a coordinate to the nearest grid cell centre.

    Pure arithmetic — no PostGIS, no spatial extension. ~0.1 degrees matches the
    native resolution of the reanalysis data; anything finer would be false
    precision.

    Returns Decimal at the precision the coordinates are stored at, so a snapped
    coordinate compares equal to a stored one. Going through float instead would
    make that equality depend on a binary round-trip, and two farms on the same
    pin could land in different cells.
    """
    if resolution_deg is None:
        resolution_deg = get_settings().grid_resolution_deg
    resolution = _to_decimal(resolution_deg)
    return (_snap_one(latitude, resolution), _snap_one(longitude, resolution))

"""Snap farm coordinates to a shared weather grid cell."""
from app.core.config import get_settings


def snap(latitude: float, longitude: float, resolution_deg: float | None = None) -> tuple[float, float]:
    """Round a coordinate to the nearest grid cell centre.

    Pure arithmetic — no PostGIS, no spatial extension. ~0.1 degrees matches the
    native resolution of the reanalysis data; anything finer would be false
    precision.
    """
    if resolution_deg is None:
        resolution_deg = get_settings().grid_resolution_deg
    return (
        round(round(latitude / resolution_deg) * resolution_deg, 6),
        round(round(longitude / resolution_deg) * resolution_deg, 6),
    )

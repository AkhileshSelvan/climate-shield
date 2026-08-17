"""Database orchestration for the burn-analysis engine.

Loads cached observations, hands them to the pure engine, and shapes the result
for the API. Read-only by construction: this module never constructs a Trigger
or a Payout, and never imports the evaluation or payout services.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app import models
from app.services import trigger_engine
from app.services.risk import burn_analysis as burn
from app.services.risk.classification import classify
from app.services.weather import cache, grid

DEFAULT_LOOKBACK_YEARS = 35


class RiskAnalysisError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _resolve_cell(
    db: Session,
    farm_id: int | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> tuple[models.WeatherGridCell, models.Farm | None]:
    if farm_id is not None:
        farm = db.query(models.Farm).filter(models.Farm.id == farm_id).first()
        if farm is None:
            raise RiskAnalysisError("Farm not found", status_code=404)
        if farm.grid_cell_id is None:
            raise RiskAnalysisError("Farm has no weather grid cell assigned", status_code=400)
        cell = (
            db.query(models.WeatherGridCell)
            .filter(models.WeatherGridCell.id == farm.grid_cell_id)
            .first()
        )
        return cell, farm

    if latitude is None or longitude is None:
        raise RiskAnalysisError("Provide either farm_id or latitude+longitude", status_code=400)

    lat, lon = grid.snap(latitude, longitude)
    cell = (
        db.query(models.WeatherGridCell)
        .filter(models.WeatherGridCell.latitude == lat)
        .filter(models.WeatherGridCell.longitude == lon)
        .first()
    )
    if cell is None:
        raise RiskAnalysisError(
            f"No weather grid cell at ({lat:.1f}, {lon:.1f}). Ingest weather first.",
            status_code=409,
        )
    return cell, None


def _load_windows(db: Session, cell_id: int, windows: list[burn.SeasonWindow]):
    """Pair each season window with its cached observations.

    Reads the cache only — no provider is consulted, so this runs offline.
    """
    paired = []
    for window in windows:
        rows = cache.read_window(db, cell_id, window.start, window.end)
        paired.append(
            (
                window,
                [
                    {
                        "precipitation_mm": r.precipitation_mm,
                        "source": r.source,
                        "is_simulated": r.is_simulated,
                    }
                    for r in rows
                ],
            )
        )
    return paired


def _build_factors(result: burn.BurnAnalysisResult, level: str, meaning: str) -> list[dict]:
    """Plain-language drivers, computed from the numbers — never generated."""
    factors: list[dict] = []

    if result.data_quality == burn.DATA_QUALITY_INSUFFICIENT:
        factors.append(
            {
                "factor": "insufficient_history",
                "detail": (
                    f"No season in the {result.historical_years}-year period had enough "
                    f"observations to evaluate. No risk score was produced."
                ),
                "direction": "blocks_estimate",
            }
        )
        return factors

    triggered = result.triggered_year_labels
    factors.append(
        {
            "factor": "historical_trigger_frequency",
            "detail": (
                f"{result.triggered_years} of {result.eligible_years} eligible seasons "
                f"would have triggered ({result.risk_score:.2f}%)."
                + (f" Triggered years: {', '.join(str(y) for y in triggered)}." if triggered else "")
            ),
            "direction": "increases_risk" if result.triggered_years else "decreases_risk",
        }
    )
    factors.append(
        {
            "factor": "risk_band",
            "detail": f"{level} — {meaning}.",
            "direction": "informational",
        }
    )

    ineligible = result.historical_years - result.eligible_years
    if ineligible:
        factors.append(
            {
                "factor": "excluded_seasons",
                "detail": (
                    f"{ineligible} of {result.historical_years} seasons were excluded for "
                    f"incomplete records. Missing days are never counted as zero rainfall."
                ),
                "direction": "reduces_confidence",
            }
        )

    if result.data_quality == burn.DATA_QUALITY_LIMITED:
        factors.append(
            {
                "factor": "limited_sample",
                "detail": (
                    f"Only {result.eligible_years} eligible seasons. Treat the score as "
                    f"indicative; a tail risk can be missed entirely at this sample size."
                ),
                "direction": "reduces_confidence",
            }
        )

    if result.is_simulated:
        factors.append(
            {
                "factor": "simulated_observations",
                "detail": "Some observations are demo-simulated, not measured weather.",
                "direction": "reduces_confidence",
            }
        )

    if any(s in ("fixture", "simulated") for s in result.data_source):
        factors.append(
            {
                "factor": "fixture_data",
                "detail": (
                    "Weather came from committed offline fixtures. The bundled fixtures are "
                    "synthetic, generated from published regional normals — not measurements. "
                    "Run `make fixtures-live` for real ERA5 data."
                ),
                "direction": "data_provenance",
            }
        )
    return factors


def _confidence(result: burn.BurnAnalysisResult) -> str:
    if result.data_quality == burn.DATA_QUALITY_INSUFFICIENT:
        return "none"
    if result.eligible_years >= 25:
        return "high"
    if result.eligible_years >= burn.DEFAULT_MIN_ELIGIBLE_YEARS:
        return "medium"
    return "low"


def analyse_risk(
    db: Session,
    trigger_type: str,
    threshold_mm: float,
    window_days: int,
    farm_id: int | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    season_end: date | None = None,
    lookback_years: int = DEFAULT_LOOKBACK_YEARS,
    min_coverage: float = burn.DEFAULT_MIN_COVERAGE,
    policy_id: int | None = None,
) -> dict:
    """Run burn analysis for a location. Read-only; creates nothing."""
    if lookback_years < 1:
        raise RiskAnalysisError("lookback_years must be at least 1", status_code=400)

    cell, farm = _resolve_cell(db, farm_id, latitude, longitude)

    # The caller may pin the season anchor for a reproducible result; otherwise
    # today is used. The pure engine never reads the clock itself.
    anchor = season_end or date.today()
    end_year = anchor.year
    start_year = end_year - lookback_years + 1

    windows = burn.build_season_windows(anchor, window_days, start_year, end_year)
    paired = _load_windows(db, cell.id, windows)

    try:
        result = burn.analyse(paired, trigger_type, threshold_mm, min_coverage=min_coverage)
    except ValueError as exc:
        raise RiskAnalysisError(str(exc), status_code=400) from exc

    level, meaning = classify(result.risk_score)

    return {
        "risk_score": result.risk_score,
        "risk_level": level,
        "risk_level_meaning": meaning,
        "trigger_frequency": result.trigger_frequency,
        "historical_years": result.historical_years,
        "eligible_years": result.eligible_years,
        "triggered_years": result.triggered_years,
        "triggered_year_labels": list(result.triggered_year_labels),
        "total_observations_used": result.total_observations_used,
        "trigger_definition": {
            "trigger_type": result.trigger_type,
            "threshold_mm": result.threshold_mm,
            "window_days": window_days,
            "season_end": anchor.isoformat(),
            "semantics": f"evaluated by {trigger_engine.ENGINE_VERSION} evaluate_trigger",
        },
        "data_source": list(result.data_source),
        "is_simulated": result.is_simulated,
        "data_quality": result.data_quality,
        "confidence": _confidence(result),
        "engine_version": result.engine_version,
        "context": {
            "grid_cell_id": cell.id,
            "latitude": float(cell.latitude),
            "longitude": float(cell.longitude),
            "farm_id": farm.id if farm else None,
            "crop": farm.crop if farm else None,
            "location": farm.location if farm else None,
            "policy_id": policy_id,
            "period_start_year": start_year,
            "period_end_year": end_year,
            "min_coverage": min_coverage,
        },
        "factors": _build_factors(result, level, meaning),
        "years": [y.as_dict() for y in result.years],
    }


def analyse_policy_risk(
    db: Session, policy_id: int, season_end: date | None = None, lookback_years: int = DEFAULT_LOOKBACK_YEARS
) -> dict:
    """Analyse using a policy's frozen trigger terms. Does not modify the policy."""
    policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()
    if policy is None:
        raise RiskAnalysisError("Policy not found", status_code=404)
    return analyse_risk(
        db,
        trigger_type=policy.trigger_type,
        threshold_mm=policy.threshold_mm,
        window_days=policy.window_days,
        farm_id=policy.farm_id,
        season_end=season_end,
        lookback_years=lookback_years,
        policy_id=policy.id,
    )

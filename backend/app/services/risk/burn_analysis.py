"""Tier-1 burn analysis: replay history, count the payouts.

Pure computation. Imports the standard library and the deterministic trigger
engine — nothing else. No database, no network, no models, no ML. The caller
supplies the observations; this module decides nothing about money.

Reusing `trigger_engine.evaluate_trigger` is deliberate and load-bearing: the
risk estimate and the actual settlement must agree on what "drought" means, so
there is exactly one definition and this module calls it rather than restating
it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from app.services import trigger_engine

BURN_ENGINE_VERSION = "burn-analysis-v1.0"

# A season is eligible only if this fraction of its days is present in the
# record. Below it, the year is excluded and reported, never silently treated
# as zero rainfall — a gap read as zero manufactures a drought that never
# happened.
DEFAULT_MIN_COVERAGE = 0.8

# Fewer eligible seasons than this and the result is reported as limited.
DEFAULT_MIN_ELIGIBLE_YEARS = 10

# Below this, no score is produced at all.
ABSOLUTE_MIN_ELIGIBLE_YEARS = 1

DATA_QUALITY_SUFFICIENT = "sufficient"
DATA_QUALITY_LIMITED = "limited"
DATA_QUALITY_INSUFFICIENT = "insufficient"


@dataclass(frozen=True)
class SeasonWindow:
    """One historical season, aligned to the same calendar window each year."""

    year: int
    start: date
    end: date

    @property
    def expected_days(self) -> int:
        return (self.end - self.start).days + 1


@dataclass(frozen=True)
class YearResult:
    """What happened in one historical season, and whether it would have paid."""

    year: int
    window_start: date
    window_end: date
    observed_mm: float | None
    triggered: bool | None
    eligible: bool
    observations_used: int
    expected_days: int
    coverage: float
    sources: tuple[str, ...] = ()
    is_simulated: bool = False
    ineligible_reason: str | None = None

    def as_dict(self) -> dict:
        return {
            "year": self.year,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "observed_mm": self.observed_mm,
            "triggered": self.triggered,
            "eligible": self.eligible,
            "observations_used": self.observations_used,
            "expected_days": self.expected_days,
            "coverage": self.coverage,
            "sources": list(self.sources),
            "is_simulated": self.is_simulated,
            "ineligible_reason": self.ineligible_reason,
        }


@dataclass(frozen=True)
class BurnAnalysisResult:
    engine_version: str
    trigger_type: str
    threshold_mm: float
    window_days: int
    historical_years: int
    eligible_years: int
    triggered_years: int
    trigger_frequency: float | None
    risk_score: float | None
    total_observations_used: int
    data_quality: str
    data_source: tuple[str, ...]
    is_simulated: bool
    years: tuple[YearResult, ...] = field(default_factory=tuple)

    @property
    def triggered_year_labels(self) -> tuple[int, ...]:
        return tuple(y.year for y in self.years if y.triggered)


def build_season_windows(
    anchor: date, window_days: int, start_year: int, end_year: int
) -> list[SeasonWindow]:
    """One window per year, all ending on the same month/day as `anchor`.

    Aligning every historical season to the same calendar position is what makes
    the years comparable — otherwise a monsoon window in one year would be
    compared against a dry-season window in another.

    The window spans `window_days + 1` dates, matching the evaluation engine's
    `start = end - timedelta(days=window_days)` with both ends inclusive.
    """
    if window_days <= 0:
        raise ValueError(f"window_days must be positive, got {window_days}")
    if end_year < start_year:
        raise ValueError(f"end_year {end_year} precedes start_year {start_year}")

    windows: list[SeasonWindow] = []
    for year in range(start_year, end_year + 1):
        try:
            end = anchor.replace(year=year)
        except ValueError:
            # 29 February in a non-leap year: fall back to the 28th rather than
            # dropping the season.
            end = anchor.replace(year=year, day=28)
        windows.append(SeasonWindow(year=year, start=end - timedelta(days=window_days), end=end))
    return windows


def _summarise_observations(observations) -> tuple[float, int, tuple[str, ...], bool]:
    total = 0.0
    count = 0
    sources: set[str] = set()
    simulated = False
    for obs in observations:
        total += float(obs["precipitation_mm"])
        count += 1
        if obs.get("source"):
            sources.add(obs["source"])
        if obs.get("is_simulated"):
            simulated = True
    return round(total, 2), count, tuple(sorted(sources)), simulated


def analyse(
    windows_with_observations: list[tuple[SeasonWindow, list[dict]]],
    trigger_type: str,
    threshold_mm: float,
    min_coverage: float = DEFAULT_MIN_COVERAGE,
    min_eligible_years: int = DEFAULT_MIN_ELIGIBLE_YEARS,
) -> BurnAnalysisResult:
    """Replay each season and count how often the trigger would have fired.

    `windows_with_observations` pairs each season window with its observations,
    each a dict of {precipitation_mm, source, is_simulated}. Supplying the data
    rather than fetching it keeps this function pure and trivially testable.
    """
    if not 0.0 < min_coverage <= 1.0:
        raise ValueError(f"min_coverage must be in (0,1], got {min_coverage}")
    # Fail fast on an unknown trigger type rather than after the loop.
    trigger_engine.evaluate_trigger(trigger_type, 0.0, threshold_mm)

    years: list[YearResult] = []
    all_sources: set[str] = set()
    any_simulated = False
    total_observations = 0

    for window, observations in windows_with_observations:
        total_mm, used, sources, simulated = _summarise_observations(observations)
        expected = window.expected_days
        coverage = round(used / expected, 4) if expected else 0.0
        all_sources.update(sources)
        any_simulated = any_simulated or simulated

        if used == 0:
            years.append(
                YearResult(
                    year=window.year, window_start=window.start, window_end=window.end,
                    observed_mm=None, triggered=None, eligible=False,
                    observations_used=0, expected_days=expected, coverage=0.0,
                    ineligible_reason="no observations for this window",
                )
            )
            continue

        if coverage < min_coverage:
            years.append(
                YearResult(
                    year=window.year, window_start=window.start, window_end=window.end,
                    observed_mm=None, triggered=None, eligible=False,
                    observations_used=used, expected_days=expected, coverage=coverage,
                    sources=sources, is_simulated=simulated,
                    ineligible_reason=(
                        f"incomplete record: {used}/{expected} days "
                        f"({coverage:.0%} < {min_coverage:.0%} required)"
                    ),
                )
            )
            continue

        # The one call that matters: the same function that settles policies.
        triggered = trigger_engine.evaluate_trigger(trigger_type, total_mm, threshold_mm)
        total_observations += used
        years.append(
            YearResult(
                year=window.year, window_start=window.start, window_end=window.end,
                observed_mm=total_mm, triggered=triggered, eligible=True,
                observations_used=used, expected_days=expected, coverage=coverage,
                sources=sources, is_simulated=simulated,
            )
        )

    eligible = [y for y in years if y.eligible]
    eligible_count = len(eligible)
    triggered_count = sum(1 for y in eligible if y.triggered)

    if eligible_count < ABSOLUTE_MIN_ELIGIBLE_YEARS:
        frequency: float | None = None
        risk_score: float | None = None
        data_quality = DATA_QUALITY_INSUFFICIENT
    else:
        from app.services.risk.classification import FREQUENCY_DECIMALS, to_risk_score

        frequency = round(triggered_count / eligible_count, FREQUENCY_DECIMALS)
        risk_score = to_risk_score(frequency)
        data_quality = (
            DATA_QUALITY_SUFFICIENT
            if eligible_count >= min_eligible_years
            else DATA_QUALITY_LIMITED
        )

    return BurnAnalysisResult(
        engine_version=BURN_ENGINE_VERSION,
        trigger_type=trigger_type,
        threshold_mm=threshold_mm,
        window_days=(windows_with_observations[0][0].expected_days - 1)
        if windows_with_observations
        else 0,
        historical_years=len(years),
        eligible_years=eligible_count,
        triggered_years=triggered_count,
        trigger_frequency=frequency,
        risk_score=risk_score,
        total_observations_used=total_observations,
        data_quality=data_quality,
        data_source=tuple(sorted(all_sources)),
        is_simulated=any_simulated,
        years=tuple(years),
    )

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class FarmCreate(BaseModel):
    farmer_name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    crop: str
    area_acres: float
    crop_stage: Optional[str] = None


class FarmResponse(FarmCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    grid_cell_id: Optional[int] = None


class PolicyCreate(BaseModel):
    farm_id: int
    # Decimal in, Decimal out. Money never becomes a float on this boundary.
    coverage_amount: Decimal = Field(ge=0, decimal_places=2)
    premium: Decimal = Field(ge=0, decimal_places=2)
    trigger_type: str
    threshold_mm: float
    window_days: int = Field(gt=0)


class PolicyResponse(PolicyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str

    @field_serializer("coverage_amount", "premium")
    def _money(self, value: Decimal) -> str:
        # Serialised as a string so no JSON consumer can silently parse it
        # back into a float.
        return f"{value:.2f}"



class WeatherIngestRequest(BaseModel):
    farm_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    days: int = Field(default=14, gt=0, le=400)
    end_date: Optional[date] = None
    # None means "use the configured default provider" (fixture).
    provider: Optional[str] = None


# ---------------------------------------------------------------------------
# Risk analysis (Tier-1 burn analysis) — read-only. These schemas describe an
# estimate; nothing here creates a policy, evaluation or payout.
# ---------------------------------------------------------------------------


class RiskAnalysisRequest(BaseModel):
    """Either farm_id, or latitude+longitude, must be supplied."""

    farm_id: Optional[int] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)

    trigger_type: str = Field(description="drought | excess_rain")
    threshold_mm: float = Field(ge=0)
    window_days: int = Field(gt=0, le=366)

    # Pin the season anchor for a reproducible result; defaults to today.
    season_end: Optional[date] = None
    lookback_years: int = Field(default=35, ge=1, le=100)
    min_coverage: float = Field(
        default=0.8, gt=0, le=1,
        description="Fraction of a window's days that must be present for the season to count",
    )


class PolicyRiskAnalysisRequest(BaseModel):
    """Analyse using a policy's frozen trigger terms. The policy is not modified."""

    season_end: Optional[date] = None
    lookback_years: int = Field(default=35, ge=1, le=100)


class RiskYear(BaseModel):
    year: int
    window_start: date
    window_end: date
    observed_mm: Optional[float]
    triggered: Optional[bool]
    eligible: bool
    observations_used: int
    expected_days: int
    coverage: float
    sources: list[str] = []
    is_simulated: bool = False
    ineligible_reason: Optional[str] = None


class RiskFactor(BaseModel):
    factor: str
    detail: str
    direction: str


class RiskAnalysisResponse(BaseModel):
    risk_score: Optional[float] = Field(description="0-100, or null when data is insufficient")
    risk_level: str = Field(description="LOW | MEDIUM | HIGH | SEVERE | UNKNOWN")
    risk_level_meaning: str
    trigger_frequency: Optional[float] = Field(description="triggered_years / eligible_years")

    historical_years: int
    eligible_years: int
    triggered_years: int
    triggered_year_labels: list[int] = []
    total_observations_used: int

    trigger_definition: dict
    data_source: list[str]
    is_simulated: bool
    data_quality: str = Field(description="sufficient | limited | insufficient")
    confidence: str

    engine_version: str
    context: dict
    factors: list[RiskFactor]
    years: list[RiskYear]

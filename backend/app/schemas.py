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

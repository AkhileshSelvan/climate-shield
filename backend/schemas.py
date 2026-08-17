from pydantic import BaseModel
from typing import Optional


class FarmCreate(BaseModel):
    farmer_name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    crop: str
    area_acres: float
    crop_stage: Optional[str] = None


class FarmResponse(FarmCreate):
    id: int

    class Config:
        from_attributes = True


class PolicyCreate(BaseModel):
    farm_id: int
    coverage_amount: float
    premium: float
    trigger_type: str
    threshold_mm: float
    window_days: int


class PolicyResponse(PolicyCreate):
    id: int
    status: str

    class Config:
        from_attributes = True
        
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.types import Money


class WeatherGridCell(Base):
    """A ~0.1 degree cell. Farms snap to a cell; weather is stored per cell, so
    a thousand farms in one block share one row per day instead of a thousand."""

    __tablename__ = "weather_grid_cells"
    __table_args__ = (UniqueConstraint("latitude", "longitude", name="uq_grid_cell_latlon"),)

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    label = Column(String, nullable=True)

    farms = relationship("Farm", back_populates="grid_cell")
    observations = relationship("WeatherObservation", back_populates="grid_cell")


class WeatherObservation(Base):
    """Cached daily weather. Every read path serves from this table; providers
    only ever write to it. This is what makes evaluation reproducible offline."""

    __tablename__ = "weather_observations"
    __table_args__ = (
        UniqueConstraint(
            "grid_cell_id", "obs_date", "source", name="uq_observation_cell_date_source"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    grid_cell_id = Column(Integer, ForeignKey("weather_grid_cells.id"), nullable=False, index=True)
    obs_date = Column(Date, nullable=False, index=True)
    source = Column(String, nullable=False)
    precipitation_mm = Column(Float, nullable=False)
    is_simulated = Column(Boolean, nullable=False, default=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    grid_cell = relationship("WeatherGridCell", back_populates="observations")


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    farmer_name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    crop = Column(String, nullable=False)
    area_acres = Column(Float, nullable=False)
    crop_stage = Column(String, nullable=True)
    grid_cell_id = Column(Integer, ForeignKey("weather_grid_cells.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    policies = relationship("Policy", back_populates="farm")
    grid_cell = relationship("WeatherGridCell", back_populates="farms")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    coverage_amount = Column(Money, nullable=False)
    premium = Column(Money, nullable=False)
    # Trigger terms are stored on the policy itself, not referenced from a
    # mutable product template, so an issued contract cannot be rewritten.
    trigger_type = Column(String, nullable=False)
    threshold_mm = Column(Float, nullable=False)
    window_days = Column(Integer, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farm = relationship("Farm", back_populates="policies")
    triggers = relationship("Trigger", back_populates="policy")


class Trigger(Base):
    """One evaluation of one policy on one date.

    The unique constraint is what makes evaluation idempotent: re-running the
    same evaluation cannot create a second row, and therefore cannot create a
    second payout."""

    __tablename__ = "triggers"
    __table_args__ = (
        UniqueConstraint("policy_id", "evaluation_date", name="uq_trigger_policy_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False, index=True)
    evaluation_date = Column(Date, nullable=False, index=True)
    observed_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    triggered = Column(Integer, nullable=False)
    window_start = Column(Date, nullable=True)
    window_end = Column(Date, nullable=True)
    observations_used = Column(Integer, nullable=False, default=0)
    data_source = Column(String, nullable=True)
    is_simulated = Column(Boolean, nullable=False, default=False)
    engine_version = Column(String, nullable=True)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

    policy = relationship("Policy", back_populates="triggers")
    payout = relationship("Payout", back_populates="trigger", uselist=False)


class Payout(Base):
    __tablename__ = "payouts"
    __table_args__ = (UniqueConstraint("trigger_id", name="uq_payout_trigger"),)

    id = Column(Integer, primary_key=True, index=True)
    trigger_id = Column(Integer, ForeignKey("triggers.id"), nullable=False)
    amount = Column(Money, nullable=False)
    status = Column(String, default="initiated")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trigger = relationship("Trigger", back_populates="payout")

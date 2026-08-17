from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    policies = relationship("Policy", back_populates="farm")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    coverage_amount = Column(Float, nullable=False)
    premium = Column(Float, nullable=False)
    trigger_type = Column(String, nullable=False)
    threshold_mm = Column(Float, nullable=False)
    window_days = Column(Integer, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farm = relationship("Farm", back_populates="policies")
    triggers = relationship("Trigger", back_populates="policy")


class Trigger(Base):
    __tablename__ = "triggers"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    observed_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    triggered = Column(Integer, nullable=False)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

    policy = relationship("Policy", back_populates="triggers")
    payout = relationship("Payout", back_populates="trigger", uselist=False)


class Payout(Base):
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True, index=True)
    trigger_id = Column(Integer, ForeignKey("triggers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="initiated")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trigger = relationship("Trigger", back_populates="payout")
    
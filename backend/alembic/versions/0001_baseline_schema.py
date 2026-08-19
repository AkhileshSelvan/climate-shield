"""Baseline schema: weather cache, idempotent evaluations, decimal money.

Supersedes the create_all() schema from the first backend. It adds the weather
grid/observation cache, the (policy_id, evaluation_date) uniqueness that makes
evaluation idempotent, the payout-per-trigger uniqueness that prevents duplicate
payments, and NUMERIC(14,2) money columns.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-08-17
"""
import sqlalchemy as sa
from alembic import op

from app.core.types import Money

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weather_grid_cells",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.UniqueConstraint("latitude", "longitude", name="uq_grid_cell_latlon"),
    )
    op.create_index("ix_weather_grid_cells_id", "weather_grid_cells", ["id"])

    op.create_table(
        "weather_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("grid_cell_id", sa.Integer(), sa.ForeignKey("weather_grid_cells.id"), nullable=False),
        sa.Column("obs_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("precipitation_mm", sa.Float(), nullable=False),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("grid_cell_id", "obs_date", "source", name="uq_observation_cell_date_source"),
    )
    op.create_index("ix_weather_observations_grid_cell_id", "weather_observations", ["grid_cell_id"])
    op.create_index("ix_weather_observations_obs_date", "weather_observations", ["obs_date"])

    op.create_table(
        "farms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("farmer_name", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("crop", sa.String(), nullable=False),
        sa.Column("area_acres", sa.Float(), nullable=False),
        sa.Column("crop_stage", sa.String(), nullable=True),
        sa.Column("grid_cell_id", sa.Integer(), sa.ForeignKey("weather_grid_cells.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_farms_id", "farms", ["id"])
    op.create_index("ix_farms_grid_cell_id", "farms", ["grid_cell_id"])

    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("farm_id", sa.Integer(), sa.ForeignKey("farms.id"), nullable=False),
        sa.Column("coverage_amount", Money(), nullable=False),
        sa.Column("premium", Money(), nullable=False),
        sa.Column("trigger_type", sa.String(), nullable=False),
        sa.Column("threshold_mm", sa.Float(), nullable=False),
        sa.Column("window_days", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_policies_id", "policies", ["id"])

    op.create_table(
        "triggers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("policy_id", sa.Integer(), sa.ForeignKey("policies.id"), nullable=False),
        sa.Column("evaluation_date", sa.Date(), nullable=False),
        sa.Column("observed_value", sa.Float(), nullable=False),
        sa.Column("threshold_value", sa.Float(), nullable=False),
        sa.Column("triggered", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.Date(), nullable=True),
        sa.Column("window_end", sa.Date(), nullable=True),
        sa.Column("observations_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("data_source", sa.String(), nullable=True),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("engine_version", sa.String(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        # The idempotency guarantee.
        sa.UniqueConstraint("policy_id", "evaluation_date", name="uq_trigger_policy_date"),
    )
    op.create_index("ix_triggers_id", "triggers", ["id"])
    op.create_index("ix_triggers_policy_id", "triggers", ["policy_id"])
    op.create_index("ix_triggers_evaluation_date", "triggers", ["evaluation_date"])

    op.create_table(
        "payouts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trigger_id", sa.Integer(), sa.ForeignKey("triggers.id"), nullable=False),
        sa.Column("amount", Money(), nullable=False),
        sa.Column("status", sa.String(), server_default="initiated"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        # At most one payout per evaluation: the duplicate-payment guard.
        sa.UniqueConstraint("trigger_id", name="uq_payout_trigger"),
    )
    op.create_index("ix_payouts_id", "payouts", ["id"])


def downgrade() -> None:
    op.drop_table("payouts")
    op.drop_table("triggers")
    op.drop_table("policies")
    op.drop_table("farms")
    op.drop_table("weather_observations")
    op.drop_table("weather_grid_cells")

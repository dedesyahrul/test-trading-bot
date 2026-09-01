"""Add timestamped OHLCV candles for chart intelligence.

Revision ID: 008_candles
Revises: 007_position_risk_telemetry
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "008_candles"
down_revision = "007_position_risk_telemetry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candles",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("pair_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timeframe", sa.String(10), server_default="minute", nullable=False),
        sa.Column("open", sa.Numeric(20, 8), nullable=False),
        sa.Column("high", sa.Numeric(20, 8), nullable=False),
        sa.Column("low", sa.Numeric(20, 8), nullable=False),
        sa.Column("close", sa.Numeric(20, 8), nullable=False),
        sa.Column("volume", sa.Numeric(20, 2)),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pair_id"], ["pairs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pair_id", "timeframe", "timestamp", name="uq_candle_pair_timeframe_timestamp"),
    )
    op.create_index("idx_candles_pair_timestamp", "candles", ["pair_id", "timestamp"])


def downgrade() -> None:
    op.drop_index("idx_candles_pair_timestamp", table_name="candles")
    op.drop_table("candles")

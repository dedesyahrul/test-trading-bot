"""Add strategies table and risk_config to bot_state

Revision ID: 002_strategies
Revises: 001_initial
Create Date: 2026-08-30 02:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_strategies"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategies",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("strategy_key", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("strategy_type", sa.String(50), nullable=False),
        sa.Column("parameters", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_key"),
    )
    op.create_index("idx_strategies_key", "strategies", ["strategy_key"])

    op.add_column(
        "bot_state",
        sa.Column("risk_config", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )

    strategies_table = sa.table(
        "strategies",
        sa.column("strategy_key", sa.String),
        sa.column("name", sa.String),
        sa.column("strategy_type", sa.String),
        sa.column("parameters", postgresql.JSON),
        sa.column("is_active", sa.Boolean),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(
        strategies_table,
        [
            {
                "strategy_key": "momentum_v1",
                "name": "Momentum Strategy",
                "strategy_type": "momentum",
                "parameters": {
                    "min_volume_24h": 50000,
                    "min_price_change_5m": 0.05,
                    "min_volume_spike": 2.0,
                    "min_buy_sell_ratio": 1.2,
                    "max_risk_score": 50,
                    "take_profit_pct": 0.20,
                    "stop_loss_pct": 0.10,
                },
                "is_active": True,
                "description": "Pure breakout detection",
            },
            {
                "strategy_key": "ml_sniper_v1",
                "name": "ML-Assisted Sniper",
                "strategy_type": "ml_assisted",
                "parameters": {
                    "min_volume_24h": 50000,
                    "max_risk_score": 40,
                    "take_profit_pct": 0.15,
                    "stop_loss_pct": 0.10,
                },
                "is_active": True,
                "description": "ML-ready placeholder for future integration",
            },
        ],
    )

    op.execute(
        """UPDATE bot_state SET risk_config = '{"max_position_size_usd": 1000, "max_daily_loss_usd": 500, "max_positions": 5, "min_liquidity_usd": 5000, "max_risk_score": 50}'::jsonb WHERE risk_config IS NULL"""
    )


def downgrade() -> None:
    op.drop_column("bot_state", "risk_config")
    op.drop_index("idx_strategies_key", table_name="strategies")
    op.drop_table("strategies")

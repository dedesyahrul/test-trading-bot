"""Add P0 circuit breaker and trade decision ledger.

Revision ID: 004_p0_risk_audit
Revises: 003_volatility_risk
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_p0_risk_audit"
down_revision = "003_volatility_risk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bot_state", sa.Column("circuit_state", sa.String(20), server_default="RUNNING"))
    op.add_column("bot_state", sa.Column("consecutive_failures", sa.Integer(), server_default="0"))
    op.add_column("bot_state", sa.Column("daily_loss_usd", sa.Numeric(20, 2), server_default="0"))
    op.add_column("bot_state", sa.Column("last_failure_at", sa.DateTime(), nullable=True))
    op.create_table(
        "trade_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("pair_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("strategy_id", sa.String(50), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("signal_type", sa.String(20), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("position_size_usd", sa.Numeric(20, 8), nullable=True),
        sa.Column("data_quality", sa.String(20), nullable=True),
        sa.Column("features", postgresql.JSON(astext_type=sa.Text()), server_default="{}", nullable=True),
        sa.Column("reasons", postgresql.JSON(astext_type=sa.Text()), server_default="[]", nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["pair_id"], ["pairs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_trade_decisions_pair_id", "trade_decisions", ["pair_id"])
    op.create_index("idx_trade_decisions_created_at", "trade_decisions", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_trade_decisions_created_at", table_name="trade_decisions")
    op.drop_index("idx_trade_decisions_pair_id", table_name="trade_decisions")
    op.drop_table("trade_decisions")
    op.drop_column("bot_state", "last_failure_at")
    op.drop_column("bot_state", "daily_loss_usd")
    op.drop_column("bot_state", "consecutive_failures")
    op.drop_column("bot_state", "circuit_state")

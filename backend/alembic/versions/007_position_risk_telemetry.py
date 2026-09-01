"""Add position/trade correlation and exit telemetry.

Revision ID: 007_position_risk_telemetry
Revises: 006_decision_score
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007_position_risk_telemetry"
down_revision = "006_decision_score"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table, name, column in [
        ("positions", "decision_id", postgresql.UUID(as_uuid=True)),
        ("positions", "exit_reason", sa.String(40)),
        ("positions", "mae_usd", sa.Numeric(20, 2)),
        ("positions", "mfe_usd", sa.Numeric(20, 2)),
        ("positions", "thesis_invalidated", sa.Boolean()),
        ("trades", "decision_id", postgresql.UUID(as_uuid=True)),
    ]:
        op.add_column(table, sa.Column(name, column, nullable=True))
    op.create_index("idx_positions_decision_id", "positions", ["decision_id"])
    op.create_index("idx_trades_decision_id", "trades", ["decision_id"])


def downgrade() -> None:
    op.drop_index("idx_trades_decision_id", table_name="trades")
    op.drop_index("idx_positions_decision_id", table_name="positions")
    for table, name in [("trades", "decision_id"), ("positions", "thesis_invalidated"), ("positions", "mfe_usd"), ("positions", "mae_usd"), ("positions", "exit_reason"), ("positions", "decision_id")]:
        op.drop_column(table, name)

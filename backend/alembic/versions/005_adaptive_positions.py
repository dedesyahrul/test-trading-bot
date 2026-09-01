"""Add adaptive position and exit state.

Revision ID: 005_adaptive_positions
Revises: 004_p0_risk_audit
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005_adaptive_positions"
down_revision = "004_p0_risk_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name, column in [
        ("initial_stop_loss", sa.Numeric(20, 8)),
        ("highest_price", sa.Numeric(20, 8)),
        ("profit_lock_price", sa.Numeric(20, 8)),
        ("exit_pressure", sa.Numeric(5, 2)),
        ("partial_exit_count", sa.Integer()),
        ("entry_decision_score", sa.Numeric(5, 2)),
        ("entry_thesis", postgresql.JSON(astext_type=sa.Text())),
    ]:
        op.add_column("positions", sa.Column(name, column, nullable=True))
    op.execute("UPDATE positions SET current_amount = entry_amount WHERE current_amount IS NULL")


def downgrade() -> None:
    for name in ("entry_thesis", "entry_decision_score", "partial_exit_count", "exit_pressure", "profit_lock_price", "highest_price", "initial_stop_loss"):
        op.drop_column("positions", name)

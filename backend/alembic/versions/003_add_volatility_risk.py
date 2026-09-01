"""Add volatility risk score used by the risk engine.

Revision ID: 003_volatility_risk
Revises: 002_strategies
"""
from alembic import op
import sqlalchemy as sa


revision = "003_volatility_risk"
down_revision = "002_strategies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "risk_assessments",
        sa.Column("volatility_risk", sa.Numeric(precision=5, scale=2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("risk_assessments", "volatility_risk")

"""Add decision score to the trade decision ledger.

Revision ID: 006_decision_score
Revises: 005_adaptive_positions
"""
from alembic import op
import sqlalchemy as sa

revision = "006_decision_score"
down_revision = "005_adaptive_positions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The column may already exist in databases upgraded during the P0 rollout.
    op.execute("ALTER TABLE trade_decisions ADD COLUMN IF NOT EXISTS decision_score NUMERIC(5, 2)")


def downgrade() -> None:
    op.execute("ALTER TABLE trade_decisions DROP COLUMN IF EXISTS decision_score")

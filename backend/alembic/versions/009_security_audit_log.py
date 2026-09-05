"""Add security gate audit log.

Revision ID: 009_security_audit_log
Revises: 008_candles
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "009_security_audit_log"
down_revision = "008_candles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "security_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("pair_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("block_reason", sa.String(255), nullable=True),
        sa.Column("block_details", sa.Text(), nullable=True),
        sa.Column("security_score", sa.Integer(), nullable=True),
        sa.Column("blocked_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("auto_unblock_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["pair_id"], ["pairs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_security_audit_pair_id", "security_audit_log", ["pair_id"])
    op.create_index("idx_security_audit_blocked_at", "security_audit_log", ["blocked_at"])


def downgrade() -> None:
    op.drop_index("idx_security_audit_blocked_at", table_name="security_audit_log")
    op.drop_index("idx_security_audit_pair_id", table_name="security_audit_log")
    op.drop_table("security_audit_log")

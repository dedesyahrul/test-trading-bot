"""Add curated scam address registry.

Revision ID: 010_scam_registry
Revises: 009_security_audit_log
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "010_scam_registry"
down_revision = "009_security_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scam_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("address_type", sa.String(30), nullable=False),
        sa.Column("scam_type", sa.String(50), nullable=False),
        sa.Column("reported_by", sa.String(100)),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("address"),
    )
    op.create_index("idx_scam_registry_address", "scam_registry", ["address"])
    op.create_index("idx_scam_registry_type", "scam_registry", ["address_type"])


def downgrade() -> None:
    op.drop_index("idx_scam_registry_type", table_name="scam_registry")
    op.drop_index("idx_scam_registry_address", table_name="scam_registry")
    op.drop_table("scam_registry")

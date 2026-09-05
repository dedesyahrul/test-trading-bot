"""Add token developer address for scam registry checks.

Revision ID: 011_token_developer_address
Revises: 010_scam_registry
"""
from alembic import op
import sqlalchemy as sa

revision = "011_token_developer_address"
down_revision = "010_scam_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tokens", sa.Column("developer_address", sa.String(255), nullable=True))
    op.create_index("idx_tokens_developer_address", "tokens", ["developer_address"])


def downgrade() -> None:
    op.drop_index("idx_tokens_developer_address", table_name="tokens")
    op.drop_column("tokens", "developer_address")

"""add es_relevante to promociones

Revision ID: r8s9t0u1v2w
Revises: q7r8s9t0u1v
Create Date: 2026-09-06
"""

from alembic import op
import sqlalchemy as sa


revision = "r8s9t0u1v2w"
down_revision = "q7r8s9t0u1v"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("promociones", sa.Column("es_relevante", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.create_index("ix_promociones_es_relevante", "promociones", ["es_relevante"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_promociones_es_relevante", table_name="promociones")
    op.drop_column("promociones", "es_relevante")

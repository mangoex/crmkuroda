"""add valido_desde to promociones

Revision ID: t0u1v2w3x4y
Revises: s9t0u1v2w3x
Create Date: 2026-10-09
"""

from alembic import op
import sqlalchemy as sa


revision = "t0u1v2w3x4y"
down_revision = "s9t0u1v2w3x"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("promociones", sa.Column("valido_desde", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("promociones", "valido_desde")

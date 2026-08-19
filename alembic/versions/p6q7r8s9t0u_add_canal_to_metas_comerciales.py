"""add canal to metas_comerciales

Revision ID: p6q7r8s9t0u
Revises: o5p6q7r8s9t
Create Date: 2026-08-19
"""

from alembic import op
import sqlalchemy as sa


revision = "p6q7r8s9t0u"
down_revision = "o5p6q7r8s9t"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "metas_comerciales",
        sa.Column("canal", sa.String(length=120), nullable=True),
    )
    op.create_index(
        "ix_metas_comerciales_canal",
        "metas_comerciales",
        ["canal"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_metas_comerciales_canal", table_name="metas_comerciales")
    op.drop_column("metas_comerciales", "canal")

"""add contact name to clientes

Revision ID: o5p6q7r8s9t
Revises: n4o5p6q7r8s
Create Date: 2026-08-08
"""

from alembic import op
import sqlalchemy as sa


revision = "o5p6q7r8s9t"
down_revision = "n4o5p6q7r8s"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clientes", sa.Column("nombre_contacto", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("clientes", "nombre_contacto")

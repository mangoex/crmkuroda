"""add vendedor_padre_id to usuarios (jerarquia padre->hijos)

Revision ID: g7b2c3d4e5f6
Revises: f6a1b2c3d4e5
Create Date: 2026-07-13 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "g7b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f6a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Columna de jerarquia (self-FK a usuarios.id). Nullable: NULL = sin padre.
    op.add_column(
        "usuarios",
        sa.Column(
            "vendedor_padre_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_usuarios_vendedor_padre_id",
        "usuarios",
        "usuarios",
        ["vendedor_padre_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_usuarios_vendedor_padre_id",
        "usuarios",
        ["vendedor_padre_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_usuarios_vendedor_padre_id", table_name="usuarios")
    op.drop_constraint("fk_usuarios_vendedor_padre_id", "usuarios", type_="foreignkey")
    op.drop_column("usuarios", "vendedor_padre_id")

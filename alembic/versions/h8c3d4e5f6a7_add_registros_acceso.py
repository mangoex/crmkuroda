"""add access records for operational dashboard

Revision ID: h8c3d4e5f6a7
Revises: g7b2c3d4e5f6
Create Date: 2026-07-15 21:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "h8c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "g7b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "registros_acceso",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entrada", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("salida", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_registros_acceso_usuario_id", "registros_acceso", ["usuario_id"])
    op.create_index("ix_registros_acceso_entrada", "registros_acceso", ["entrada"])


def downgrade() -> None:
    op.drop_index("ix_registros_acceso_entrada", table_name="registros_acceso")
    op.drop_index("ix_registros_acceso_usuario_id", table_name="registros_acceso")
    op.drop_table("registros_acceso")

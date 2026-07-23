"""add shared data update timestamps

Revision ID: i9d4e5f6a7b8
Revises: h8c3d4e5f6a7
Create Date: 2026-07-22 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "i9d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "h8c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "actualizaciones_datos",
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_por_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["actualizado_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("tipo"),
    )
    # Los datos presentes al desplegar esta mejora ya son la versión vigente.
    op.execute(
        """
        INSERT INTO actualizaciones_datos (tipo)
        SELECT 'inventario-abcf'
        WHERE EXISTS (SELECT 1 FROM inventario_abcf)
        ON CONFLICT (tipo) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO actualizaciones_datos (tipo)
        SELECT 'cotizaciones'
        WHERE EXISTS (SELECT 1 FROM cotizaciones)
        ON CONFLICT (tipo) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("actualizaciones_datos")

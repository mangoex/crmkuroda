"""add commercial analytics tables

Revision ID: j0e5f6a7b8c9
Revises: i9d4e5f6a7b8
Create Date: 2026-07-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "j0e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "i9d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "canales_venta",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("codigo_origen", sa.String(), nullable=False),
        sa.Column("nombre_normalizado", sa.String(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo_origen"),
    )
    op.create_index("ix_canales_venta_codigo_origen", "canales_venta", ["codigo_origen"])

    op.create_table(
        "cotizacion_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cotizacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("codigo_material", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("familia", sa.String(), nullable=True),
        sa.Column("grupo_materiales", sa.String(), nullable=True),
        sa.Column("cantidad_cotizada", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("importe_cotizado", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("cantidad_facturada", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("importe_facturado", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["cotizacion_id"], ["cotizaciones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cotizacion_items_cotizacion_id", "cotizacion_items", ["cotizacion_id"])
    op.create_index("ix_cotizacion_items_codigo_material", "cotizacion_items", ["codigo_material"])
    op.create_index("ix_cotizacion_items_familia", "cotizacion_items", ["familia"])
    op.create_index("ix_cotizacion_items_grupo_materiales", "cotizacion_items", ["grupo_materiales"])

    op.create_table(
        "cotizacion_comentarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cotizacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("autor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=False),
        sa.Column("creado_en", sa.DateTime(), nullable=False),
        sa.Column("editado_en", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["autor_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cotizacion_id"], ["cotizaciones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cotizacion_comentarios_cotizacion_id",
        "cotizacion_comentarios",
        ["cotizacion_id"],
    )
    op.create_index("ix_cotizacion_comentarios_autor_id", "cotizacion_comentarios", ["autor_id"])
    op.create_index("ix_cotizacion_comentarios_creado_en", "cotizacion_comentarios", ["creado_en"])


def downgrade() -> None:
    op.drop_index("ix_cotizacion_comentarios_creado_en", table_name="cotizacion_comentarios")
    op.drop_index("ix_cotizacion_comentarios_autor_id", table_name="cotizacion_comentarios")
    op.drop_index("ix_cotizacion_comentarios_cotizacion_id", table_name="cotizacion_comentarios")
    op.drop_table("cotizacion_comentarios")

    op.drop_index("ix_cotizacion_items_grupo_materiales", table_name="cotizacion_items")
    op.drop_index("ix_cotizacion_items_familia", table_name="cotizacion_items")
    op.drop_index("ix_cotizacion_items_codigo_material", table_name="cotizacion_items")
    op.drop_index("ix_cotizacion_items_cotizacion_id", table_name="cotizacion_items")
    op.drop_table("cotizacion_items")

    op.drop_index("ix_canales_venta_codigo_origen", table_name="canales_venta")
    op.drop_table("canales_venta")

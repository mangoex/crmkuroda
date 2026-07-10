"""add por_entregar table

Revision ID: f6a1b2c3d4e5
Revises: e5f6a1b2c3d4
Create Date: 2026-07-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "e5f6a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "por_entregar",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("factura", sa.String(), nullable=True),
        sa.Column("producto_sku", sa.String(), nullable=True),
        sa.Column("producto_desc", sa.String(), nullable=True),
        sa.Column("cantidad_entregar", sa.Float(), nullable=True),
        sa.Column("vendedor_codigo", sa.String(), nullable=True),
        sa.Column("vendedor_nombre", sa.String(), nullable=True),
        sa.Column("numero_cliente", sa.String(), nullable=True),
        sa.Column("cliente_nombre", sa.String(), nullable=True),
        sa.Column("fecha_disponibilidad", sa.String(), nullable=True),
        sa.Column("dias_disponible", sa.Integer(), nullable=True),
        sa.Column("estado_crm", sa.String(), nullable=True),
        sa.Column("motivo_estado", sa.String(), nullable=True),
        sa.Column("fecha_carga", sa.DateTime(), nullable=True),
    )
    op.create_index(op.f("ix_por_entregar_id"), "por_entregar", ["id"], unique=False)
    op.create_index(op.f("ix_por_entregar_factura"), "por_entregar", ["factura"], unique=False)
    op.create_index(op.f("ix_por_entregar_producto_sku"), "por_entregar", ["producto_sku"], unique=False)
    op.create_index(op.f("ix_por_entregar_vendedor_codigo"), "por_entregar", ["vendedor_codigo"], unique=False)
    op.create_index(op.f("ix_por_entregar_vendedor_nombre"), "por_entregar", ["vendedor_nombre"], unique=False)
    op.create_index(op.f("ix_por_entregar_numero_cliente"), "por_entregar", ["numero_cliente"], unique=False)
    op.create_index(op.f("ix_por_entregar_fecha_disponibilidad"), "por_entregar", ["fecha_disponibilidad"], unique=False)
    op.create_index(op.f("ix_por_entregar_dias_disponible"), "por_entregar", ["dias_disponible"], unique=False)
    op.create_index(op.f("ix_por_entregar_estado_crm"), "por_entregar", ["estado_crm"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_por_entregar_estado_crm"), table_name="por_entregar")
    op.drop_index(op.f("ix_por_entregar_dias_disponible"), table_name="por_entregar")
    op.drop_index(op.f("ix_por_entregar_fecha_disponibilidad"), table_name="por_entregar")
    op.drop_index(op.f("ix_por_entregar_numero_cliente"), table_name="por_entregar")
    op.drop_index(op.f("ix_por_entregar_vendedor_nombre"), table_name="por_entregar")
    op.drop_index(op.f("ix_por_entregar_vendedor_codigo"), table_name="por_entregar")
    op.drop_index(op.f("ix_por_entregar_producto_sku"), table_name="por_entregar")
    op.drop_index(op.f("ix_por_entregar_factura"), table_name="por_entregar")
    op.drop_index(op.f("ix_por_entregar_id"), table_name="por_entregar")
    op.drop_table("por_entregar")

"""extend sobrepedidos for VA05/VL06O import

Revision ID: e5f6a1b2c3d4
Revises: d4e5f6a1b2c3
Create Date: 2026-07-10 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sobrepedidos", sa.Column("factura", sa.String(), nullable=True))
    op.add_column("sobrepedidos", sa.Column("fecha_venta", sa.String(), nullable=True))
    op.add_column("sobrepedidos", sa.Column("numero_cliente", sa.String(), nullable=True))
    op.add_column("sobrepedidos", sa.Column("indicador", sa.String(), nullable=True))
    op.add_column("sobrepedidos", sa.Column("grupo", sa.String(), nullable=True))
    op.add_column("sobrepedidos", sa.Column("disponibilidad_vl06o", sa.String(), nullable=True))
    op.add_column("sobrepedidos", sa.Column("cantidad_disponible", sa.Float(), nullable=True))
    op.add_column("sobrepedidos", sa.Column("fecha_disponibilidad", sa.String(), nullable=True))
    op.add_column("sobrepedidos", sa.Column("dias_disponible", sa.Integer(), nullable=True))
    op.add_column("sobrepedidos", sa.Column("motivo_estado", sa.String(), nullable=True))
    op.create_index(op.f("ix_sobrepedidos_factura"), "sobrepedidos", ["factura"], unique=False)
    op.create_index(op.f("ix_sobrepedidos_fecha_venta"), "sobrepedidos", ["fecha_venta"], unique=False)
    op.create_index(op.f("ix_sobrepedidos_numero_cliente"), "sobrepedidos", ["numero_cliente"], unique=False)
    op.create_index(op.f("ix_sobrepedidos_indicador"), "sobrepedidos", ["indicador"], unique=False)
    op.create_index(op.f("ix_sobrepedidos_grupo"), "sobrepedidos", ["grupo"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sobrepedidos_grupo"), table_name="sobrepedidos")
    op.drop_index(op.f("ix_sobrepedidos_indicador"), table_name="sobrepedidos")
    op.drop_index(op.f("ix_sobrepedidos_numero_cliente"), table_name="sobrepedidos")
    op.drop_index(op.f("ix_sobrepedidos_fecha_venta"), table_name="sobrepedidos")
    op.drop_index(op.f("ix_sobrepedidos_factura"), table_name="sobrepedidos")
    op.drop_column("sobrepedidos", "motivo_estado")
    op.drop_column("sobrepedidos", "dias_disponible")
    op.drop_column("sobrepedidos", "fecha_disponibilidad")
    op.drop_column("sobrepedidos", "cantidad_disponible")
    op.drop_column("sobrepedidos", "disponibilidad_vl06o")
    op.drop_column("sobrepedidos", "grupo")
    op.drop_column("sobrepedidos", "indicador")
    op.drop_column("sobrepedidos", "numero_cliente")
    op.drop_column("sobrepedidos", "fecha_venta")
    op.drop_column("sobrepedidos", "factura")

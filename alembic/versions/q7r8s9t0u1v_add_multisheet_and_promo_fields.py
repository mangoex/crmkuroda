"""add multisheet and promo fields to cotizaciones and cotizacion_items

Revision ID: q7r8s9t0u1v
Revises: p6q7r8s9t0u
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa


revision = "q7r8s9t0u1v"
down_revision = "p6q7r8s9t0u"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cotizaciones
    op.add_column("cotizaciones", sa.Column("hora_facturacion", sa.String(), nullable=True))
    op.add_column("cotizaciones", sa.Column("margen", sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column("cotizaciones", sa.Column("grupo_vendedores", sa.String(), nullable=True))
    op.add_column("cotizaciones", sa.Column("plazo_entrega", sa.String(), nullable=True))
    op.create_index("ix_cotizaciones_grupo_vendedores", "cotizaciones", ["grupo_vendedores"], unique=False)

    # Cotizacion Items
    op.add_column("cotizacion_items", sa.Column("indicador_abcf", sa.String(), nullable=True))
    op.add_column("cotizacion_items", sa.Column("unidad_medida", sa.String(), nullable=True))
    op.add_column("cotizacion_items", sa.Column("precio_venta", sa.Numeric(precision=14, scale=2), server_default="0", nullable=False))
    op.add_column("cotizacion_items", sa.Column("es_promocion", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("cotizacion_items", sa.Column("precio_promocion", sa.Numeric(precision=14, scale=2), nullable=True))
    op.create_index("ix_cotizacion_items_indicador_abcf", "cotizacion_items", ["indicador_abcf"], unique=False)
    op.create_index("ix_cotizacion_items_es_promocion", "cotizacion_items", ["es_promocion"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cotizacion_items_es_promocion", table_name="cotizacion_items")
    op.drop_index("ix_cotizacion_items_indicador_abcf", table_name="cotizacion_items")
    op.drop_column("cotizacion_items", "precio_promocion")
    op.drop_column("cotizacion_items", "es_promocion")
    op.drop_column("cotizacion_items", "precio_venta")
    op.drop_column("cotizacion_items", "unidad_medida")
    op.drop_column("cotizacion_items", "indicador_abcf")

    op.drop_index("ix_cotizaciones_grupo_vendedores", table_name="cotizaciones")
    op.drop_column("cotizaciones", "plazo_entrega")
    op.drop_column("cotizaciones", "grupo_vendedores")
    op.drop_column("cotizaciones", "margen")
    op.drop_column("cotizaciones", "hora_facturacion")

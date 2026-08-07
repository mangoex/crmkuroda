"""add quote operational indexes

Revision ID: k1e5f6a7b8c9
Revises: j0e5f6a7b8c9
Create Date: 2026-08-06
"""

from alembic import op


revision = "k1e5f6a7b8c9"
down_revision = "j0e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_cotizaciones_vendedor_fecha",
        "cotizaciones",
        ["vendedor_id", "fecha_registro"],
    )
    op.create_index(
        "ix_cotizaciones_fecha_numero",
        "cotizaciones",
        ["fecha_registro", "numero_cotizacion"],
    )
    op.execute(
        "CREATE INDEX ix_cotizaciones_unlinked_seller_name "
        "ON cotizaciones (upper(trim(vendedor_nombre))) "
        "WHERE vendedor_id IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX ix_cotizaciones_unlinked_seller_name")
    op.drop_index("ix_cotizaciones_fecha_numero", table_name="cotizaciones")
    op.drop_index("ix_cotizaciones_vendedor_fecha", table_name="cotizaciones")

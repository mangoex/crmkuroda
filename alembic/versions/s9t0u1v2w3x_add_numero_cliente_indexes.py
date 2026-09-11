"""add numero_cliente indexes to cotizaciones

Revision ID: s9t0u1v2w3x
Revises: r8s9t0u1v2w
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa


revision = "s9t0u1v2w3x"
down_revision = "r8s9t0u1v2w"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_cotizaciones_numero_cliente "
        "ON cotizaciones (numero_cliente)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_cotizaciones_upper_trim_numero_cliente "
        "ON cotizaciones (upper(trim(numero_cliente)))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_cotizaciones_upper_trim_numero_cliente")
    op.execute("DROP INDEX IF EXISTS ix_cotizaciones_numero_cliente")

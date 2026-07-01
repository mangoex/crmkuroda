"""increase pct precision

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-07-01 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a1'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('cotizaciones', 'porcentaje_importe', type_=sa.Numeric(precision=10, scale=2))
    op.alter_column('cotizaciones', 'porcentaje_materiales', type_=sa.Numeric(precision=10, scale=2))


def downgrade() -> None:
    pass

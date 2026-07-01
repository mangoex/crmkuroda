"""add excel columns to cotizaciones

Revision ID: a1b2c3d4e5f6
Revises: 7febaed0465a
Create Date: 2026-07-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '7febaed0465a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to cotizaciones
    op.add_column('cotizaciones', sa.Column('organizacion_ventas', sa.String(), nullable=True))
    op.add_column('cotizaciones', sa.Column('vendedor_nombre', sa.String(), nullable=True))
    op.add_column('cotizaciones', sa.Column('numero_cliente', sa.String(), nullable=True))
    op.add_column('cotizaciones', sa.Column('importe_facturado', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('cotizaciones', sa.Column('porcentaje_importe', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('cotizaciones', sa.Column('materiales_cotizados', sa.Text(), nullable=True))
    op.add_column('cotizaciones', sa.Column('materiales_facturados', sa.Text(), nullable=True))
    op.add_column('cotizaciones', sa.Column('porcentaje_materiales', sa.Numeric(precision=5, scale=2), nullable=True))
    
    # Alter vendedor_id to be nullable
    with op.batch_alter_table('cotizaciones') as batch_op:
        batch_op.alter_column('vendedor_id', existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    pass

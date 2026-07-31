"""Add recordatorios_seguimiento table

Revision ID: k1f6a7b8c9d0
Revises: j0e5f6a7b8c9
Create Date: 2026-07-31 18:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'k1f6a7b8c9d0'
down_revision = 'j0e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'recordatorios_seguimiento',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cotizacion_id', postgresql.UUID(as_uuid=True),
                   sa.ForeignKey('cotizaciones.id', ondelete='CASCADE'),
                   nullable=False, index=True),
        sa.Column('vendedor_id', postgresql.UUID(as_uuid=True),
                   sa.ForeignKey('usuarios.id', ondelete='CASCADE'),
                   nullable=False, index=True),
        sa.Column('fecha_programada', sa.Date(), nullable=False, index=True),
        sa.Column('nota', sa.Text(), nullable=True),
        sa.Column('completado', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completado_en', sa.DateTime(), nullable=True),
        sa.Column('creado_en', sa.DateTime(), nullable=False,
                   server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('recordatorios_seguimiento')

"""Add clientes table

Revision ID: l2m3n4o5p6q7
Revises: k1f6a7b8c9d0
Create Date: 2026-08-04 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'l2m3n4o5p6q7'
down_revision = 'k1f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'clientes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('sociedad', sa.String(length=50), nullable=True),
        sa.Column('numero_cliente', sa.String(length=50), nullable=True, index=True),
        sa.Column('nombre', sa.String(length=255), nullable=False, index=True),
        sa.Column('rfc', sa.String(length=20), nullable=True, index=True),
        sa.Column('tipo_persona', sa.String(length=50), nullable=True, index=True),
        sa.Column('calle', sa.String(length=255), nullable=True),
        sa.Column('numero_exterior', sa.String(length=50), nullable=True),
        sa.Column('colonia', sa.String(length=150), nullable=True, index=True),
        sa.Column('codigo_postal', sa.String(length=20), nullable=True),
        sa.Column('poblacion', sa.String(length=150), nullable=True, index=True),
        sa.Column('estado', sa.String(length=100), nullable=True),
        sa.Column('telefono', sa.String(length=50), nullable=True),
        sa.Column('celular', sa.String(length=50), nullable=True),
        sa.Column('fax', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('clientes')

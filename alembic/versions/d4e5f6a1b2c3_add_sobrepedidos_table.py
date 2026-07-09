"""add sobrepedidos table

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-07-09 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a1b2c3'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'sobrepedidos',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('id_pedido_erp', sa.Integer(), nullable=True),
        sa.Column('cliente_nombre', sa.String(), nullable=True),
        sa.Column('vendedor_codigo', sa.String(), nullable=True),
        sa.Column('vendedor_nombre', sa.String(), nullable=True),
        sa.Column('producto_sku', sa.String(), nullable=True),
        sa.Column('producto_desc', sa.String(), nullable=True),
        sa.Column('cantidad_pendiente', sa.Float(), nullable=True),
        sa.Column('fecha_pedido', sa.String(), nullable=True),
        sa.Column('estatus_compras', sa.String(), nullable=True),
        sa.Column('proveedor', sa.String(), nullable=True),
        sa.Column('estado_crm', sa.String(), nullable=True),
        sa.Column('fecha_carga', sa.DateTime(), nullable=True)
    )
    op.create_index(op.f('ix_sobrepedidos_id'), 'sobrepedidos', ['id'], unique=False)
    op.create_index(op.f('ix_sobrepedidos_id_pedido_erp'), 'sobrepedidos', ['id_pedido_erp'], unique=False)
    op.create_index(op.f('ix_sobrepedidos_vendedor_nombre'), 'sobrepedidos', ['vendedor_nombre'], unique=False)
    op.create_index(op.f('ix_sobrepedidos_vendedor_codigo'), 'sobrepedidos', ['vendedor_codigo'], unique=False)
    op.create_index(op.f('ix_sobrepedidos_producto_sku'), 'sobrepedidos', ['producto_sku'], unique=False)
    op.create_index(op.f('ix_sobrepedidos_proveedor'), 'sobrepedidos', ['proveedor'], unique=False)
    op.create_index(op.f('ix_sobrepedidos_estado_crm'), 'sobrepedidos', ['estado_crm'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_sobrepedidos_estado_crm'), table_name='sobrepedidos')
    op.drop_index(op.f('ix_sobrepedidos_proveedor'), table_name='sobrepedidos')
    op.drop_index(op.f('ix_sobrepedidos_producto_sku'), table_name='sobrepedidos')
    op.drop_index(op.f('ix_sobrepedidos_vendedor_codigo'), table_name='sobrepedidos')
    op.drop_index(op.f('ix_sobrepedidos_vendedor_nombre'), table_name='sobrepedidos')
    op.drop_index(op.f('ix_sobrepedidos_id_pedido_erp'), table_name='sobrepedidos')
    op.drop_index(op.f('ix_sobrepedidos_id'), table_name='sobrepedidos')
    op.drop_table('sobrepedidos')

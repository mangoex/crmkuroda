"""vincular cotizaciones huerfanas y asignar K96 a mario navarro

Revision ID: u1v2w3x4y5z
Revises: t0u1v2w3x4y
Create Date: 2026-10-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


revision = "u1v2w3x4y5z"
down_revision = "t0u1v2w3x4y"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # 1. Asignar clave K96 a mario.navarro@kuroda.com si existe y no tiene codigo
    conn.execute(text("""
        UPDATE usuarios
        SET codigo_vendedor = 'K96'
        WHERE email = 'mario.navarro@kuroda.com'
          AND (codigo_vendedor IS NULL OR codigo_vendedor = '');
    """))

    # 2. Vincular cotizaciones sin vendedor_id que coincidan con codigo_vendedor en grupo_vendedores
    conn.execute(text("""
        UPDATE cotizaciones
        SET vendedor_id = (
            SELECT u.id FROM usuarios u
            WHERE u.codigo_vendedor IS NOT NULL
              AND upper(trim(cotizaciones.grupo_vendedores)) = upper(trim(u.codigo_vendedor))
            LIMIT 1
        )
        WHERE vendedor_id IS NULL
          AND grupo_vendedores IS NOT NULL
          AND EXISTS (
            SELECT 1 FROM usuarios u
            WHERE u.codigo_vendedor IS NOT NULL
              AND upper(trim(cotizaciones.grupo_vendedores)) = upper(trim(u.codigo_vendedor))
          );
    """))

    # 3. Vincular cotizaciones sin vendedor_id cuyo vendedor_nombre coincida o sea prefijo truncado de 20 caracteres
    conn.execute(text("""
        UPDATE cotizaciones
        SET vendedor_id = (
            SELECT u.id FROM usuarios u
            WHERE u.nombre_completo IS NOT NULL
              AND (
                upper(trim(cotizaciones.vendedor_nombre)) = upper(trim(u.nombre_completo))
                OR (
                    length(trim(cotizaciones.vendedor_nombre)) >= 15
                    AND upper(trim(u.nombre_completo)) LIKE upper(trim(cotizaciones.vendedor_nombre)) || '%'
                )
              )
            LIMIT 1
        )
        WHERE vendedor_id IS NULL
          AND vendedor_nombre IS NOT NULL
          AND EXISTS (
            SELECT 1 FROM usuarios u
            WHERE u.nombre_completo IS NOT NULL
              AND (
                upper(trim(cotizaciones.vendedor_nombre)) = upper(trim(u.nombre_completo))
                OR (
                    length(trim(cotizaciones.vendedor_nombre)) >= 15
                    AND upper(trim(u.nombre_completo)) LIKE upper(trim(cotizaciones.vendedor_nombre)) || '%'
                )
              )
          );
    """))


def downgrade() -> None:
    pass

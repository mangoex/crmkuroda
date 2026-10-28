"""add bot_lectura readonly role, user columns and operational indexes for /api/v1/bot

Revision ID: v2w3x4y5z6a
Revises: u1v2w3x4y5z
Create Date: 2026-10-28
"""

import os
from alembic import op
from sqlalchemy.sql import text


revision = "v2w3x4y5z6a"
down_revision = "u1v2w3x4y5z"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # 1. Nuevas columnas opcionales en usuarios para /api/v1/bot/vendedores
    if dialect == "postgresql":
        conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS equipo VARCHAR;"))
        conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS fecha_alta TIMESTAMPTZ DEFAULT NOW();"))

    # 2. Índices solicitados en vendedor_id, fecha y estatus de ventas y cotizaciones
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cotizaciones_vendedor_id ON cotizaciones (vendedor_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cotizaciones_fecha_registro ON cotizaciones (fecha_registro);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cotizaciones_fecha_factura ON cotizaciones (fecha_factura);"))
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_cotizaciones_estatus_bot "
            "ON cotizaciones (numero_factura, venta_perdida, fecha_registro);"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_cotizaciones_vendedor_factura_fecha "
            "ON cotizaciones (vendedor_id, fecha_factura, fecha_registro);"
        )
    )
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_metas_vendedor_id ON metas (vendedor_id);"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_metas_fechas ON metas (fecha_inicio, fecha_limite);"))
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_recordatorios_vendedor_estado_fecha "
            "ON recordatorios_seguimiento (vendedor_id, completado, fecha_programada);"
        )
    )

    # 3. Rol de PostgreSQL de solo lectura (bot_lectura) con SELECT únicamente en tablas del bot
    if dialect == "postgresql":
        bot_pwd = (os.getenv("BOT_DB_PASSWORD") or "BotLectura_Secure_2026_ReadOnly!").replace("'", "''")
        conn.execute(
            text(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bot_lectura') THEN
                        EXECUTE 'CREATE ROLE bot_lectura WITH LOGIN PASSWORD ''{bot_pwd}'' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT';
                    END IF;
                END
                $$;
                """
            )
        )
        conn.execute(text("GRANT USAGE ON SCHEMA public TO bot_lectura;"))
        conn.execute(text("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM bot_lectura;"))
        conn.execute(
            text(
                "GRANT SELECT ON TABLE "
                "usuarios, cotizaciones, cotizacion_items, cotizacion_comentarios, "
                "metas, metas_comerciales, clientes, recordatorios_seguimiento "
                "TO bot_lectura;"
            )
        )
        conn.execute(text("ALTER USER bot_lectura SET default_transaction_read_only = on;"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP INDEX IF EXISTS ix_recordatorios_vendedor_estado_fecha;"))
    conn.execute(text("DROP INDEX IF EXISTS ix_metas_fechas;"))
    conn.execute(text("DROP INDEX IF EXISTS ix_metas_vendedor_id;"))
    conn.execute(text("DROP INDEX IF EXISTS ix_cotizaciones_vendedor_factura_fecha;"))
    conn.execute(text("DROP INDEX IF EXISTS ix_cotizaciones_estatus_bot;"))
    conn.execute(text("DROP INDEX IF EXISTS ix_cotizaciones_fecha_factura;"))
    conn.execute(text("DROP INDEX IF EXISTS ix_cotizaciones_fecha_registro;"))
    conn.execute(text("DROP INDEX IF EXISTS ix_cotizaciones_vendedor_id;"))

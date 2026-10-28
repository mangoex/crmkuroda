-- =============================================================================
-- Endurecimiento de PostgreSQL para el módulo /api/v1/bot (CRM Kuroda)
-- 1. Rotación de contraseña del superusuario postgres
-- 2. Creación del rol de solo lectura `bot_lectura` con SELECT exclusivo
-- 3. Índices en vendedor_id, fecha y estatus de ventas y cotizaciones
-- =============================================================================

-- 1) Cambiar la contraseña del usuario postgres (reemplazar al ejecutar o vía variable psql -v)
-- Ejemplo de uso:
--   psql -v postgres_pwd="'NuevaClavePostgresSegura'" -v bot_pwd="'ClaveBotLecturaSegura'" -f scripts/setup_bot_db_security.sql
\if :{?postgres_pwd}
ALTER USER postgres WITH PASSWORD :postgres_pwd;
\endif

-- 2) Crear rol bot_lectura sin privilegios administrativos y forzar solo lectura
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bot_lectura') THEN
        CREATE ROLE bot_lectura WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
END
$$;

\if :{?bot_pwd}
ALTER ROLE bot_lectura WITH PASSWORD :bot_pwd;
\endif

ALTER ROLE bot_lectura SET default_transaction_read_only = on;
ALTER ROLE bot_lectura SET timezone = 'America/Mazatlan';

-- 3) Revocar permisos previos y otorgar SELECT únicamente sobre las tablas del módulo /api/v1/bot
GRANT USAGE ON SCHEMA public TO bot_lectura;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM bot_lectura;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM bot_lectura;
REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM bot_lectura;

GRANT SELECT ON TABLE
    usuarios,
    cotizaciones,
    cotizacion_items,
    cotizacion_comentarios,
    metas,
    metas_comerciales,
    clientes,
    recordatorios_seguimiento
TO bot_lectura;

-- 4) Índices de rendimiento en vendedor_id, fecha y estatus de ventas y cotizaciones
CREATE INDEX IF NOT EXISTS ix_cotizaciones_vendedor_id ON cotizaciones (vendedor_id);
CREATE INDEX IF NOT EXISTS ix_cotizaciones_fecha_registro ON cotizaciones (fecha_registro);
CREATE INDEX IF NOT EXISTS ix_cotizaciones_fecha_factura ON cotizaciones (fecha_factura);
CREATE INDEX IF NOT EXISTS ix_cotizaciones_estatus_bot ON cotizaciones (numero_factura, venta_perdida, fecha_registro);
CREATE INDEX IF NOT EXISTS ix_cotizaciones_vendedor_factura_fecha ON cotizaciones (vendedor_id, fecha_factura, fecha_registro);
CREATE INDEX IF NOT EXISTS ix_metas_vendedor_id ON metas (vendedor_id);
CREATE INDEX IF NOT EXISTS ix_metas_fechas ON metas (fecha_inicio, fecha_limite);
CREATE INDEX IF NOT EXISTS ix_recordatorios_vendedor_estado_fecha ON recordatorios_seguimiento (vendedor_id, completado, fecha_programada);

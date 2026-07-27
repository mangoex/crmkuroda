# Validación — Analítica y seguimiento comercial

Fecha: 2026-07-26

## Resultado

Las nueve historias cuentan con contrato, implementación, migración reversible
y pruebas automatizadas. No se ejecutó migración sobre una base real ni se
realizó despliegue; esas acciones requieren el entorno de destino.

## Evidencia ejecutada

- `venv/bin/python -m unittest discover -s tests -v`
  - 36 pruebas aprobadas.
- `node --check static/app.js`
  - código de salida 0.
- `venv/bin/python -m compileall -q app tests alembic/versions`
  - código de salida 0.
- `venv/bin/alembic heads`
  - una sola cabeza: `j0e5f6a7b8c9`.
- `venv/bin/alembic upgrade i9d4e5f6a7b8:j0e5f6a7b8c9 --sql`
  - genera las tres tablas, índices y llaves foráneas.
- `venv/bin/alembic downgrade j0e5f6a7b8c9:i9d4e5f6a7b8 --sql`
  - elimina de forma reversible únicamente las tres tablas nuevas.
- Importación de `app.main`
  - registra las rutas estáticas antes de `/{cotizacion_id}` y expone todas las
    rutas nuevas de cotizaciones y analítica.
- Navegador local
  - página cargada sin errores de consola;
  - controles nuevos presentes en el DOM;
  - cero elementos laterales con `draggable="true"`.
- `git diff --check`
  - código de salida 0.

## Límites de esta validación

La comprobación en navegador llegó hasta la pantalla de autenticación porque
no se levantó una base PostgreSQL local con datos de prueba. Los cálculos,
permisos y flujos de carga/comentarios sí se validaron mediante pruebas de
servicio y API con colaboradores controlados.

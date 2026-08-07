# Validación — Analítica y seguimiento comercial

Fecha: 2026-08-06

## Resultado

Las diez historias cuentan con contrato, implementación, migración reversible
y pruebas automatizadas. La operación de cotizaciones y seguimiento ya no
materializa el histórico completo en el navegador: usa páginas de 50 registros,
un máximo contractual de 100 y una vista resumen con KPI calculados en SQL.
No se ejecutó migración sobre una base real ni se realizó despliegue; esas
acciones requieren el entorno de destino.

## Evidencia ejecutada

- `venv/bin/python -B -m unittest discover -s tests -v`
  - 46 pruebas aprobadas, incluidas las cinco de contrato de rendimiento.
- `node --check static/app.js`
  - código de salida 0.
- `venv/bin/python -m compileall -q app tests alembic/versions`
  - código de salida 0.
- `venv/bin/python -m alembic upgrade k1e5f6a7b8c9 --sql`
  - genera los índices operativos de vendedor/fecha, fecha/folio y asesor no vinculado.
- `venv/bin/python -m alembic downgrade k1e5f6a7b8c9:j0e5f6a7b8c9 --sql`
  - elimina de forma reversible únicamente esos tres índices.
- Importación de `app.main`
  - registra las rutas estáticas antes de `/{cotizacion_id}` y expone todas las
    rutas nuevas de cotizaciones y analítica.
- `node test_jsdom.js`
  - no ejecutable en esta copia: falta la dependencia local `jsdom`; no se
    instalaron paquetes ni se modificó el lockfile fuera del alcance autorizado.
- `git diff --check`
  - código de salida 0.

## Límites de esta validación

La comprobación visual autenticada y la medición de latencia real requieren una
base PostgreSQL con volumen equivalente y credenciales de prueba. La migración
se validó como SQL, no se aplicó a una base real. El detalle comercial pesado
permanece bajo demanda y la analítica por canal/material se carga sólo por
acción explícita.

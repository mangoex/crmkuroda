# Validación — Analítica y seguimiento comercial

Fecha: 2026-08-06

## Resultado

Las once historias cuentan con contrato, implementación, migración reversible
y pruebas automatizadas. La operación de cotizaciones y seguimiento ya no
materializa el histórico completo en el navegador: usa páginas de 50 registros,
un máximo contractual de 100 y una vista resumen con KPI calculados en SQL.
Seguimiento consulta sus estados en paralelo, por lo que las vencidas aparecen
sin depender de la primera página cronológica.
La sección Metas entrega a gerencia objetivos mensuales generales, por vendedor
y por `organizacion_ventas`; día y semana se prorratean determinísticamente.
El vendedor recibe sólo su avance propio desde el backend.
No se ejecutó migración sobre una base real ni se realizó despliegue; esas
acciones requieren el entorno de destino.

## Evidencia ejecutada

- `venv/bin/python -B -m unittest discover -s tests -v`
  - 76 pruebas aprobadas, incluidas las cinco de contrato de metas comerciales.
- `node --check static/app.js`
  - código de salida 0.
- `venv/bin/python -m compileall -q app tests alembic/versions`
  - código de salida 0.
- `venv/bin/python -m alembic upgrade n4o5p6q7r8s --sql`
  - genera la tabla auditable `metas_comerciales`, restricciones de alcance e índices de consulta.
- `venv/bin/python -m alembic downgrade n4o5p6q7r8s:m3n4o5p6q7r8 --sql`
  - elimina de forma reversible únicamente la tabla e índices de metas comerciales.
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

# Changelog

Todas las actualizaciones y correciones notables al proyecto **CRM Kuroda** se documentarán en este archivo.

## [1.1.0] - 2026-06-24
### Auditoría Profunda y Estabilización

### Seguridad y Control de Acceso ??
- **RBAC Reforzado:** Implementada validación de roles en endpoints críticos (`/api/v1/analisis`, `/api/auth/register`, `/api/v1/vendedores`). Los usuarios sin rol de 'admin' o 'gerente' no pueden acceder a datos financieros consolidados ni crear nuevas cuentas libremente.
- **Validación Criptográfica en Webhooks:** El webhook de WhatsApp ahora valida `X-Hub-Signature-256`, rechazando payloads falsificados.
- **Sanitización XSS (Frontend):** Agregada la función `escapeHTML` en `app.js` para mitigar inyecciones de Cross-Site Scripting (XSS) en las tablas de vendedores, métricas, y tarjetas del Kanban.

### Estabilidad y Base de Datos ??
- **Integración de Alembic:** Eliminadas las sentencias de `Base.metadata.create_all()` y `ALTER TABLE` manuales en el inicio de la aplicación. Se inicializó `alembic` configurado para `postgresql+asyncpg` para administrar las migraciones asíncronas de manera profesional.
- **Transacciones Seguras:** Eliminado el auto-commit prematuro en la dependencia asíncrona `get_db()`. Ahora el commit solo sucede tras completarse el bloque lógico, previniendo estados muertos y *deadlocks*.
- **Optimización Queries N+1:** El endpoint de dashboard global en `companies.py` fue refactorizado. Las iteraciones que causaban múltiples queries para buscar `SlightEdgePlan` y `SlightEdgeLog` por vendedor, se procesan ahora en un solo bloque con diccionarios de Python (reduciendo de $O(N)$ a $O(1)$ la complejidad de base de datos).
- **Límites de Paginación:** Restringido el parámetro `limit` de 5000 a 100 en `/api/v1/cotizaciones` para prevenir vulnerabilidades de denegación de servicio (DoS).

### Interfaz y Lógica ???
- **Resolución de "Ghost Bids":** En `asignaciones.py`, al re-subastar un lead, las pujas obsoletas ya no permanecen en la base de datos debido a un bug lógico (ahora se aplica `delete()` en lugar de `select()`).
- **Fuga de Memoria Kanban:** Solucionado el problema donde arrastrar y soltar (Drag and Drop) multiplicaba infinitamente los 'event listeners' usando una bandera preventiva `dataset.dndSetup = "true"`.
- **Limpieza de "Hardcoded Dates":** Las fechas de evaluación estáticas para pruebas en el funnel y KPIs fueron sustituidas por el cálculo en tiempo real con `new Date()`.

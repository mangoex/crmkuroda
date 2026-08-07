# PRD — Analítica y seguimiento comercial

Estado: aprobado para desarrollo
Versión: 1.1
Fecha: 2026-08-06

## Objetivo

Dar a gerencia una lectura confiable del rendimiento comercial y a los
asesores herramientas operativas para priorizar, contactar y dar seguimiento
a sus cotizaciones.

## Decisiones de producto

- Venta lograda significa importe facturado.
- La vigencia operativa de una cotización pendiente es de 30 días.
- El día comercial se calcula con la zona horaria configurada; por defecto
  `America/Mazatlan`.
- El menú lateral tiene un orden fijo estricto (Mi Panel, Seguimiento, Cotizaciones, Promociones, Inventario D, Sobrepedidos, Por entregar, Vendedores, Centro de Agentes, La Ventaja, Asignación, API WhatsApp) sin funcionalidad de reordenamiento drag & drop.
- El sistema opera únicamente en versión clara (light-mode), habiendo deshabilitado la conmutación a modo oscuro.
- Los cálculos deterministas de menú, ordenamiento y métricas son procesados exclusivamente en backend con Python.
- El contacto preferente es celular y, si falta, teléfono.
- Los comentarios de seguimiento son un historial independiente del motivo de
  venta perdida.
- Los canales se normalizan mediante un catálogo administrable. Un código sin
  relación explícita se reporta como `Sin clasificar`.
- Las coincidencias de promociones se realizan únicamente por código exacto de
  material y vigencia.
- Ver todas las cotizaciones significa poder recorrer el universo autorizado
  mediante filtros y páginas; no descargarlo completo al navegador.
- Los cálculos comerciales, estados y agregados se resuelven de forma
  determinista en Python o PostgreSQL. El LLM no interviene en resultados,
  filtros ni paginación.

## Roles

- `admin`: acceso completo y configuración de canales.
- `gerente`: lectura completa, analítica y comentarios sobre cualquier
  cotización.
- `vendedor`: datos propios y de hijos directos según la jerarquía vigente.
- `soporte`: conserva su acceso operativo actual; no obtiene analítica
  comercial ni mutaciones nuevas.

## Historias

### HU-01 — Ventas por asesor, familia y grupo de materiales

Gerencia consulta importe y unidades facturadas por asesor, familia, grupo y
SKU. Los vendedores consultan únicamente su ámbito visible. La suma del detalle
debe reconciliar con el total de partidas facturadas del mismo filtro.

### HU-02 — Ventas por canal

Gerencia y vendedores consultan importe facturado, operaciones, importe
cotizado, conversión, ticket promedio y participación por canal. Los códigos
desconocidos permanecen visibles como `Sin clasificar`.

### HU-03 — Orden fijo del menú lateral y modo claro exclusivo

Las pestañas del menú lateral se presentan en un orden estricto (Mi Panel, Seguimiento, Cotizaciones, Promociones, Inventario D, Sobrepedidos, Por entregar, Vendedores, Centro de Agentes, La Ventaja, Asignación, API WhatsApp) y no se pueden reordenar mediante arrastre (*drag & drop*) ni preferencias guardadas. El sistema opera exclusivamente en su versión clara (light-mode).

### HU-04 — Rendimiento de asesores

Gerencia consulta meta, facturación, cumplimiento, cotizaciones, conversiones,
ticket promedio, pendientes y consistencia por asesor y periodo.

### HU-05 — Cotizaciones completas para gerencia

Gerencia ve todas las cotizaciones. Los registros históricos sin UUID se
resuelven por código o nombre inequívoco; si no se resuelven, siguen visibles
como `Asesor sin vincular`.

### HU-06 — Filtro rápido Hoy

La sección Cotizaciones ofrece `Hoy`, `Este mes` y `Todas`. `Hoy` representa la
fecha calendario de la zona horaria comercial, no las últimas 24 horas.

### HU-07 — Comentarios de seguimiento

Cada cotización tiene un historial con texto, autor y fecha. Los comentarios no
reemplazan el motivo de venta perdida.

### HU-08 — Prioridad por promoción

Las cotizaciones pendientes y vigentes con SKU en promoción aparecen primero,
con materiales coincidentes, precio y fecha límite. Una promoción vencida o
una coincidencia solo por descripción no genera prioridad.

### HU-09 — Contacto del cliente

Cotizaciones, seguimiento y asignaciones muestran contacto preferente y
acciones de llamada o WhatsApp cuando corresponda.

### HU-10 — Consulta comercial escalable

Gerencia y vendedores pueden recorrer todas las cotizaciones autorizadas por
fecha, vendedor, estado y búsqueda de cliente o número de cliente. La interfaz
carga sólo una página operativa y recupera el detalle pesado bajo demanda; los
KPIs mantienen los totales del filtro completo. Seguimiento muestra un conjunto
acotado de tarjetas por carga, sin crear una tarjeta por cada cotización
histórica.

## Requisitos no funcionales

- `NFR-PERF-001`: las listas operativas de cotizaciones y seguimiento no
  solicitan más de 100 registros por petición.
- `NFR-PERF-002`: la lista no transporta propuesta ni partidas SKU; éstos se
  consultan al abrir una cotización autorizada.
- `NFR-DATA-001`: una reconciliación de Excel sólo puede eliminar cotizaciones
  importadas con número de cotización que no estén presentes en el archivo;
  nunca elimina cotizaciones manuales o generadas por agente sin folio.

## Fuera de alcance

- Inferir familia o SKU a partir de descripciones libres.
- Inventar equivalencias entre códigos de canal y nombres comerciales.
- Cambiar la política actual de jerarquía padre-hijo.
- Enviar mensajes de WhatsApp automáticamente desde estas historias.

## Indicadores de éxito

- Cero cotizaciones omitidas para gerencia respecto de la carga fuente.
- Totales analíticos reconciliados con sus fuentes.
- Cero falsos positivos promocionales por coincidencia de texto.
- Comentarios auditables sin pérdida del motivo de venta perdida.
- Contacto visible cuando teléfono o celular existe.
- Navegación estable con el archivo completo de cotizaciones, sin omitir
  registros ni bloquear el navegador por materializar todos los resultados.

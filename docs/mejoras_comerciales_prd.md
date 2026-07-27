# PRD — Analítica y seguimiento comercial

Estado: aprobado para desarrollo
Versión: 1.0
Fecha: 2026-07-26

## Objetivo

Dar a gerencia una lectura confiable del rendimiento comercial y a los
asesores herramientas operativas para priorizar, contactar y dar seguimiento
a sus cotizaciones.

## Decisiones de producto

- Venta lograda significa importe facturado.
- La vigencia operativa de una cotización pendiente es de 30 días.
- El día comercial se calcula con la zona horaria configurada; por defecto
  `America/Mazatlan`.
- El menú lateral tiene un orden fijo para todos los roles.
- El contacto preferente es celular y, si falta, teléfono.
- Los comentarios de seguimiento son un historial independiente del motivo de
  venta perdida.
- Los canales se normalizan mediante un catálogo administrable. Un código sin
  relación explícita se reporta como `Sin clasificar`.
- Las coincidencias de promociones se realizan únicamente por código exacto de
  material y vigencia.

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

### HU-03 — Orden fijo del menú lateral

Las pestañas no se pueden reordenar mediante ratón, tacto o preferencias
guardadas en el navegador.

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

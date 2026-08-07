# SDD — Analítica y seguimiento comercial

Estado: aprobado para desarrollo
Versión: 1.1

## Arquitectura

Se conserva FastAPI, SQLAlchemy async, PostgreSQL, Alembic y el frontend
estático existente.

### Nuevas entidades

#### `cotizacion_items`

- `id` UUID
- `cotizacion_id` UUID con borrado en cascada
- `codigo_material`
- `descripcion`
- `familia`
- `grupo_materiales`
- `cantidad_cotizada`
- `importe_cotizado`
- `cantidad_facturada`
- `importe_facturado`

#### `cotizacion_comentarios`

- `id` UUID
- `cotizacion_id` UUID con borrado en cascada
- `autor_id` UUID con borrado restringido mediante `SET NULL`
- `comentario`
- `creado_en`
- `editado_en`

#### `canales_venta`

- `id`
- `codigo_origen` único
- `nombre_normalizado`
- `activo`

## Servicios

### Contactos

Normaliza `datos_contacto` sin destruir los valores originales y expone
`contacto_preferente`.

### Canales

Resuelve el código crudo mediante `canales_venta`. También reconoce, de forma
determinista, nombres que ya coincidan con Apartados, Kuroda Turbo, Material D,
Promociones o Marketplace.

### Promociones

Cruza `cotizacion_items.codigo_material` con
`promociones.codigo_material`. Requiere `valido_hasta >= hoy`.

### Analítica

Las agregaciones se calculan en código o SQL de forma determinista. El LLM no
participa en cifras comerciales.

### Consulta operativa de cotizaciones

- La lista usa `limit` (máximo 100) y `offset`; el frontend utiliza 50 por
  página.
- `vista=resumen` proyecta sólo los campos para tabla y Kanban. Excluye
  `items`, `items_detalle` y `texto_propuesta`.
- `busqueda` se resuelve en PostgreSQL sobre cliente y número de cliente.
- `estado` acepta `all`, `total`, `concretadas`, `pendientes` y `vencidas`.
  Sus condiciones se calculan de forma determinista con factura, pérdida,
  fecha de registro y `QUOTE_VALID_DAYS`.
- La respuesta resumida incluye indicadores agregados para el filtro base,
  antes del filtro de estado, para conservar los KPI sin descargar todas las
  filas.
- El detalle completo se conserva en `GET /api/v1/cotizaciones/{id}` tras la
  validación de ámbito.
- Los índices de `vendedor_id + fecha_registro`, `fecha_registro +
  numero_cotizacion` y búsqueda histórica por vendedor sin vínculo se gestionan
  mediante una migración Alembic reversible.

## API

- `GET /api/v1/cotizaciones/`
  - conserva filtros actuales y añade `busqueda`, `estado` y `vista`;
  - con `vista=resumen` devuelve una página ligera, prioridad promocional y
    los indicadores deterministas del filtro;
  - conserva la vista completa para integraciones que aún requieran propuesta
    o partidas.
- `GET|POST /api/v1/cotizaciones/{id}/comentarios`
- `PUT /api/v1/cotizaciones/{id}/comentarios/{comentario_id}`
- `POST /api/v1/cotizaciones/detalle-materiales/upload`
- `GET /api/v1/analitica/ventas-por-canal`
- `GET /api/v1/analitica/ventas-por-material`
- `GET /api/v1/analitica/rendimiento-asesores`
- `GET|PUT /api/v1/analitica/canales`

## Contrato de importación de partidas

Encabezados requeridos:

- `Numero de Cotizacion`
- `Codigo Material`
- `Descripcion`
- `Familia`
- `Grupo de Materiales`
- `Cantidad Cotizada`
- `Importe Cotizado`
- `Cantidad Facturada`
- `Importe Facturado`

La carga es transaccional. Una estructura inválida no reemplaza el detalle
existente. Cotizaciones inexistentes se reportan como filas rechazadas. Sólo
se reemplazan las partidas de las cotizaciones que tengan al menos una fila
aceptada; el detalle de otras cotizaciones permanece intacto.

## Permisos

- Toda lectura o mutación de una cotización reutiliza la resolución de ámbito
  de vendedores.
- Configurar canales y cargar partidas requiere `admin` o `gerente`.
- La analítica de equipo requiere `admin` o `gerente`.
- La analítica por canal y material permite al vendedor solo su ámbito.

## Compatibilidad

- El Excel resumen actual continúa funcionando.
- La carga resumen reconcilia por `numero_cotizacion`: conserva el UUID y el
  historial de los registros existentes, crea los nuevos y elimina únicamente
  cotizaciones importadas con número que ya no aparecen en el archivo completo.
- Un número duplicado en el archivo o en la base cancela la transacción para
  evitar una reconciliación ambigua.
- `Cotizacion.items` y las cotizaciones manuales/de agente sin folio se
  conservan durante la reconciliación.
- El detalle por SKU se importa por un endpoint separado.
- El campo legado `comentarios` se conserva para observaciones existentes y
  motivos de venta perdida.

## Reversibilidad

La migración elimina únicamente las tres tablas nuevas en `downgrade`. No
modifica columnas existentes.

# Especificacion de usuario - Sobrepedidos VA05/VL06O

Fecha de analisis: 2026-07-10

Archivo base autorizado: `C:\Users\Miguel Gonzalez\Downloads\VA05.VL06O.CRM.xlsx`

Archivo anterior descartado para esta funcionalidad: `ZVA05VTAS.VL06O.CRM 2.0.xlsx`

## Contexto

El usuario necesita que la pestana `Sobrepedidos` del CRM use como fuente oficial el archivo `VA05.VL06O.CRM.xlsx`.

La implementacion actual fue construida a partir de un archivo anterior que incluia una hoja `SP`. El nuevo archivo ya no contiene `SP`; solo contiene `VA05` y `VL06O`. Por tanto, la importacion actual no es compatible con el archivo base nuevo y debe modificarse antes de usarlo en produccion.

## Estructura del archivo base

### Hoja VA05

Contiene 57 registros y 12 columnas:

- `Fecha Venta`
- `Factura`
- `Vendedor`
- `Num Cliente`
- `Nombre Cliente`
- `Proveedor`
- `Codigo`
- `Indicador`
- `Producto`
- `Grupo`
- `Cantidad Pendiente`
- `Estatus Compras`

Uso previsto:

- Es la lista operativa de productos pendientes por entregar o resolver.
- Cada fila representa una linea de producto pendiente.
- `Factura` funciona como identificador comercial principal del documento.
- `Codigo` identifica el producto/SKU.
- `Cantidad Pendiente` es la cantidad que falta surtir.
- `Estatus Compras` contiene la explicacion de compras, por ejemplo confirmacion, factura de proveedor, back order o falta de informacion.

### Hoja VL06O

Contiene 430 registros y 9 columnas:

- `Factura`
- `Codigo`
- `Producto`
- `Cantidad a Entregar`
- `Clave Vendedor`
- `Num Cliente`
- `Nombre Cliente`
- `Fecha en Disponibilidad`
- `Dias Disponible`

Uso previsto:

- Es la lista logistica de productos disponibles para entrega.
- Debe usarse como evidencia de disponibilidad, pero solo cuando el cruce sea suficientemente especifico.

## Hallazgos de datos

- `VA05` contiene 57 lineas pendientes.
- `VA05` contiene 36 facturas distintas.
- `VA05` contiene 57 codigos de producto distintos.
- `VL06O` contiene 430 lineas y 97 facturas distintas.
- Hay 18 lineas de `VA05` cuya `Factura` aparece en `VL06O`.
- No hay ninguna coincidencia exacta por `Factura + Codigo` entre `VA05` y `VL06O`.
- Por lo anterior, no se debe marcar en verde una linea de VA05 solo porque su factura aparezca en VL06O; eso puede significar que otra linea de la misma factura esta disponible, no necesariamente el producto pendiente.
- El archivo solo tiene color amarillo en encabezados. Los colores verde, amarillo y rojo del CRM no vienen controlados desde el Excel; deben derivarse por reglas de negocio auditables.

## Distribucion observada en Estatus Compras

Sobre las 57 lineas de `VA05`:

- 28 tienen estatus tipo `Fac ...`
- 16 tienen `Sin Informacion de Compras`
- 5 tienen `Confirmacion ...`
- 6 tienen `Back order` con informacion parcial
- 2 tienen `Back order sin fecha`

Tambien se observaron fechas sospechosas en comentarios de factura de proveedor:

- 12 lineas con `Fac 2757742 30.06.2028`
- 4 lineas con `Fac 2757742 30.06.2027`
- 1 linea con `Fac 2757742 30.06.2031`

Estas fechas deben mostrarse como dato recibido, pero conviene marcarlas como posible dato atipico si se implementa validacion adicional.

## Necesidad del usuario

Como gerente o administrador comercial, quiero cargar el archivo `VA05.VL06O.CRM.xlsx` en el CRM para ver los sobrepedidos activos, filtrarlos por vendedor, cliente, proveedor, producto y estado operativo, y saber que partidas requieren accion, seguimiento o entrega.

Como vendedor, quiero ver solamente mis sobrepedidos para poder responder a clientes con informacion clara y actualizada.

## Campos que debe mostrar el CRM

Campos minimos recomendados:

- Fecha venta
- Factura
- Vendedor
- Numero de cliente
- Nombre de cliente
- Proveedor
- Codigo
- Indicador
- Producto
- Grupo
- Cantidad pendiente
- Estatus compras
- Disponibilidad VL06O
- Cantidad disponible VL06O
- Fecha en disponibilidad
- Dias disponible
- Estado CRM
- Motivo del estado

## Reglas propuestas para Estado CRM

Los colores deben tener significado controlado y auditable:

### Verde - Listo / disponible

Usar verde solo cuando exista evidencia directa de disponibilidad para la misma linea:

- Coincidencia por `Factura + Codigo` entre `VA05` y `VL06O`, y
- `Cantidad a Entregar` en VL06O mayor o igual a `Cantidad Pendiente` en VA05.

Si hay coincidencia por `Factura + Codigo`, pero la cantidad disponible es menor que la pendiente, usar amarillo y mostrar disponible parcial.

### Amarillo - En proceso / con avance

Usar amarillo cuando hay avance documentado, pero todavia no hay evidencia completa de disponibilidad:

- `Estatus Compras` contiene `Confirmacion`.
- `Estatus Compras` contiene `Fac`.
- `Estatus Compras` contiene `Back order` con fecha aproximada o comentario de seguimiento.
- Existe coincidencia parcial en `VL06O`, pero no a nivel `Factura + Codigo` o no cubre la cantidad completa.

### Rojo - Requiere accion

Usar rojo cuando falta informacion o no hay fecha clara:

- `Estatus Compras` contiene `Sin Informacion de Compras`.
- `Estatus Compras` contiene `Back order sin fecha`.
- No hay coincidencia en `VL06O` ni comentario operativo util.

## Criterios de aceptacion BDD

### Carga valida

Dado que soy administrador o gerente
Cuando subo un archivo Excel con hojas `VA05` y `VL06O`
Entonces el sistema importa las lineas de `VA05` como sobrepedidos
Y calcula el estado CRM con reglas controladas.

### Archivo incompatible

Dado que subo un archivo Excel
Cuando el archivo no contiene `VA05` o `VL06O`
Entonces el sistema rechaza la carga con un mensaje claro indicando las hojas requeridas.

### Semaforo verde

Dado una linea de `VA05` con `Factura`, `Codigo` y `Cantidad Pendiente`
Cuando existe una linea en `VL06O` con la misma `Factura` y el mismo `Codigo`
Y la suma de `Cantidad a Entregar` cubre la cantidad pendiente
Entonces el estado CRM debe ser verde.

### Semaforo amarillo

Dado una linea de `VA05`
Cuando no hay disponibilidad completa en `VL06O`
Pero `Estatus Compras` indica confirmacion, factura de proveedor o back order con seguimiento
Entonces el estado CRM debe ser amarillo.

### Semaforo rojo

Dado una linea de `VA05`
Cuando `Estatus Compras` indica falta de informacion o back order sin fecha
Entonces el estado CRM debe ser rojo.

### Vista por vendedor

Dado que soy vendedor
Cuando consulto `Sobrepedidos`
Entonces solo veo lineas cuyo `Vendedor` coincide con mi codigo de vendedor.

## Cambios tecnicos esperados

- Cambiar el importador de `app/api/v1/sobrepedidos.py` para que ya no requiera hoja `SP`.
- Parsear `VA05` como fuente principal.
- Parsear `VL06O` como fuente de disponibilidad.
- Cambiar el modelo `Sobrepedido` y la migracion si se agregan campos nuevos.
- Ajustar `static/index.html` y `static/app.js` para mostrar los nuevos campos y filtros.
- Mantener filtros por proveedor, estado y busqueda.
- Agregar filtros recomendados por vendedor, cliente y grupo.
- Agregar pruebas TDD para clasificacion de semaforo y carga del archivo nuevo.
- Mantener documentadas las reglas de color para que verde, amarillo y rojo no dependan de interpretacion visual manual.

## Preguntas abiertas

- Confirmar si `Factura` es el mejor identificador de cruce entre `VA05` y `VL06O`, o si en SAP existe otro campo oculto/documento que relacione mejor las lineas.
- Confirmar si una coincidencia solo por `Factura` debe mostrarse como alerta informativa, pero no como disponibilidad de la linea.
- Confirmar si `Fac ...` en `Estatus Compras` debe significar amarillo o verde. La recomendacion actual es amarillo hasta que exista disponibilidad comprobada en `VL06O`.
- Confirmar como tratar fechas futuras atipicas en comentarios, por ejemplo 2027, 2028 y 2031.

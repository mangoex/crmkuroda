# BDD — Analítica y seguimiento comercial

## HU-01

**Dado** un detalle facturado con asesor, familia, grupo y SKU
**Cuando** gerencia consulta ventas por material
**Entonces** obtiene la jerarquía solicitada
**Y** la suma de partidas coincide con el total del filtro.

## HU-02

**Dado** un código de canal configurado
**Cuando** se consulta la analítica del periodo
**Entonces** la operación aparece bajo el nombre configurado.

**Dado** un código no configurado
**Entonces** la operación aparece en `Sin clasificar`.

## HU-03

**Dado** cualquier rol autenticado
**Cuando** carga el sistema o interactúa con el menú lateral
**Entonces** las pestañas se presentan en el orden fijo oficial (Mi Panel, Seguimiento, Cotizaciones, Promociones, Inventario D, Sobrepedidos, Por entregar, Vendedores, Centro de Agentes, La Ventaja, Asignación, API WhatsApp)
**Y** las pestañas carecen de la capacidad de arrastre (*drag & drop*)
**Y** la interfaz se renderiza exclusivamente en versión clara (*light-mode*).

## HU-04

**Dado** un asesor con facturas, meta y actividades
**Cuando** gerencia consulta rendimiento
**Entonces** la venta lograda proviene de `importe_facturado`
**Y** se muestran cumplimiento, conversión, ticket y consistencia.

## HU-05

**Dado** cotizaciones de varios asesores y una sin vínculo
**Cuando** gerencia abre Cotizaciones
**Entonces** ve todos los registros
**Y** el registro sin vínculo aparece como `Asesor sin vincular`.

## HU-06

**Dado** cotizaciones de hoy y ayer
**Cuando** el usuario activa `Hoy`
**Entonces** únicamente aparecen las de la fecha comercial actual.

## HU-07

**Dado** una cotización permitida
**Cuando** el usuario agrega un comentario
**Entonces** se conserva texto, autor y fecha
**Y** el motivo de venta perdida no cambia.

**Dado** un comentario propio, o un comentario visible para gerencia
**Cuando** se edita el texto
**Entonces** conserva su autor y fecha original
**Y** registra la fecha de edición.

**Dado** un historial existente
**Cuando** se vuelve a cargar el Excel resumen con el mismo número de cotización
**Entonces** se actualizan los datos comerciales sin reemplazar el UUID
**Y** el historial permanece asociado.

## HU-08

**Dado** una cotización vigente con un SKU exacto en promoción vigente
**Cuando** se carga Seguimiento
**Entonces** aparece antes que las cotizaciones sin promoción.

**Dado** una promoción vencida o una descripción parecida sin SKU exacto
**Entonces** no se marca prioridad.

## HU-09

**Dado** un cliente con celular pero sin teléfono
**Cuando** se muestra en Cotizaciones, Seguimiento o Asignaciones
**Entonces** el celular aparece como contacto preferente.

## HU-10 / NFR-PERF-001

**Dado** más cotizaciones autorizadas que el tamaño de página
**Cuando** el usuario abre Cotizaciones o Seguimiento
**Entonces** la API devuelve sólo la página solicitada, nunca más de 100 filas
**Y** informa el total completo para que el usuario pueda recorrer todos los
registros.

**Dado** una búsqueda por cliente, número de cliente, vendedor, fecha o estado
**Cuando** el usuario cambia un filtro
**Entonces** PostgreSQL aplica el filtro antes de paginar
**Y** los KPI se calculan sobre todo el filtro base de forma determinista.

**Dado** una cotización manual o generada por agente sin número oficial
**Cuando** se reconcilia un Excel resumen
**Entonces** la cotización no se elimina
**Y** sólo se eliminan filas importadas con folio ausente del archivo completo.

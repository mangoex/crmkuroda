# Matriz de trazabilidad — Analítica y seguimiento comercial

| Historia | Contrato | Evidencia automatizada | Evidencia de interfaz |
|---|---|---|---|
| HU-01 | SDD: `cotizacion_items`, ventas por material | `test_material_detail_*`, carga válida/inválida | tabla jerárquica expandible |
| HU-02 | SDD: catálogo y ventas por canal | canal configurado, desconocido y totales facturados | gráfica, resumen y configuración |
| HU-03 | PRD: menú fijo | contrato DOM sin `draggable` ni orden almacenado | menú sin controles de arrastre |
| HU-04 | SDD: rendimiento | facturación, meta, conversión, ticket, pendientes y consistencia | panel gerencial con periodo |
| HU-05 | API de cotizaciones | resolución histórica por nombre y filtro de huérfanos | opción `Asesor sin vincular` |
| HU-06 | filtros de fecha existentes | contrato DOM y fecha comercial configurada | Hoy/Este mes/Todas |
| HU-07 | `cotizacion_comentarios` | alta, edición, autoría, permiso y preservación del campo legado | modal de historial y edición |
| HU-08 | cruce SKU-promoción | exactitud, vigencia, caducidad y ausencia de inferencia por descripción | distintivo y orden Kanban |
| HU-09 | normalizador de contacto | prioridad celular, respaldo teléfono y preservación | enlaces de correo, llamada y WhatsApp |

## Puertas de aceptación

1. Migración `upgrade` y `downgrade` generan SQL PostgreSQL válido.
2. Suite Python completa verde.
3. Sintaxis JavaScript, contrato DOM y carga en navegador verdes.
4. `git diff --check` sin errores.
5. Permisos cubiertos para gerencia, vendedor, jerarquía y soporte.
6. Totales analíticos reconciliados y calculados sin LLM.

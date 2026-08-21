# Documento de Requerimientos del Producto (PRD) - CRM Inteligente con Gestión Agéntica

**Versión:** 2.0 (Actualizada post-auditoría integral)  
**Metodología:** Spec-Driven Development (SDD / SBD) & Test-Driven Development (TDD)  
**Framework de Dirección:** Humanio CEO (*Contexto, Ecosistema, Orquestación*)  
**Estado:** Producción Activa / Arquitectura Consolidada

---

## 1. Introducción y Visión General

El Sistema de Gestión de Relaciones con el Cliente (**CRM Kuroda**) es una plataforma comercial inteligente de alto rendimiento diseñada para potenciar la fuerza de ventas mediante automatización agéntica, integración de datos transaccionales del ERP SAP (reportes `VA05`, `VL06O`), control de inventario estratificado (`ABC+F`), sobrepedidos, promociones vigentes, analítica comercial y acompañamiento conductual basado en la metodología *La Ligera Ventaja* (The Slight Edge).

---

## 2. Objetivos Principales del Sistema

1. **Acompañamiento y Coaching Agéntico:** Proveer seguimiento diario automatizado a cada vendedor, planificador de disciplinas constantes y retroalimentación inteligente de metas.
2. **Eficiencia en Cotizaciones y Facturación:** Acelerar el ciclo de presupuestos, sincronización de facturas emitidas y análisis de causas raíz de ventas perdidas.
3. **Control Comercial Integral (Inventario y Sobrepedidos):** Visibilidad transparente de inventario disponible por sucursal (`ABC+F`), clasificación operativa de pedidos sobre demanda y entregas pendientes.
4. **Gobierno de Datos y Seguridad (RBAC):** Control estricto de accesos por roles (`admin`, `gerente`, `vendedor`, `soporte`), jerarquías comerciales padre-hijo y protección total de secretos.

---

## 3. Arquitectura Tecnológica y Ecosistema

| Componente | Tecnología Seleccionada | Propósito / Rol |
| :--- | :--- | :--- |
| **Infraestructura VPS** | Railway VPS / Docker | Servidor de producción y ejecución de workers asíncronos. |
| **Base de Datos** | PostgreSQL + SQLAlchemy Async + Alembic | Persistencia relacional, migraciones automáticas auditadas. |
| **Backend REST** | Python 3.12+ / FastAPI | Endpoints REST asíncronos, validación Pydantic v2 y seguridad JWT. |
| **Ecosistema LLM** | OpenRouter (GPT-4o mini) & Google Gemini Flash | Orquestación agéntica multi-proveedor con reintentos exponenciales. |
| **Canal de Mensajería** | WhatsApp Cloud API (Meta) & Enlaces Directos `wa.me` | Notificaciones de supervisión, webhooks bidireccionales y enlaces rápidos. |
| **Frontend** | HTML5, CSS Nativo (Dark UIX), JavaScript Vanilla | Dashboard responsivo, filtros dinámicos, vista ejecutiva y de vendedor. |

---

## 4. Especificación Funcional de los Agentes de IA

### Agente 1: Definición y Análisis de Metas Comerciales
* **Rol:** Estructura cuotas comerciales mensuales y estratégicas por vendedor, sucursal y canal.
* **Entradas:** Historial de ventas, promociones activas y directrices corporativas.
* **Salidas:** JSON estructurado con `monto_objetivo`, `descripcion` y `kpis_clave`.

### Agente 2: Supervisor Virtual y Seguimiento WhatsApp
* **Rol:** Genera y despacha seguimientos matutinos personalizados con base en metas vigentes y cotizaciones abiertas.
* **Entradas:** Pipeline activo del vendedor y métricas diarias.
* **Salidas:** Mensajes profesionales enviados vía Meta Cloud API o enlaces formateados `wa.me`.

### Agente 3: Redactor de Propuestas Comerciales y Cotizaciones
* **Rol:** Redacta cotizaciones corporativas persuasivas garantizando exactitud matemática.
* **Regla Inmutable:** El total monetario se calcula determinísticamente en Python antes de invocar la redacción del LLM.

### Agente 4: Analista de Inteligencia de Negocios (Business Insights)
* **Rol:** Analiza cotizaciones ganadas, perdidas y pendientes para generar resúmenes ejecutivos mensuales y detección de causas raíz de pérdida.

### Agente 5: Coach de La Ligera Ventaja (Slight Edge)
* **Rol:** Conversación estructurada para calcular el embudo inverso de ventas, asignar puntos a disciplinas diarias e invocar herramientas estructuradas (`save_slight_edge_plan`).

---

## 5. Módulos Operativos del Ecosistema CRM Kuroda

1. **Autenticación y Seguridad:** JWT, hashing bcrypt y control de roles RBAC.
2. **Jerarquía Comercial:** Supervisión de vendedores padre sobre carteras de vendedores hijos.
3. **Cotizaciones y Facturación SAP:** Carga masiva de Excels, conciliación de facturas y venta perdida.
4. **Catálogo de Clientes:** Maestro unificado de más de 22,000 clientes con búsqueda por RFC, tipo de persona y filtros geográficos.
5. **Inventario ABC+F:** Control multi-sucursal y visibilidad configurada para vendedores.
6. **Sobrepedidos & Por Entregar:** Clasificación operativa de pedidos especiales y entregas pendientes.
7. **Promociones Activas:** Catálogo de precios promocionales vinculado al generador de metas.
8. **Asignaciones y Subastas:** Distribución equitativa de prospectos entre la fuerza de ventas.
9. **Analítica Comercial:** KPIs de cierre, ticket promedio, mapa de calor y tiempos de respuesta.
10. **La Ligera Ventaja:** Bitácora diaria de puntos, consistencia y dashboard de coordinación.

---

## 6. Políticas de Calidad, SBD y TDD

* **TDD Estricto:** Toda nueva regla o cálculo comercial debe respaldarse con pruebas unitarias en `pytest`.
* **Cero Secretos:** Credenciales inyectadas exclusivamente vía variables de entorno.
* **Zona Horaria Oficial:** Todas las métricas diarias y tareas programadas operan bajo `America/Mazatlan`.
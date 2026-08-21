# Plan de Arquitectura Técnica y Constitución del Proyecto (SBD / TDD)

**Versión:** 2.0 (Consolidada post-auditoría)  
**Metodología:** Spec-Based Development (SBD) & Test-Driven Development (TDD)  
**Marco Rector:** Humanio CEO (*Contexto, Ecosistema, Orquestación*)  
**Estado:** Arquitectura Técnica de Referencia Inmutable

---

## 1. Constitución del Proyecto (Reglas Inamovibles de Ingeniería)

1. **Inyección Segura y Cero Secretos:** Las credenciales de base de datos (`DATABASE_URL`), claves JWT (`SECRET_KEY`), tokens de Meta (`META_WHATSAPP_TOKEN`, `META_APP_SECRET`) y llaves LLM (`OPENROUTER_API_KEY`, `GEMINI_API_KEY`) se cargan exclusivamente mediante `pydantic-settings` desde variables de entorno.
2. **Tipado Estricto & Pydantic v2:** Todas las firmas de función, controladores y servicios deben utilizar Type Hints y modelos de Pydantic v2 con `ConfigDict(from_attributes=True)`.
3. **Cálculos Comerciales Deterministas:** Ningún cálculo aritmético de importes, subtotales, cuotas o porcentajes de cumplimiento se delega al LLM; todo cálculo se ejecuta de forma determinista en Python antes de invocar la redacción agéntica.
4. **Resiliencia Agéntica:** El servicio central de LLM (`app/agents/llm.py`) implementa reintentos con *exponential backoff* ante errores transitorios y soporte multi-proveedor desacoplado.
5. **Zona Horaria del Negocio:** Todas las fechas operativas, métricas comerciales y tareas de segundo plano se sincronizan con `settings.BUSINESS_TIMEZONE` (`America/Mazatlan`).

---

## 2. Estructura Modular del Proyecto

```text
crmkuroda/
├── app/
│   ├── __init__.py
│   ├── main.py                     # Ciclo de vida lifespan y registro de routers
│   ├── core/
│   │   ├── config.py               # Settings Pydantic v2 y variables de entorno
│   │   ├── database.py             # Engine SQLAlchemy async y SessionLocal
│   │   ├── security.py             # JWT, bcrypt y dependencias RBAC (RoleChecker)
│   │   └── scheduler.py            # Tareas programadas en background (APScheduler)
│   ├── models/                     # Modelos ORM SQLAlchemy
│   │   ├── usuario.py              # Usuarios y jerarquía padre-hijo
│   │   ├── cotizacion.py           # Cotizaciones y datos importados SAP
│   │   ├── cotizacion_detalle.py   # Items y comentarios de seguimiento
│   │   ├── meta.py                 # Metas operativas de agente
│   │   ├── meta_comercial.py       # Metas mensuales por vendedor/sucursal/canal
│   │   ├── cliente.py              # Catálogo maestro de clientes (22k+)
│   │   ├── cliente_asignacion.py   # Asignaciones y subastas comerciales
│   │   ├── inventario_abcf.py      # Inventario estratificado multi-sucursal
│   │   ├── sobrepedido.py          # Pedidos sobre demanda VA05/VL06O
│   │   ├── por_entregar.py         # Entregas pendientes
│   │   ├── promocion.py            # Promociones vigentes
│   │   ├── slight_edge.py          # Planes y bitácora de La Ligera Ventaja
│   │   ├── commercial_analytics.py # Snapshots y analítica de ventas
│   │   └── log_agente.py           # Trazabilidad y auditoría de IA
│   ├── schemas/                    # Contratos Pydantic v2
│   ├── services/                   # Lógica de negocio determinista (Jerarquías, Analytics, SAP)
│   ├── agents/                     # Servicios agénticos (Metas, Cotizaciones, WhatsApp, Slight Edge)
│   └── api/                        # Controladores REST FastAPI
│       ├── auth.py
│       └── v1/
├── static/                         # Frontend Web responsivo (Dark UIX, JS, CSS)
├── tests/                          # Suite de pruebas automatizadas con pytest (117+ tests)
├── alembic/                        # Migraciones versionadas de base de datos
├── requirements.txt                # Dependencias fijadas
└── Procfile                        # Comando de arranque para Railway VPS
```

---

## 3. Arquitectura del Modelo de Datos (PostgreSQL)

| Tabla | Clave Primaria | Propósito y Relaciones Clave |
| :--- | :---: | :--- |
| `usuarios` | UUID v4 | Usuarios, roles RBAC, código de vendedor y relación padre-hijo (`vendedor_padre_id`). |
| `clientes` | Integer | Catálogo general de clientes, RFC, razón social, contactos y geolocalización. |
| `cotizaciones` | UUID v4 | Cabecera de cotizaciones, totales calculados, folios y trazabilidad de facturas SAP. |
| `cotizaciones_items` | UUID v4 | Detalle de partidas cotizadas con subtotales deterministas. |
| `cotizaciones_comentarios`| UUID v4 | Bitácora de seguimiento por vendedor/gerencia. |
| `metas_comerciales` | UUID v4 | Metas mensuales auditables por tipo (`general`, `vendedor`, `sucursal`) y canal. |
| `inventario_abcf` | Integer | Existencias por sucursal, proveedor, rotación ABC+F y visibilidad. |
| `sobrepedidos` | Integer | Pedidos sobre demanda y seguimiento de documentos SAP. |
| `por_entregar` | Integer | Pedidos con estatus de entrega y almacén de origen. |
| `slight_edge_plans` | UUID v4 | Objetivos financieros, ticket promedio y disciplinas de consistencia diaria. |
| `slight_edge_logs` | UUID v4 | Registro diario de actividades, puntos acumulados y reflexiones. |
| `logs_agentes` | Integer | Auditoría de prompts y respuestas de IA. |

---

## 4. Pipeline de Despliegue Continuo (CI/CD)

1. **Validación Local / TDD:** Ejecución obligatoria de `pytest` (`117 passed`).
2. **Push a GitHub (`main`):** Disparo de webhook de despliegue en Railway.
3. **Compilación Railway:** Construcción de contenedor Docker / entorno virtual Python.
4. **Lifespan Startup:** Ejecución automatizada de `alembic upgrade head`, sincronización DDL segura, siembra controlada condicional e inicio del scheduler en `America/Mazatlan`.
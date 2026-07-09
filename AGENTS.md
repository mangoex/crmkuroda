# AGENTS.md - CRM Kuroda

## Perfil de Miguel / Humanio

Miguel Gonzalez es facilitador de inteligencia artificial empresarial y dirige Humanio (humanio.digital), con el eslogan "Potenciando Humanos". Su modelo de trabajo es CEO: Contexto, Ecosistema y Orquestacion.

Humanio se enfoca en capacitacion en IA, consultoria, automatizaciones y creacion de agentes de IA. En este repositorio conviene explicar decisiones con enfoque practico de negocio, adopcion por equipos y resultados operativos, no solo como cambios tecnicos aislados.

## Contexto del proyecto

Repositorio: `mangoex/crmkuroda.git`

Carpeta local real del repo: `C:\Users\Miguel Gonzalez\Downloads\CRMK\crmkuroda`

CRM Kuroda es un CRM inteligente para equipos comerciales. Combina gestion de vendedores, metas, cotizaciones, seguimiento, carga de Excel, dashboards y agentes de IA para apoyar coordinacion comercial.

La aplicacion usa:

- Backend Python con FastAPI.
- SQLAlchemy async y Alembic para base de datos.
- PostgreSQL en produccion, con `DATABASE_URL` inyectado por entorno.
- Frontend estatico en `static/index.html`, `static/app.js` y `static/style.css`.
- Despliegue pensado para Railway con `Procfile`.
- OpenRouter como proveedor LLM mediante `OPENROUTER_API_KEY` y `OPENROUTER_MODEL`.

## Modulos principales

- Autenticacion y roles: `app/api/auth.py`, `app/core/security.py`, modelo `Usuario`.
- Vendedores: gestion de usuarios comerciales y datos de vendedor.
- Cotizaciones: carga Excel, cotizaciones manuales, cotizaciones generadas por IA, factura, venta perdida y comentarios.
- Promociones: carga Excel de promociones, filtros, KPIs y visualizacion en frontend.
- Inventario ABC+F: carga Excel multihoja, filtros por sucursal/ABC/proveedor/busqueda y control de visibilidad para vendedores.
- La Ligera Ventaja / Slight Edge: coach conversacional, plan diario, bitacora de actividades, dashboard de coordinador y recomendaciones de IA.
- Asignacion de clientes: clientes disponibles, asignacion directa, subastas entre vendedores y resolucion.
- Analisis: agente de insights comerciales sobre cotizaciones ganadas/perdidas/pendientes.
- WhatsApp/webhooks: endpoints e intencion de integracion con Meta/WhatsApp, pero revisar implementacion real antes de asumir produccion activa.

## Reglas de trabajo en este repo

- Antes de modificar, revisar `git status --short --branch` y proteger cambios locales existentes.
- No subir ni commitear bases locales, Excels, archivos de prueba o scripts temporales salvo instruccion explicita.
- La carpeta raiz `C:\Users\Miguel Gonzalez\Downloads\CRMK` no es el repo; trabajar dentro de `crmkuroda`.
- El remoto `origin/main` puede estar mas avanzado que la copia local. Si hay cambios locales, no hacer `pull` automatico sin revisar conflictos.
- Preferir cambios pequenos, deterministas y alineados con el patron actual.
- Si el cambio afecta UI, revisar tanto `static/index.html` como `static/app.js` y `static/style.css`.
- Si el cambio afecta datos o Excel, inspeccionar primero columnas reales y modelos/migraciones relacionadas.
- Si el cambio afecta permisos, validar comportamiento por rol: `admin`, `gerente`, `vendedor`.
- Si el cambio toca calculos comerciales, mantener calculos deterministicos en codigo; no delegar matematicas criticas al LLM.
- No colocar credenciales reales en el repo. Usar variables de entorno.

## Notas tecnicas importantes

- `app/main.py` ejecuta `python -m alembic upgrade head` al iniciar y tambien llama `Base.metadata.create_all`; revisar con cuidado si se cambia arranque o migraciones.
- Hay credenciales por defecto para seed local (`admin@kuroda.com` / `admin123`) en `app/main.py`; tratarlas como dato de desarrollo y no como secreto de produccion.
- `app/core/config.py` contiene valores fallback, incluidos `SECRET_KEY` y `DATABASE_URL`; produccion debe depender de variables de entorno.
- `app/agents/llm.py` llama a OpenRouter y expone alias `call_gemini` por compatibilidad historica.
- `app/agents/cotizaciones_agent.py` calcula totales en Python antes de pedir redaccion al LLM; preservar ese patron.
- `static/app.js` concentra mucha logica de UI. Buscar funciones existentes antes de crear una nueva abstraccion.

## Estado observado el 2026-07-09

- **Sincronización con GitHub:** La rama local `main` se encuentra completamente al día y sincronizada con `origin/main`. Los 15 commits remotos previos (que incluyen rediseños de la interfaz de vendedor, mapa de calor, controles de carga de inventario/promociones, motivos de venta perdida, factura en cotizaciones y búsquedas visuales) se han integrado con éxito.
- **Cambios locales y archivos sin seguimiento:**
  - La copia local de `static/app.js` está limpia y sin modificaciones pendientes frente al repositorio remoto.
  - El archivo `update_inv.py` permanece en el directorio como archivo sin seguimiento (untracked). Contiene la lógica preliminar para ordenar y paginar el inventario, cuyos cambios ya están aplicados y confirmados en el repositorio oficial (`static/index.html` y `static/app.js`).
- **Estado de la carpeta raíz del proyecto (`C:\Users\Miguel Gonzalez\Downloads\CRMK`):** Además del repositorio `crmkuroda`, contiene los archivos Excel de entrada (`Cotizaciones`, `Inventario`, `Promociones`) y la documentación del PRD y Plan de Arquitectura.

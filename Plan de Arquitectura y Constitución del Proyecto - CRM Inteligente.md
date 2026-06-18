Plan de Arquitectura Técnica y Constitución del Proyecto (SDD)

Este documento formaliza la arquitectura del sistema, la configuración de la infraestructura y el diseño técnico modular para el nuevo CRM Inteligente Agéntico. Actúa como el mapa técnico de ingeniería inmutable (System Constitution) para guiar la codificación automática con el modelo 3.5 Flash dentro del entorno Antigravity de manera precisa y determinista.

1. Constitución del Proyecto (Reglas Inamovibles de Codificación)

El Agente de IA (3.5 Flash) debe adherirse estrictamente a los siguientes principios técnicos de desarrollo durante las etapas de generación de código:

Inyección Segura de Dependencias: Queda estrictamente prohibido escribir credenciales de base de datos, API tokens de Meta o llaves de cifrado en texto plano. Se debe emplear de manera exclusiva la librería pydantic-settings para leer la configuración desde las variables de entorno inyectadas por Railway.

Tipado Estricto de Datos: Todas las firmas de funciones y controladores de ruta (endpoints) en FastAPI deben utilizar Type Hints de Python y esquemas de validación basados en Pydantic v2.

Aislamiento de Agentes: Los 3 agentes de IA deben ser diseñados como servicios desacoplados e independientes (patrón Service Layer). Ningún agente debe depender directamente del estado de memoria de otro; toda comunicación e intercambio de datos debe realizarse a través de la base de datos PostgreSQL.



2. Estructura de Directorios del Proyecto

Para garantizar la modularidad y el correcto puente de despliegue continuo desde GitHub hacia Railway, se implementará la siguiente estructura de archivos estándar de FastAPI:

crm_agentico/├── app/│   ├── __init__.py│   ├── main.py                 # Punto de entrada de la aplicación FastAPI│   ├── core/│   │   ├── config.py           # Configuración central y variables de entorno│   │   ├── database.py         # Conexión asíncrona a PostgreSQL (SQLAlchemy)│   │   └── security.py         # Autenticación, JWT y control de accesos (RBAC)│   ├── models/                 # Modelos ORM de SQLAlchemy│   │   ├── usuario.py│   │   ├── meta.py│   │   └── cotizacion.py│   ├── schemas/                # Esquemas de validación Pydantic│   │   ├── usuario.py│   │   ├── meta.py│   │   └── cotizacion.py│   ├── agents/                 # Lógica de prompts y orquestación de IA│   │   ├── metas_agent.py│   │   ├── seguimiento_agent.py│   │   └── cotizaciones_agent.py│   └── api/                    # Capa de controladores y rutas REST│       ├── auth.py             # Login, registro y validación de tokens│       └── v1/│           ├── vendedores.py│           ├── metas.py│           └── webhooks.py     # Integración con Meta Tech Provider (WhatsApp)├── requirements.txt            # Dependencias del proyecto└── Procfile                    # Comando de arranque para la VPS de Railway



3. Diseño y Modelado de la Base de Datos (PostgreSQL)

A continuación se detalla el esquema relacional básico indispensable para soportar el control de accesos por roles (RBAC) y la persistencia de las actividades de los agentes:

Tabla

Campos Principales

Tipo de Dato

Descripción y Restricciones

 

usuarios

id, email, hashed_password, rol, telefono_whatsapp

UUID, VARCHAR, VARCHAR, VARCHAR, VARCHAR

Soporta roles 'admin', 'gerente' y 'vendedor'. Telefono se usa para vinculación con WhatsApp.

metas

id, vendedor_id, descripcion, monto_objetivo, fecha_inicio, fecha_limite, estado

UUID, UUID (FK), TEXT, NUMERIC, DATE, DATE, VARCHAR

Almacena los objetivos definidos de manera automatizada por el Agente 1.

cotizaciones

id, vendedor_id, cliente_nombre, datos_contacto, items, total, texto_propuesta

UUID, UUID (FK), VARCHAR, JSONB, JSONB, NUMERIC, TEXT

Contiene los presupuestos generados estructuradamente por el Agente 3.



4. Especificación Técnica de Orquestación Agéntica

Cada uno de los tres agentes de Inteligencia Artificial que ejecutará 3.5 Flash se conectará a la capa del backend mediante funciones de servicio dedicadas:

Agente 1: Analizador y Definidor de Metas

Mecanismo de Activación: Evento de backend ejecutado al inicio de cada mes o por solicitud explícita del Administrador desde el panel de control.

Estrategia de Prompting: System prompt estricto con formato JSON estructurado que evalúa el histórico del vendedor y genera un JSON con claves monto_objetivo, descripcion_metas y kpis_clave.

Agente 2: Monitor de Seguimiento Activo vía WhatsApp

Mecanismo de Activación: Tarea programada en segundo plano (Cron job o Background Tasks de FastAPI) ejecutada diariamente a horarios específicos.

Integración de Red: Envía payloads a la API de WhatsApp del Tech Provider de Meta. Procesa las respuestas entrantes de los vendedores a través del endpoint /api/v1/webhooks/whatsapp para actualizar estados o guardar notas de seguimiento en la base de datos.

Agente 3: Redactor de Propuestas Comerciales y Cotizaciones

Mecanismo de Activación: Petición POST del vendedor con payload JSON conteniendo especificaciones del cliente y requerimientos específicos.

Formato de Salida: Generación en texto plano o HTML limpio estructurado listo para enviarse por correo electrónico o convertirse en PDF, adjuntando un resumen formal de precios de manera matemática exacta.



5. Infraestructura, Despliegue Continuo y Configuración

El entorno operativo en Railway se configurará aislando el entorno productivo con las siguientes claves de entorno obligatorias que la aplicación requiere para arrancar:

# Configuración del Entorno de Producción (Railway VPS)DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbnameSECRET_KEY=clave_secreta_jwt_para_firmar_tokens_de_accesoACCESS_TOKEN_EXPIRE_MINUTES=60# Configuración de Integración con Meta APIMETA_WHATSAPP_TOKEN=token_proveedor_tecnologico_meta_whatsappMETA_PHONE_NUMBER_ID=identificador_de_linea_telefonica_comercialWHATSAPP_WEBHOOK_VERIFY_TOKEN=token_de_verificacion_para_registro# Configuración de Modelos de Inteligencia ArtificialLLM_API_KEY=credenciales_acceso_orquestador_antigravity

El flujo de integración continua (CI/CD) se activará automáticamente con cada git push exitoso en la rama main del repositorio de GitHub conectado, donde Railway compilará el entorno virtual de Python, instalará las dependencias de requirements.txt y levantará la API de FastAPI de forma inmediata a través del servidor Uvicorn.
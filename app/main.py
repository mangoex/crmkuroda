from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import engine, Base

# We will import these routers shortly
from app.api.auth import router as auth_router
from app.api.v1.vendedores import router as vendedores_router
from app.api.v1.metas import router as metas_router
from app.api.v1.cotizaciones import router as cotizaciones_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.analisis import router as analisis_router
from app.api.v1.slight_edge import router as slight_edge_router
from app.api.v1.companies import router as companies_router
from app.api.v1.asignaciones import router as asignaciones_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend del CRM Inteligente con Gestión Agéntica",
    version="1.0.0",
)

# CORS Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from sqlalchemy import text

# Auto create database tables on startup (convenient for Railway zero-config)
from app.core.scheduler import start_scheduler

@app.on_event("startup")
async def on_startup():
    # Ejecutar migraciones de Alembic de forma automática para mantener la BD siempre al día
    import asyncio
    proc = await asyncio.create_subprocess_shell("python -m alembic upgrade head")
    await proc.communicate()

    async with engine.begin() as conn:
        # Create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)
        
        # Note: Database migrations and schema updates are now managed by Alembic.

    # Crear administrador por defecto y empresa por defecto si no existen
    from app.core.database import SessionLocal
    from app.models.usuario import Usuario
    from app.models.company import Company
    from app.core.security import get_password_hash
    from sqlalchemy.future import select
    
    async with SessionLocal() as session:
        # Seed company
        res_comp = await session.execute(select(Company).filter(Company.code == "kuroda"))
        company = res_comp.scalars().first()
        if not company:
            default_company = Company(
                code="kuroda",
                name="Kuroda Inteligente",
                global_sales_target=0.0,
                global_goals="Directrices estratégicas predeterminadas de la empresa."
            )
            session.add(default_company)

        # Seed admin
        res_admin = await session.execute(select(Usuario).filter(Usuario.email == "admin@kuroda.com"))
        admin_user = res_admin.scalars().first()
        if not admin_user:
            nuevo_admin = Usuario(
                email="admin@kuroda.com",
                hashed_password=get_password_hash("admin123"),
                rol="admin",
                nombre_completo="Administrador General"
            )
            session.add(nuevo_admin)
            

        # Seed available clients if empty
        from app.models.cliente_asignacion import ClienteDisponible
        cli_count_res = await session.execute(select(ClienteDisponible))
        if not cli_count_res.scalars().first():
            dummy_clients = [
                ClienteDisponible(
                    nombre="Agropecuaria del Noroeste S.A.",
                    email="contacto@agronoroeste.com",
                    telefono="6677123456",
                    comentarios="Cliente interesado en tuberías de alta presión para riego.",
                    estado="disponible"
                ),
                ClienteDisponible(
                    nombre="Construcciones y Proyectos del Pacífico S.A.",
                    email="licitaciones@conspacifico.mx",
                    telefono="6699876543",
                    comentarios="Solicita cotización de válvulas industriales y conexiones de PVC.",
                    estado="disponible"
                ),
                ClienteDisponible(
                    nombre="Desarrolladora de Vivienda del Valle",
                    email="compras@viviendavalle.com",
                    telefono="6688112233",
                    comentarios="Proyecto habitacional en Los Mochis. Busca grifería y medidores.",
                    estado="disponible"
                ),
                ClienteDisponible(
                    nombre="Distribuidora Hidráulica del Golfo",
                    email="ventas@hidrogolfo.com",
                    telefono="6671098765",
                    comentarios="Mayorista local. Busca acuerdo de distribución de refacciones.",
                    estado="disponible"
                )
            ]
            for dc in dummy_clients:
                session.add(dc)

        await session.commit()

    # Iniciar el planificador de tareas en segundo plano
    start_scheduler()

# Standardized Error Handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err["loc"])
        errors.append(f"{loc}: {err['msg']}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Fallo en la validación de los datos enviados.",
            "details": errors
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the traceback in a real production app (omitted here for security)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Error interno del servidor. Por favor, contacte a soporte."
        }
    )

# Base healthcheck / API status endpoint
@app.get("/api/health", tags=["Health"])
async def api_health():
    return {
        "status": "success",
        "message": "Bienvenido al CRM Inteligente Kuroda API",
        "version": "1.0.0"
    }

# Serve Frontend Index at Root
@app.get("/", tags=["Frontend"])
async def root():
    return FileResponse("static/index.html")

# Register API Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(vendedores_router, prefix="/api/v1/vendedores", tags=["Vendedores"])
app.include_router(metas_router, prefix="/api/v1/metas", tags=["Metas"])
app.include_router(cotizaciones_router, prefix="/api/v1/cotizaciones", tags=["Cotizaciones"])
app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["Webhooks"])
app.include_router(analisis_router, prefix="/api/v1/analisis", tags=["Analisis"])
app.include_router(slight_edge_router, prefix="/api/slight-edge", tags=["La Ligera Ventaja"])
app.include_router(companies_router, prefix="/companies", tags=["Compañías / Empresas"])
app.include_router(asignaciones_router, prefix="/api/v1/asignaciones", tags=["Asignación de Clientes"])

# Mount Static Files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

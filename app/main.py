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
    async with engine.begin() as conn:
        # Create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)
        
        # Run column migrations if tables already exist
        await conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS codigo_vendedor VARCHAR;"))
        await conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nombre_completo VARCHAR;"))
        await conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS avatar VARCHAR;"))
        
        # Drop unique index/constraint for whatsapp phone numbers to allow multiple accounts to share phone number
        await conn.execute(text("DROP INDEX IF EXISTS ix_usuarios_telefono_whatsapp;"))
        await conn.execute(text("ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_telefono_whatsapp_key;"))
        
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS numero_cotizacion VARCHAR;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS fecha_registro DATE;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS canal VARCHAR;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS numero_factura VARCHAR;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS fecha_factura DATE;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS venta_perdida VARCHAR;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS comentarios TEXT;"))

        # Delete Lorena Peraza's Slight Edge data for testing reset
        try:
            res_user = await conn.execute(text("SELECT id FROM usuarios WHERE nombre_completo LIKE '%Lorena Peraza%';"))
            lorena_id = res_user.scalar()
            if lorena_id:
                await conn.execute(text("DELETE FROM slight_edge_plans WHERE user_id = :uid;"), {"uid": lorena_id})
                await conn.execute(text("DELETE FROM slight_edge_logs WHERE user_id = :uid;"), {"uid": lorena_id})
        except Exception:
            pass

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
        res = await session.execute(select(Usuario).filter(Usuario.email == "admin@kuroda.com"))
        admin_user = res.scalars().first()
        if not admin_user:
            nuevo_admin = Usuario(
                email="admin@kuroda.com",
                hashed_password=get_password_hash("admin123"),
                rol="admin",
                nombre_completo="Administrador General"
            )
            session.add(nuevo_admin)
        else:
            admin_user.hashed_password = get_password_hash("admin123")
            admin_user.rol = "admin"
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
    # Log the traceback in a real production app
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": f"Error interno del servidor: {str(exc)}"
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

# Mount Static Files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

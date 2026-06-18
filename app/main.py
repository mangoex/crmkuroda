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
        
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS numero_cotizacion VARCHAR;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS fecha_registro DATE;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS canal VARCHAR;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS numero_factura VARCHAR;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS fecha_factura DATE;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS venta_perdida VARCHAR;"))
        await conn.execute(text("ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS comentarios TEXT;"))

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

# Mount Static Files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

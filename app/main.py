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
from app.api.v1.promociones import router as promociones_router
from app.api.v1.inventario_abcf import router as inventario_abcf_router
from app.api.v1.sobrepedidos import router as sobrepedidos_router
from app.api.v1.por_entregar import router as por_entregar_router
from app.api.v1.actualizaciones_datos import router as actualizaciones_datos_router
from app.api.v1.commercial_analytics import router as commercial_analytics_router

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

        # Seed inventario_abcf if empty or zero cost
        from app.models.inventario_abcf import InventarioAbcf
        from sqlalchemy import func, delete
        inv_cost_res = await session.execute(select(func.sum(InventarioAbcf.costo_promedio_unitario)))
        sum_cost = inv_cost_res.scalar() or 0.0
        
        if sum_cost == 0.0:
            import os, openpyxl, unicodedata
            excel_path = os.path.join(os.path.dirname(__file__), "..", "Inventario MKS D.XLSX")
            if not os.path.exists(excel_path):
                excel_path = os.path.abspath("Inventario MKS D.XLSX")
            
            if os.path.exists(excel_path):
                try:
                    await session.execute(delete(InventarioAbcf))
                    wb = openpyxl.load_workbook(excel_path, read_only=True)
                    ws = wb.active
                    header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), ())
                    
                    def _norm(v):
                        text = unicodedata.normalize('NFKD', str(v or ''))
                        text = ''.join(c for c in text if not unicodedata.combining(c))
                        return ''.join(c for c in text.lower() if c.isalnum())
                        
                    headers = [_norm(val) for val in header_row]
                    
                    def _hidx(*aliases):
                        norm_aliases = {_norm(a) for a in aliases}
                        return next((i for i, h in enumerate(headers) if h in norm_aliases), None)
                        
                    idx_centro = _hidx("centro", "sucursal", "nombre centro")
                    idx_almacen = _hidx("almacen", "almacen origen")
                    idx_num_prov = _hidx("numero proveedor", "numero de proveedor")
                    idx_nom_prov = _hidx("nombre proveedor", "nombre del proveedor", "proveedor")
                    idx_abcf = _hidx("abc+f", "abcf", "d")
                    idx_cod_mat = _hidx("codigo material", "clave material", "sku")
                    idx_desc_mat = _hidx("descripcion material", "descripcion")
                    idx_cant_prop = _hidx("cantidad propia", "cant propia")
                    idx_consig = _hidx("existencia consignacion", "inv consig", "existencia en consignacion de proveedore")
                    idx_costo = _hidx("costo promedio unitario", "precio promedio", "costo promedio")
                    idx_importe = _hidx("importe inventario propio", "importe inv", "importe de inventario propio")
                    idx_ubic = _hidx("ubicacion")
                    idx_gpo = _hidx("grupo materiales")
                    idx_desc_gpo = _hidx("descripcion grupo materiales", "descrip gpo materiales")
                    
                    def _rval(r, i, fallback=None):
                        target = i if i is not None else fallback
                        return r[target] if target is not None and len(r) > target else None
                        
                    def _flt(v):
                        if v is None or v == "": return 0.0
                        if isinstance(v, (int, float)): return float(v)
                        try: return float(str(v).replace("$", "").replace(",", "").strip())
                        except: return 0.0

                    for row in ws.iter_rows(min_row=2, values_only=True):
                        if not row or not _rval(row, idx_centro, 0): continue
                        cp = _flt(_rval(row, idx_cant_prop, 7))
                        ec = _flt(_rval(row, idx_consig, 8))
                        if cp == 0.0 and ec == 0.0: continue
                        
                        inv_obj = InventarioAbcf(
                            nombre_centro=str(_rval(row, idx_centro, 0) or ''),
                            almacen=str(_rval(row, idx_almacen, 1) or ''),
                            numero_proveedor=str(_rval(row, idx_num_prov, 2) or ''),
                            nombre_proveedor=str(_rval(row, idx_nom_prov, 3) or ''),
                            abc_f=str(_rval(row, idx_abcf, 4) or ''),
                            codigo_material=str(_rval(row, idx_cod_mat, 5) or ''),
                            descripcion_material=str(_rval(row, idx_desc_mat, 6) or ''),
                            cantidad_propia=cp,
                            existencia_consignacion=ec,
                            costo_promedio_unitario=_flt(_rval(row, idx_costo, 14)),
                            importe_inventario_propio=_flt(_rval(row, idx_importe, 15)),
                            ubicacion=str(_rval(row, idx_ubic, 17) or ''),
                            grupo_materiales=str(_rval(row, idx_gpo, 18) or ''),
                            descrip_gpo_materiales=str(_rval(row, idx_desc_gpo, 19) or '')
                        )
                        session.add(inv_obj)
                    wb.close()
                except Exception as seed_err:
                    print(f"Error seeding inventario_abcf: {seed_err}")

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
app.include_router(promociones_router, prefix="/api/v1/promociones", tags=["Promociones"])
app.include_router(inventario_abcf_router, prefix="/api/v1/inventario-abcf", tags=["Inventario ABC+F"])
app.include_router(sobrepedidos_router, prefix="/api/v1/sobrepedidos", tags=["Sobrepedidos"])
app.include_router(por_entregar_router, prefix="/api/v1/por-entregar", tags=["Por Entregar"])
app.include_router(actualizaciones_datos_router, prefix="/api/v1/actualizaciones-datos", tags=["Actualizaciones de datos"])
app.include_router(commercial_analytics_router, prefix="/api/v1/analitica", tags=["Analítica comercial"])

# Mount Static Files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

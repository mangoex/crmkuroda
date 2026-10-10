from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, or_
import io
import openpyxl
from typing import Optional

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.inventario_abcf import InventarioAbcf
from app.models.promocion import Promocion
from app.models.cotizacion import Cotizacion
from app.models.usuario import Usuario
from app.services.actualizaciones_datos import registrar_actualizacion_datos

router = APIRouter()

require_admin = RoleChecker(["admin", "gerente", "compras"])


async def get_reference_pricing_catalog(db: AsyncSession) -> dict[str, float]:
    """
    Construye un catálogo consolidado de respaldo de precios {codigo_material_upper: precio}
    cruzando en orden de prioridad:
    1. Catálogo maestro embebido oficial (Inventario MKS D.XLSX).
    2. Registros vigentes de Promoción (precio_promocion o costo_promedio > 0).
    3. Histórico de Cotizaciones (precio_unitario en items JSON).
    4. Base de datos actual de InventarioAbcf (si ya tenía precios válidos).
    """
    catalog: dict[str, float] = {}

    # 1. Catálogo maestro oficial embebido (base de partida)
    try:
        from seed_inventario import get_master_catalog_prices
        master_prices = get_master_catalog_prices()
        if master_prices:
            catalog.update(master_prices)
    except Exception:
        pass

    # 2. Cotizaciones históricas
    try:
        quote_res = await db.execute(
            select(Cotizacion.items).where(Cotizacion.items.isnot(None))
        )
        for row in quote_res.all():
            items = row[0]
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict):
                        sku = str(it.get("producto") or it.get("codigo_material") or "").strip().upper()
                        p = float(it.get("precio_unitario") or 0.0)
                        if sku and p > 0:
                            catalog[sku] = p
    except Exception:
        pass

    # 3. Base de datos actual InventarioAbcf
    try:
        inv_res = await db.execute(
            select(InventarioAbcf.codigo_material, InventarioAbcf.costo_promedio_unitario).where(
                InventarioAbcf.costo_promedio_unitario.isnot(None),
                InventarioAbcf.costo_promedio_unitario > 0
            )
        )
        for row in inv_res.all():
            sku = str(row[0] or "").strip().upper()
            p = float(row[1] or 0.0)
            if sku and p > 0:
                catalog[sku] = p
    except Exception:
        pass

    # 4. Promociones vigentes (máxima prioridad de precio comercial)
    try:
        promo_res = await db.execute(
            select(Promocion.codigo_material, Promocion.precio_promocion, Promocion.costo_promedio).where(
                or_(Promocion.precio_promocion > 0, Promocion.costo_promedio > 0)
            )
        )
        for row in promo_res.all():
            sku = str(row[0] or "").strip().upper()
            p = float(row[1] or 0.0) or float(row[2] or 0.0)
            if sku and p > 0:
                catalog[sku] = p
    except Exception:
        pass

    return catalog


def _normalize_header(value) -> str:
    """Normaliza encabezados de Excel para tolerar acentos y cambios menores."""
    import unicodedata

    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return "".join(char for char in text.lower() if char.isalnum())


def _header_index(headers: list[str], *aliases: str) -> Optional[int]:
    normalized_aliases = {_normalize_header(alias) for alias in aliases}
    return next((index for index, header in enumerate(headers) if header in normalized_aliases), None)


def _row_value(row, index: Optional[int], fallback: Optional[int] = None):
    target = index if index is not None else fallback
    return row[target] if target is not None and len(row) > target else None


def _as_float(value, default=None):
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return float(value)
    val_str = str(value).replace("$", "").replace(",", "").strip()
    try:
        return float(val_str)
    except ValueError:
        return default


@router.get("/")
async def list_inventario(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InventarioAbcf))
    inventarios = result.scalars().all()
    if not inventarios:
        return {"status": "success", "data": []}

    # Auto-curación en caliente: si hay registros sin precio, resolverlos con el catálogo de referencia
    unpriced = [i for i in inventarios if not i.costo_promedio_unitario or i.costo_promedio_unitario <= 0]
    if unpriced:
        ref_catalog = await get_reference_pricing_catalog(db)
        repaired_any = False
        for i in unpriced:
            sku_key = str(i.codigo_material or "").strip().upper()
            if sku_key in ref_catalog:
                p = ref_catalog[sku_key]
                i.costo_promedio_unitario = p
                if (not i.importe_inventario_propio or i.importe_inventario_propio <= 0) and i.cantidad_propia and i.cantidad_propia > 0:
                    i.importe_inventario_propio = round(p * i.cantidad_propia, 2)
                if (not i.valor_consignacion_proveedor or i.valor_consignacion_proveedor <= 0) and i.existencia_consignacion and i.existencia_consignacion > 0:
                    i.valor_consignacion_proveedor = round(p * i.existencia_consignacion, 2)
                repaired_any = True
        if repaired_any:
            try:
                await db.commit()
            except Exception:
                pass

    return {"status": "success", "data": [i.to_dict() for i in inventarios]}

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_inventario(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    if not file.filename.endswith(".xlsx") and not file.filename.endswith(".XLSX"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")
    
    contents = await file.read()
    
    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
        # Pre-cargar catálogo de respaldo antes de modificar nada en base de datos
        reference_catalog = await get_reference_pricing_catalog(db)
        
        items_to_add = []
        seen_keys = set()
        
        for ws in wb.worksheets:
            if ws.sheet_state == 'hidden':
                continue

            headers = []
            indices = {}
            start_data_row = 2

            # Tolerar encabezados en filas 1 a 6 (en caso de títulos de reporte SAP previos)
            for cand_row_idx, cand_row in enumerate(ws.iter_rows(min_row=1, max_row=6, values_only=True), start=1):
                cand_headers = [_normalize_header(value) for value in cand_row]
                cand_cod = _header_index(
                    cand_headers,
                    "codigo material", "clave material", "codigo producto", "clave producto", "sku", "material", "articulo", "codigo"
                )
                cand_centro = _header_index(
                    cand_headers,
                    "centro", "sucursal", "centro distribucion", "nombre centro", "ce"
                )
                if cand_cod is not None and cand_centro is not None:
                    headers = cand_headers
                    start_data_row = cand_row_idx + 1
                    break

            if not headers:
                header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), ())
                headers = [_normalize_header(value) for value in header_row]
                start_data_row = 2

            indices = {
                "centro": _header_index(headers, "centro", "sucursal", "centro distribucion", "nombre centro", "ce", "planta"),
                "almacen": _header_index(headers, "almacen", "almacen origen"),
                "numero_proveedor": _header_index(headers, "numero proveedor", "codigo proveedor", "proveedor codigo", "numero de proveedor"),
                "nombre_proveedor": _header_index(headers, "nombre proveedor", "proveedor", "razon social proveedor", "nombre del proveedor"),
                # D representa el indicador ABC+Frecuencia de Venta, no la clave de material.
                "abc_f": _header_index(
                    headers,
                    "abc+f",
                    "abcf",
                    "codigo abcf",
                    "clasificacion abcf",
                    "indicador abc+frecuencia de venta",
                    "indicador abcf frecuencia de venta",
                    "d",
                ),
                "codigo_material": _header_index(headers, "codigo material", "clave material", "codigo producto", "clave producto", "sku", "material", "articulo", "codigo"),
                "descripcion_material": _header_index(headers, "descripcion del material", "descripcion material", "descripcion producto", "descripcion", "producto"),
                "cantidad_propia": _header_index(headers, "cantidad propia", "cant propia", "inventario disponible", "existencia propia", "disponible", "libre utilizacion", "libre utilización", "existencia", "stock"),
                "existencia_consignacion": _header_index(headers, "existencia consignacion", "inv consig", "inventario consignacion", "existencia en consignacion de proveedore", "existencia en consignacion de proveedores", "consignacion", "consignación", "stock consignacion"),
                "entregas_pendientes": _header_index(headers, "entregas pendientes"),
                "existencia_transito": _header_index(headers, "existencia transito", "transito"),
                "existencia_bloqueada": _header_index(headers, "existencia bloqueada", "bloqueada"),
                "existencia_control_calidad": _header_index(headers, "existencia control calidad", "control calidad"),
                "umb": _header_index(headers, "umb", "unidad medida", "unidad de medida base"),
                "costo_promedio_unitario": _header_index(
                    headers,
                    "precio venta",
                    "precio de venta",
                    "precio venta civa",
                    "precio venta con iva",
                    "precio venta neto",
                    "precio de venta civa",
                    "precio de venta con iva",
                    "precio lista",
                    "precio de lista",
                    "precio lista civa",
                    "precio lista con iva",
                    "precio unitario",
                    "precio unitario civa",
                    "precio unitario con iva",
                    "precio comercial",
                    "precio",
                    "precios",
                    "pvp",
                    "pvp civa",
                    "pvp con iva",
                    "costo promedio unitario",
                    "costo promedio unitario moneda de venta",
                    "costo unitario",
                    "costo unit",
                    "costo",
                    "costos",
                    "costo promedio",
                    "costo prom",
                    "costo reposicion",
                    "costo reposición",
                    "costo estandar",
                    "costo estándar",
                    "costo estandar promocion",
                    "precio promedio",
                    "precio prom",
                    "precio promocion",
                    "precio efectivo promocion",
                    "precio efectivo",
                    "precio base",
                    "precio sugerido",
                    "precio publico",
                    "precio público",
                    "precio mostrador",
                    "precio distribuidor",
                    "valor unitario",
                    "val unitario",
                    "val unit",
                    "p venta",
                    "p vta",
                    "precio vta",
                    "importe venta",
                    "importe unitario",
                    "val neto",
                    "valor neto",
                    "cto unit",
                    "cto unitario",
                    "precio ref",
                    "precio referencia",
                ),
                "importe_inventario_propio": _header_index(
                    headers,
                    "importe inventario propio",
                    "importe inv propio",
                    "importe inv",
                    "importe inventario",
                    "importe de inventario propio",
                    "importe propio",
                    "importe total",
                    "importe neto",
                    "importe",
                    "valor inventario",
                    "valor propio",
                    "val inventario",
                    "imp inventario",
                ),
                "valor_consignacion_proveedor": _header_index(
                    headers,
                    "valor consignacion proveedor",
                    "valor de consignacion proveedor",
                    "valor consignacion",
                    "valor de consignacion",
                    "importe consignacion",
                    "importe consignado",
                    "consignacion importe",
                    "valor consignado",
                ),
                "ubicacion": _header_index(headers, "ubicacion", "localizacion"),
                "grupo_materiales": _header_index(headers, "grupo materiales"),
                "descrip_gpo_materiales": _header_index(headers, "descripcion grupo materiales", "descrip gpo materiales"),
                "codigo_anterior_material": _header_index(headers, "codigo anterior material"),
                "abc": _header_index(headers, "indicador abc", "abc"),
                "fecha_ultimo_inventario": _header_index(headers, "fecha ultimo inventario", "fecha del ultimo inventario ciclico"),
            }

            if indices["codigo_material"] is None or indices["centro"] is None:
                continue

            iter_rows = ws.iter_rows(min_row=start_data_row, values_only=True)
            for row in iter_rows:
                if not row or not _row_value(row, indices["centro"], 0):
                    continue

                try:
                    c_propia = _as_float(_row_value(row, indices["cantidad_propia"], 7), 0.0)
                    e_consig = _as_float(_row_value(row, indices["existencia_consignacion"], 8), 0.0)
                    
                    if c_propia == 0.0 and e_consig == 0.0:
                        continue

                    centro_val = str(_row_value(row, indices["centro"], 0)) if _row_value(row, indices["centro"], 0) is not None else None
                    cod_mat = str(_row_value(row, indices["codigo_material"], 1)) if _row_value(row, indices["codigo_material"], 1) is not None else None
                    almacen_val = str(_row_value(row, indices["almacen"])) if _row_value(row, indices["almacen"]) is not None else None

                    dedup_key = (centro_val, almacen_val, cod_mat)
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)

                    c_unitario = _as_float(_row_value(row, indices["costo_promedio_unitario"], 14))
                    imp_propio = _as_float(_row_value(row, indices["importe_inventario_propio"], 15))
                    val_consig = _as_float(_row_value(row, indices["valor_consignacion_proveedor"], 16))

                    sku_key = str(cod_mat or "").strip().upper()

                    # Resolución y blindaje de precio unitario
                    if c_unitario is None or c_unitario <= 0.0:
                        if imp_propio and imp_propio > 0 and c_propia > 0:
                            c_unitario = round(imp_propio / c_propia, 2)
                        elif val_consig and val_consig > 0 and e_consig > 0:
                            c_unitario = round(val_consig / e_consig, 2)
                        elif sku_key in reference_catalog:
                            c_unitario = reference_catalog[sku_key]

                    # Auto-completar importes totales si vinieron en 0 o vacíos
                    if (imp_propio is None or imp_propio <= 0.0) and c_unitario and c_unitario > 0 and c_propia > 0:
                        imp_propio = round(c_unitario * c_propia, 2)
                    if (val_consig is None or val_consig <= 0.0) and c_unitario and c_unitario > 0 and e_consig > 0:
                        val_consig = round(c_unitario * e_consig, 2)
                        
                    inv = InventarioAbcf(
                        nombre_centro=centro_val,
                        almacen=almacen_val,
                        numero_proveedor=str(_row_value(row, indices["numero_proveedor"])) if _row_value(row, indices["numero_proveedor"]) is not None else None,
                        nombre_proveedor=str(_row_value(row, indices["nombre_proveedor"], 2)) if _row_value(row, indices["nombre_proveedor"], 2) is not None else None,
                        abc_f=str(_row_value(row, indices["abc_f"])) if _row_value(row, indices["abc_f"]) is not None else None,
                        codigo_material=cod_mat,
                        descripcion_material=str(_row_value(row, indices["descripcion_material"], 3)) if _row_value(row, indices["descripcion_material"], 3) is not None else None,
                        cantidad_propia=c_propia,
                        existencia_consignacion=e_consig,
                        entregas_pendientes=_as_float(_row_value(row, indices["entregas_pendientes"], 9)),
                        existencia_transito=_as_float(_row_value(row, indices["existencia_transito"], 10)),
                        existencia_bloqueada=_as_float(_row_value(row, indices["existencia_bloqueada"], 11)),
                        existencia_control_calidad=_as_float(_row_value(row, indices["existencia_control_calidad"], 12)),
                        umb=str(_row_value(row, indices["umb"], 13)) if _row_value(row, indices["umb"], 13) is not None else None,
                        costo_promedio_unitario=c_unitario,
                        importe_inventario_propio=imp_propio,
                        valor_consignacion_proveedor=val_consig,
                        ubicacion=str(_row_value(row, indices["ubicacion"], 17)) if _row_value(row, indices["ubicacion"], 17) is not None else None,
                        grupo_materiales=str(_row_value(row, indices["grupo_materiales"], 18)) if _row_value(row, indices["grupo_materiales"], 18) is not None else None,
                        descrip_gpo_materiales=str(_row_value(row, indices["descrip_gpo_materiales"], 19)) if _row_value(row, indices["descrip_gpo_materiales"], 19) is not None else None,
                        codigo_anterior_material=str(_row_value(row, indices["codigo_anterior_material"], 20)) if _row_value(row, indices["codigo_anterior_material"], 20) is not None else None,
                        abc=str(_row_value(row, indices["abc"], 21)) if _row_value(row, indices["abc"], 21) is not None else None,
                        fecha_ultimo_inventario=str(_row_value(row, indices["fecha_ultimo_inventario"], 22)) if _row_value(row, indices["fecha_ultimo_inventario"], 22) is not None else None
                    )
                    items_to_add.append(inv)
                except Exception as row_error:
                    print(f"Error parseando fila: {row_error}")
                    continue

        if not items_to_add:
            raise HTTPException(status_code=400, detail="No se encontraron registros válidos de inventario en el archivo.")

        # Reemplazo atómico seguro: solo ahora eliminamos los registros anteriores
        await db.execute(delete(InventarioAbcf))
        for inv in items_to_add:
            db.add(inv)
            
        await registrar_actualizacion_datos(db, "inventario-abcf", current_user.id)
        await db.commit()
        return {"status": "success", "message": f"Se han cargado {len(items_to_add)} registros de inventario exitosamente."}
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error general procesando archivo de inventario: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {str(e)}")


@router.post("/reparar-precios", status_code=status.HTTP_200_OK)
async def reparar_precios_endpoint(
    current_user: Usuario = Depends(require_admin)
):
    from seed_inventario import reparar_precios_inventario
    total = await reparar_precios_inventario()
    return {"status": "success", "message": f"Precios de Inventario D reparados exitosamente ({total} registros sincronizados con catálogo oficial)."}

import io
import os
import logging
import openpyxl
from sqlalchemy.future import select
from sqlalchemy import func, insert, delete
from app.core.database import SessionLocal, engine, Base
from app.models.inventario_abcf import InventarioAbcf
from app.models.actualizacion_datos import ActualizacionDatos
from app.api.v1.inventario_abcf import (
    _normalize_header,
    _header_index,
    _row_value,
    _as_float,
    _sort_worksheets_material_d_first,
    SALE_PRICE_ALIASES,
    UNIT_COST_ALIASES,
)

logger = logging.getLogger(__name__)

EXCEL_PATHS = [
    os.path.join(os.path.dirname(__file__), "Inventario MKS D.XLSX"),
    os.path.join(os.path.dirname(__file__), "..", "Inventario MKS D.XLSX"),
    os.path.join(os.path.dirname(__file__), "Inventario MKS al 29.06.26.XLSX"),
    os.path.join(os.path.dirname(__file__), "..", "Inventario MKS al 29.06.26.XLSX"),
    "Inventario MKS D.XLSX",
    "../Inventario MKS D.XLSX",
    "Inventario MKS al 29.06.26.XLSX",
    "../Inventario MKS al 29.06.26.XLSX",
]


def find_inventario_excel():
    for p in EXCEL_PATHS:
        abs_p = os.path.abspath(p)
        if os.path.exists(abs_p):
            return abs_p
    return None


_master_catalog_cache = None


def get_master_catalog_prices() -> dict[str, float]:
    """Retorna un mapa en caché {codigo_material_upper: precio} desde el catálogo maestro de inventario."""
    global _master_catalog_cache
    if _master_catalog_cache is not None:
        return _master_catalog_cache

    price_map = {}
    excel_path = find_inventario_excel()
    if excel_path and os.path.exists(excel_path):
        try:
            wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
            records = parse_inventario_rows_from_workbook(wb)
            for r in records:
                sku = str(r.get("codigo_material") or "").strip().upper()
                price = r.get("costo_promedio_unitario")
                if sku and price and price > 0 and sku not in price_map:
                    price_map[sku] = float(price)
        except Exception as e:
            logger.warning(f"No se pudo cargar catálogo maestro de precios desde Excel: {e}")

    _master_catalog_cache = price_map
    return price_map


def parse_inventario_rows_from_workbook(wb) -> list[dict]:
    """Extrae y parsea filas con precios y ubicaciones desde un libro openpyxl, priorizando hojas de Material D."""
    records = []
    seen_keys = set()
    sheet_price_map: dict[str, float] = {}

    ordered_sheets = _sort_worksheets_material_d_first(wb.worksheets)

    for ws in ordered_sheets:
        if ws.sheet_state == "hidden":
            continue

        headers = []
        start_data_row = 2

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

        precio_venta_idx = _header_index(headers, *SALE_PRICE_ALIASES)
        costo_unitario_idx = _header_index(headers, *UNIT_COST_ALIASES)

        indices = {
            "centro": _header_index(headers, "centro", "sucursal", "centro distribucion", "nombre centro", "ce", "planta"),
            "almacen": _header_index(headers, "almacen", "almacen origen"),
            "numero_proveedor": _header_index(headers, "numero proveedor", "codigo proveedor", "proveedor codigo", "numero de proveedor"),
            "nombre_proveedor": _header_index(headers, "nombre proveedor", "proveedor", "razon social proveedor", "nombre del proveedor"),
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
            "precio_venta": precio_venta_idx,
            "costo_unitario": costo_unitario_idx,
            "costo_promedio_unitario": precio_venta_idx if precio_venta_idx is not None else costo_unitario_idx,
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

        # Ignorar hojas que no tienen código ni descripción ni centro
        if indices["codigo_material"] is None or indices["centro"] is None:
            continue

        for row in ws.iter_rows(min_row=start_data_row, values_only=True):
            if not row or not _row_value(row, indices["centro"], 0):
                continue

            try:
                c_propia = _as_float(_row_value(row, indices["cantidad_propia"], 7), 0.0)
                e_consig = _as_float(_row_value(row, indices["existencia_consignacion"], 8), 0.0)

                if c_propia == 0.0 and e_consig == 0.0:
                    continue

                centro_val = str(_row_value(row, indices["centro"], 0)).strip() if _row_value(row, indices["centro"], 0) is not None else None
                cod_mat = str(_row_value(row, indices["codigo_material"], 1)).strip() if _row_value(row, indices["codigo_material"], 1) is not None else None
                almacen_val = str(_row_value(row, indices["almacen"])).strip() if _row_value(row, indices["almacen"]) is not None else None

                # Clave única para evitar duplicados entre hojas idénticas (prevalece Material D al procesarse primero)
                dedup_key = (centro_val, almacen_val, cod_mat)
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                p_venta_val = _as_float(_row_value(row, indices["precio_venta"])) if indices["precio_venta"] is not None else None
                c_costo_val = _as_float(_row_value(row, indices["costo_unitario"], 14))
                c_unitario = p_venta_val if (p_venta_val is not None and p_venta_val > 0) else c_costo_val

                imp_propio = _as_float(_row_value(row, indices["importe_inventario_propio"], 15))
                val_consig = _as_float(_row_value(row, indices["valor_consignacion_proveedor"], 16))
                sku_key = str(cod_mat or "").strip().upper()

                if c_unitario is None or c_unitario <= 0.0:
                    if imp_propio and imp_propio > 0 and c_propia > 0:
                        c_unitario = round(imp_propio / c_propia, 2)
                    elif val_consig and val_consig > 0 and e_consig > 0:
                        c_unitario = round(val_consig / e_consig, 2)
                    elif sku_key in sheet_price_map:
                        c_unitario = sheet_price_map[sku_key]

                if sku_key and c_unitario and c_unitario > 0 and sku_key not in sheet_price_map:
                    sheet_price_map[sku_key] = c_unitario

                if (imp_propio is None or imp_propio == 0.0) and c_unitario and c_unitario > 0 and c_propia > 0:
                    imp_propio = round(c_unitario * c_propia, 2)
                if (val_consig is None or val_consig == 0.0) and c_unitario and c_unitario > 0 and e_consig > 0:
                    val_consig = round(c_unitario * e_consig, 2)

                records.append({
                    "nombre_centro": centro_val,
                    "almacen": almacen_val,
                    "numero_proveedor": str(_row_value(row, indices["numero_proveedor"])) if _row_value(row, indices["numero_proveedor"]) is not None else None,
                    "nombre_proveedor": str(_row_value(row, indices["nombre_proveedor"], 2)) if _row_value(row, indices["nombre_proveedor"], 2) is not None else None,
                    "abc_f": str(_row_value(row, indices["abc_f"])) if _row_value(row, indices["abc_f"]) is not None else None,
                    "codigo_material": cod_mat,
                    "descripcion_material": str(_row_value(row, indices["descripcion_material"], 3)) if _row_value(row, indices["descripcion_material"], 3) is not None else None,
                    "cantidad_propia": c_propia,
                    "existencia_consignacion": e_consig,
                    "entregas_pendientes": _as_float(_row_value(row, indices["entregas_pendientes"], 9)),
                    "existencia_transito": _as_float(_row_value(row, indices["existencia_transito"], 10)),
                    "existencia_bloqueada": _as_float(_row_value(row, indices["existencia_bloqueada"], 11)),
                    "existencia_control_calidad": _as_float(_row_value(row, indices["existencia_control_calidad"], 12)),
                    "umb": str(_row_value(row, indices["umb"], 13)) if _row_value(row, indices["umb"], 13) is not None else None,
                    "costo_promedio_unitario": c_unitario,
                    "importe_inventario_propio": imp_propio,
                    "valor_consignacion_proveedor": val_consig,
                    "ubicacion": str(_row_value(row, indices["ubicacion"], 17)) if _row_value(row, indices["ubicacion"], 17) is not None else None,
                    "grupo_materiales": str(_row_value(row, indices["grupo_materiales"], 18)) if _row_value(row, indices["grupo_materiales"], 18) is not None else None,
                    "descrip_gpo_materiales": str(_row_value(row, indices["descrip_gpo_materiales"], 19)) if _row_value(row, indices["descrip_gpo_materiales"], 19) is not None else None,
                    "codigo_anterior_material": str(_row_value(row, indices["codigo_anterior_material"], 20)) if _row_value(row, indices["codigo_anterior_material"], 20) is not None else None,
                    "abc": str(_row_value(row, indices["abc"], 21)) if _row_value(row, indices["abc"], 21) is not None else None,
                    "fecha_ultimo_inventario": str(_row_value(row, indices["fecha_ultimo_inventario"], 22)) if _row_value(row, indices["fecha_ultimo_inventario"], 22) is not None else None,
                })
            except Exception as e:
                continue

    return records


async def seed_inventario_from_excel(force=False):
    """Siembra o repara automáticamente el inventario ABC+F con precios y ubicaciones válidas."""
    excel_file = find_inventario_excel()
    if not excel_file:
        logger.info("No se encontró archivo Excel de Inventario para siembra automática.")
        return 0

    async with SessionLocal() as session:
        if not force:
            count_res = await session.execute(select(func.count(InventarioAbcf.id)))
            existing_count = count_res.scalar() or 0

            # Verificar si existe una carga manual realizada por un usuario (para no sobreescribirla al reiniciar)
            has_user_upload = False
            try:
                upload_record = await session.get(ActualizacionDatos, "inventario-abcf")
                if upload_record is not None:
                    has_user_upload = True
            except Exception:
                pass

            if existing_count > 0:
                valid_price_res = await session.execute(
                    select(func.count(InventarioAbcf.id)).where(
                        InventarioAbcf.costo_promedio_unitario.isnot(None),
                        InventarioAbcf.costo_promedio_unitario > 0
                    )
                )
                valid_price_count = valid_price_res.scalar() or 0

                # Si un usuario ya subió su archivo manualmente y tiene precios válidos, respetar su carga sin importar el tamaño
                if has_user_upload and valid_price_count > 0:
                    logger.info(
                        f"Inventario ABC+F cargado por usuario ({existing_count} registros, {valid_price_count} con precio). Se respeta carga manual."
                    )
                    return existing_count

                # Si el inventario tiene al menos 2000 precios válidos o más del 90% con precio, se omite siembra
                if valid_price_count >= 2000 or (existing_count > 0 and (valid_price_count / existing_count) >= 0.90):
                    logger.info(f"Inventario ABC+F ya contiene {existing_count} registros ({valid_price_count} con precio válido). Se omite siembra.")
                    return existing_count
                
                logger.info(f"Inventario existente contiene {existing_count} registros pero solo {valid_price_count} con precio válido. Reparando y re-sembrando automáticamente...")

        print(f"Cargando Inventario ABC+F desde: {excel_file}")
        wb = openpyxl.load_workbook(excel_file, read_only=True, data_only=True)
        records = parse_inventario_rows_from_workbook(wb)

        if not records:
            return 0

        # Eliminar registros anteriores si se está forzando o reparando
        await session.execute(delete(InventarioAbcf))
        await session.commit()

        batch_size = 1000
        total_inserted = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            await session.execute(insert(InventarioAbcf), batch)
            await session.commit()
            total_inserted += len(batch)

        print(f"¡Siembra de Inventario ABC+F completada! ({total_inserted} registros con precios y ubicaciones)")
        return total_inserted


async def reparar_precios_inventario():
    """Actualiza y garantiza la presencia de precios oficiales en Inventario D."""
    return await seed_inventario_from_excel(force=True)

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
    2. Histórico de Cotizaciones (precio_unitario en items JSON).
    3. Costo promedio de Promociones (como respaldo contable si no hay costo en inventario).
    4. Base de datos actual de InventarioAbcf (si ya tenía precios válidos, máxima prioridad de inventario).
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

    # 3. Costo promedio de Promociones (respaldo si el inventario viene en 0)
    try:
        promo_res = await db.execute(
            select(Promocion.codigo_material, Promocion.precio_promocion, Promocion.costo_promedio).where(
                or_(Promocion.precio_promocion > 0, Promocion.costo_promedio > 0)
            )
        )
        for row in promo_res.all():
            sku = str(row[0] or "").strip().upper()
            # Preferir costo_promedio para respaldo de inventario; usar precio_promocion solo si no hay otro dato
            p = float(row[2] or 0.0) or float(row[1] or 0.0)
            if sku and p > 0:
                catalog[sku] = p
    except Exception:
        pass

    # 4. Base de datos actual InventarioAbcf (máxima prioridad de inventario real)
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

    return catalog


def _normalize_header(value) -> str:
    """Normaliza encabezados de Excel para tolerar acentos y cambios menores."""
    import unicodedata

    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return "".join(char for char in text.lower() if char.isalnum())


def _header_index(headers: list[str], *aliases: str) -> Optional[int]:
    """
    Busca el índice de una columna respetando el orden de prioridad de `aliases`
    (primero evalúa el primer alias contra todas las columnas, luego el segundo, etc.).
    """
    for alias in aliases:
        norm_alias = _normalize_header(alias)
        for index, header in enumerate(headers):
            if header == norm_alias:
                return index
    return None


def _find_flexible_price_index(headers: list[str], aliases: tuple[str, ...], keywords: tuple[str, ...], exclude: tuple[str, ...] = ()) -> Optional[int]:
    """Busca primero por alias exacto en prioridad y luego por coincidencia parcial de palabras clave."""
    exact_idx = _header_index(headers, *aliases)
    if exact_idx is not None:
        return exact_idx
    for kw in keywords:
        norm_kw = _normalize_header(kw)
        for index, header in enumerate(headers):
            if not header:
                continue
            if any(_normalize_header(ex) in header for ex in exclude):
                continue
            if norm_kw in header:
                return index
    return None


def _sort_worksheets_material_d_first(worksheets: list):
    """
    Ordena las hojas del libro de Excel dando prioridad a las pestañas específicas
    de 'Material D' (ej. 'Material D Ck Matriz.', 'Material D Ck Conquista', etc.)
    sobre las hojas generales ('Sheet1', 'Inventario MKS').
    Así, al deduplicar por (centro, almacen, codigo_material), prevalecen los precios
    y datos de las hojas de Material D.
    """
    def _sheet_priority(ws):
        title_norm = _normalize_header(getattr(ws, "title", ""))
        if "materiald" in title_norm or "matd" in title_norm or "inventariod" in title_norm:
            return 0
        return 1

    return sorted(worksheets, key=_sheet_priority)


def _row_value(row, index: Optional[int], fallback: Optional[int] = None):
    target = index if index is not None else fallback
    return row[target] if target is not None and len(row) > target else None


def _clean_code(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text or None


def _as_float(value, default=None):
    import re

    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return float(value)
    val_str = str(value).replace(",", "").strip()
    if val_str.startswith("="):
        return default
    try:
        return float(val_str.replace("$", "").strip())
    except ValueError:
        match = re.search(r"[-+]?\d+(?:\.\d+)?", val_str)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return default
        return default


def _col_letters_to_index(col_str: str) -> int:
    idx = 0
    for ch in col_str.upper():
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def _safe_eval_arithmetic(expr: str) -> Optional[float]:
    import ast
    import operator as op

    operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.USub: op.neg,
        ast.UAdd: op.pos,
    }

    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in operators:
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in operators:
            return operators[type(node.op)](_eval(node.operand))
        raise ValueError("Unsupported expression")

    try:
        tree = ast.parse(expr, mode="eval")
        return float(_eval(tree.body))
    except Exception:
        return None


def _resolve_formula_cell(formula_val, ws_data_rows: Optional[list], current_row_offset: int, visited: Optional[set] = None) -> Optional[float]:
    """
    Evalúa de forma segura fórmulas aritméticas simples en Excel (ej. '=O2*1.16', '=P2/H2')
    cuando openpyxl(data_only=True) devuelve None por falta de caché de fórmula.
    """
    import re

    if formula_val is None:
        return None
    if not isinstance(formula_val, str) or not formula_val.strip().startswith("="):
        return _as_float(formula_val)

    expr = formula_val.strip()[1:].strip()
    if visited is None:
        visited = set()

    def _replace_ref(match):
        col_letters = match.group(1)
        row_num = int(match.group(2))
        col_idx = _col_letters_to_index(col_letters)
        key = (row_num, col_idx)
        if key in visited or ws_data_rows is None:
            return "0"
        row_pos = row_num - 1
        if 0 <= row_pos < len(ws_data_rows) and col_idx < len(ws_data_rows[row_pos]):
            cell_v = ws_data_rows[row_pos][col_idx]
            val = _as_float(cell_v)
            if val is not None:
                return str(val)
        return "0"

    # Solo soportar fórmulas aritméticas puras con referencias de celda
    if not re.fullmatch(r"[\s0-9.+\-*/()\$A-Za-z]+", expr):
        return None
    # Rechazar llamadas a funciones (letras seguidas de '(') excepto si no hay
    if re.search(r"[A-Za-z_]+\s*\(", expr):
        return None

    resolved_expr = re.sub(r"\$?([A-Za-z]{1,3})\$?(\d+)", _replace_ref, expr)
    return _safe_eval_arithmetic(resolved_expr)


SALE_PRICE_ALIASES = (
    "precio venta",
    "precio de venta",
    "precio venta civa",
    "precio venta con iva",
    "precio venta neto",
    "precio de venta civa",
    "precio de venta con iva",
    "precio venta publico",
    "precio de venta publico",
    "precio publico civa",
    "precio publico con iva",
    "precio civa",
    "precio con iva",
    "precio material d",
    "precio d",
    "precio remate",
    "precio remate civa",
    "precio liquidacion",
    "precio liquidación",
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
    "precio ref",
    "precio referencia",
)

UNIT_COST_ALIASES = (
    "costo promedio unitario",
    "costo promedio unitario moneda de venta",
    "costo promedio unitario civa",
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
    "cto unit",
    "cto unitario",
)


@router.get("/")
async def list_inventario(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InventarioAbcf))
    inventarios = result.scalars().all()
    if not inventarios:
        return {"status": "success", "data": []}

    # Auto-curación en caliente: si hay registros sin precio, resolverlos primero desde sus propios importes
    # y solo en última instancia con el catálogo de referencia
    unpriced = [i for i in inventarios if not i.costo_promedio_unitario or i.costo_promedio_unitario <= 0]
    if unpriced:
        ref_catalog = None
        repaired_any = False
        for i in unpriced:
            c_propia = float(i.cantidad_propia or 0.0)
            e_consig = float(i.existencia_consignacion or 0.0)
            imp_propio = float(i.importe_inventario_propio or 0.0)
            val_consig = float(i.valor_consignacion_proveedor or 0.0)

            resolved_p = None
            if imp_propio > 0 and c_propia > 0:
                resolved_p = round(imp_propio / c_propia, 2)
            elif val_consig > 0 and e_consig > 0:
                resolved_p = round(val_consig / e_consig, 2)
            else:
                if ref_catalog is None:
                    ref_catalog = await get_reference_pricing_catalog(db)
                sku_key = str(i.codigo_material or "").strip().upper()
                if sku_key in ref_catalog:
                    resolved_p = ref_catalog[sku_key]

            if resolved_p and resolved_p > 0:
                i.costo_promedio_unitario = resolved_p
                if (not i.importe_inventario_propio or i.importe_inventario_propio <= 0) and c_propia > 0:
                    i.importe_inventario_propio = round(resolved_p * c_propia, 2)
                if (not i.valor_consignacion_proveedor or i.valor_consignacion_proveedor <= 0) and e_consig > 0:
                    i.valor_consignacion_proveedor = round(resolved_p * e_consig, 2)
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
        wb_formulas = None
        # Pre-cargar catálogo de respaldo antes de modificar nada en base de datos
        reference_catalog = await get_reference_pricing_catalog(db)
        
        items_to_add = []
        seen_keys = set()
        sheet_price_map: dict[str, float] = {}
        detected_columns_summary: list[str] = []
        
        # Priorizar pestañas de Material D sobre hojas generales
        ordered_sheets = _sort_worksheets_material_d_first(wb.worksheets)
        
        for ws in ordered_sheets:
            if ws.sheet_state == 'hidden':
                continue

            raw_headers = []
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
                    raw_headers = [str(v or "").strip() for v in cand_row]
                    headers = cand_headers
                    start_data_row = cand_row_idx + 1
                    break

            if not headers:
                header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), ())
                raw_headers = [str(v or "").strip() for v in header_row]
                headers = [_normalize_header(value) for value in header_row]
                start_data_row = 2

            precio_venta_idx = _find_flexible_price_index(
                headers,
                SALE_PRICE_ALIASES,
                ("precioventa", "preciopublico", "precioremate", "preciod", "precio", "pvp"),
                exclude=("descuento",),
            )
            costo_unitario_idx = _find_flexible_price_index(
                headers,
                UNIT_COST_ALIASES,
                ("costopromedio", "costounitario"),
                exclude=("descuento",),
            )

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

            if indices["codigo_material"] is None or indices["centro"] is None:
                continue

            has_explicit_price_col = (
                indices["precio_venta"] is not None
                or indices["costo_unitario"] is not None
                or indices["importe_inventario_propio"] is not None
                or indices["valor_consignacion_proveedor"] is not None
            )

            chosen_col_idx = indices["precio_venta"] if indices["precio_venta"] is not None else indices["costo_unitario"]
            if chosen_col_idx is not None and chosen_col_idx < len(raw_headers):
                detected_columns_summary.append(f"{ws.title}: {raw_headers[chosen_col_idx]}")

            ws_all_rows = list(ws.iter_rows(min_row=1, values_only=True))
            ws_formula_rows = None

            for row_offset, row in enumerate(ws_all_rows[start_data_row - 1:], start=start_data_row - 1):
                if not row or not _row_value(row, indices["centro"], 0):
                    continue

                try:
                    c_propia = _as_float(_row_value(row, indices["cantidad_propia"], 7 if not has_explicit_price_col else None), 0.0)
                    e_consig = _as_float(_row_value(row, indices["existencia_consignacion"], 8 if not has_explicit_price_col else None), 0.0)
                    
                    if c_propia == 0.0 and e_consig == 0.0:
                        continue

                    centro_val = _clean_code(_row_value(row, indices["centro"], 0))
                    cod_mat = _clean_code(_row_value(row, indices["codigo_material"], 1))
                    almacen_val = _clean_code(_row_value(row, indices["almacen"]))

                    dedup_key = (centro_val, almacen_val, cod_mat)
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)

                    def _get_numeric_with_formula_fallback(col_idx: Optional[int], fallback_idx: Optional[int] = None) -> Optional[float]:
                        target_idx = col_idx if col_idx is not None else fallback_idx
                        if target_idx is None:
                            return None
                        raw_val = row[target_idx] if len(row) > target_idx else None
                        parsed = _as_float(raw_val)
                        if parsed is not None:
                            return parsed
                        if raw_val is None:
                            nonlocal wb_formulas, ws_formula_rows
                            if wb_formulas is None:
                                wb_formulas = openpyxl.load_workbook(io.BytesIO(contents), data_only=False)
                            if ws_formula_rows is None and ws.title in wb_formulas.sheetnames:
                                ws_formula_rows = list(wb_formulas[ws.title].iter_rows(min_row=1, values_only=True))
                            if ws_formula_rows and row_offset < len(ws_formula_rows) and target_idx < len(ws_formula_rows[row_offset]):
                                f_raw = ws_formula_rows[row_offset][target_idx]
                                if isinstance(f_raw, str) and f_raw.strip().startswith("="):
                                    return _resolve_formula_cell(f_raw, ws_all_rows, row_offset)
                        return None

                    # Extraer primero Precio de Venta explícito (si la columna existe y tiene valor > 0),
                    # de lo contrario usar Costo Promedio Unitario del archivo (sin fallback posicional ciego si hay encabezados)
                    p_venta_val = _get_numeric_with_formula_fallback(indices["precio_venta"])
                    c_costo_val = _get_numeric_with_formula_fallback(
                        indices["costo_unitario"],
                        14 if (not has_explicit_price_col and len(headers) >= 16) else None,
                    )
                    if p_venta_val is not None and p_venta_val > 0:
                        c_unitario = p_venta_val
                    elif c_costo_val is not None:
                        c_unitario = c_costo_val
                    else:
                        c_unitario = p_venta_val

                    imp_propio = _get_numeric_with_formula_fallback(
                        indices["importe_inventario_propio"],
                        15 if (not has_explicit_price_col and len(headers) >= 16) else None,
                    )
                    val_consig = _get_numeric_with_formula_fallback(
                        indices["valor_consignacion_proveedor"],
                        16 if (not has_explicit_price_col and len(headers) >= 17) else None,
                    )

                    sku_key = str(cod_mat or "").strip().upper()

                    # Resolución determinista del precio unitario:
                    # 1. Valor explícito en el archivo (Precio Venta o Costo Unitario)
                    # 2. División exacta de Importe Propio / Cantidad Propia del propio archivo
                    # 3. División exacta de Valor Consignación / Existencia Consignación del propio archivo
                    # 4. Otro registro del mismo SKU dentro del mismo archivo subido
                    # 5. Catálogo de referencia SOLO cuando el archivo no incluye columnas de precio/costo/importe
                    if c_unitario is None or c_unitario <= 0.0:
                        if imp_propio and imp_propio > 0 and c_propia > 0:
                            c_unitario = round(imp_propio / c_propia, 2)
                        elif val_consig and val_consig > 0 and e_consig > 0:
                            c_unitario = round(val_consig / e_consig, 2)
                        elif sku_key in sheet_price_map:
                            c_unitario = sheet_price_map[sku_key]
                        elif not has_explicit_price_col and sku_key in reference_catalog:
                            c_unitario = reference_catalog[sku_key]

                    if sku_key and c_unitario and c_unitario > 0 and sku_key not in sheet_price_map:
                        sheet_price_map[sku_key] = c_unitario

                    # Auto-completar importes totales si vinieron en 0 o vacíos
                    if (imp_propio is None or imp_propio <= 0.0) and c_unitario and c_unitario > 0 and c_propia > 0:
                        imp_propio = round(c_unitario * c_propia, 2)
                    if (val_consig is None or val_consig <= 0.0) and c_unitario and c_unitario > 0 and e_consig > 0:
                        val_consig = round(c_unitario * e_consig, 2)
                        
                    inv = InventarioAbcf(
                        nombre_centro=centro_val,
                        almacen=almacen_val,
                        numero_proveedor=_clean_code(_row_value(row, indices["numero_proveedor"])),
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
        col_info = f" (Columna de precio: {', '.join(detected_columns_summary[:3])})" if detected_columns_summary else ""
        return {
            "status": "success",
            "message": f"Se han cargado {len(items_to_add)} registros de inventario exitosamente.{col_info}",
            "detected_price_columns": detected_columns_summary,
        }
        
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

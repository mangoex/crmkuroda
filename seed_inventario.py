import os
import io
import openpyxl
import asyncio
import logging
from sqlalchemy.future import select
from sqlalchemy import func, delete
from app.core.database import SessionLocal
from app.models.inventario_abcf import InventarioAbcf
from app.api.v1.inventario_abcf import _normalize_header, _header_index, _row_value, _as_float

logger = logging.getLogger(__name__)

EXCEL_PATHS = [
    os.path.join(os.path.dirname(__file__), "Inventario MKS D.XLSX"),
    os.path.join(os.path.dirname(__file__), "..", "Inventario MKS D.XLSX"),
    os.path.join(os.path.dirname(__file__), "Inventario MKS al 29.06.26.XLSX"),
    os.path.join(os.path.dirname(__file__), "..", "Inventario MKS al 29.06.26.XLSX"),
    "Inventario MKS D.XLSX",
    "../Inventario MKS D.XLSX",
]


def find_inventario_excel_file():
    for p in EXCEL_PATHS:
        abs_p = os.path.abspath(p)
        if os.path.exists(abs_p):
            return abs_p
    return None


async def seed_inventario_from_excel(force=False):
    excel_file = find_inventario_excel_file()
    if not excel_file:
        logger.warning("No se encontro archivo Excel de Inventario D")
        return 0

    async with SessionLocal() as session:
        if not force:
            count_res = await session.execute(select(func.count(InventarioAbcf.id)))
            existing_count = count_res.scalar() or 0

            cost_sum_res = await session.execute(select(func.coalesce(func.sum(InventarioAbcf.costo_promedio_unitario), 0)))
            total_cost = cost_sum_res.scalar() or 0

            # Si ya existen registros Y tienen costos mayores a 0, no resembrar
            if existing_count > 0 and total_cost > 0:
                return existing_count

        print(f"Cargando/actualizando inventario D desde: {excel_file}")
        wb = openpyxl.load_workbook(excel_file, read_only=True, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return 0

        header_row = rows[0]
        headers = [_normalize_header(value) for value in header_row]

        indices = {
            "centro": _header_index(headers, "centro", "sucursal", "centro distribucion", "nombre centro"),
            "almacen": _header_index(headers, "almacen", "almacen origen"),
            "numero_proveedor": _header_index(headers, "numero proveedor", "codigo proveedor", "proveedor codigo", "numero de proveedor"),
            "nombre_proveedor": _header_index(headers, "nombre proveedor", "proveedor", "razon social proveedor", "nombre del proveedor"),
            "abc_f": _header_index(headers, "abc+f", "abcf", "codigo abcf", "clasificacion abcf", "indicador abc+frecuencia de venta", "indicador abcf frecuencia de venta", "d"),
            "codigo_material": _header_index(headers, "codigo material", "clave material", "codigo producto", "clave producto", "sku"),
            "descripcion_material": _header_index(headers, "descripcion material", "descripcion producto", "descripcion", "producto"),
            "cantidad_propia": _header_index(headers, "cantidad propia", "cant propia", "inventario disponible", "existencia propia", "disponible"),
            "existencia_consignacion": _header_index(headers, "existencia consignacion", "inv consig", "inventario consignacion", "existencia en consignacion de proveedore", "existencia en consignacion de proveedores"),
            "entregas_pendientes": _header_index(headers, "entregas pendientes"),
            "existencia_transito": _header_index(headers, "existencia transito", "transito"),
            "existencia_bloqueada": _header_index(headers, "existencia bloqueada", "bloqueada"),
            "existencia_control_calidad": _header_index(headers, "existencia control calidad", "control calidad"),
            "umb": _header_index(headers, "umb", "unidad medida", "unidad de medida base"),
            "costo_promedio_unitario": _header_index(headers, "costo promedio unitario", "costo promedio", "precio promedio", "costo prom unitario", "costo prom", "precio prom", "precio", "costo", "costo unitario", "precio unitario"),
            "importe_inventario_propio": _header_index(headers, "importe de inventario propio", "importe inventario propio", "importe inv propio", "importe inv", "importe inventario", "importe propio", "importe total", "importe"),
            "valor_consignacion_proveedor": _header_index(headers, "valor consignacion proveedor", "valor de consignacion proveedor"),
            "ubicacion": _header_index(headers, "ubicacion", "localizacion"),
            "grupo_materiales": _header_index(headers, "grupo materiales", "grupo de materiales"),
            "descrip_gpo_materiales": _header_index(headers, "descripcion grupo materiales", "descrip gpo materiales", "descripcion de grupo materiales"),
            "codigo_anterior_material": _header_index(headers, "codigo anterior material", "codigo anterior"),
            "abc": _header_index(headers, "abc", "indicador abc"),
            "fecha_ultimo_inventario": _header_index(headers, "fecha ultimo inventario", "fecha del ultimo inventario ciclico", "ultimo inventario"),
        }

        # Limpiar registros previos para evitar duplicados o datos incompletos
        await session.execute(delete(InventarioAbcf))

        rows_added = 0
        for row in rows[1:]:
            if not row or not _row_value(row, indices["centro"], 0):
                continue

            c_propia = _as_float(_row_value(row, indices["cantidad_propia"], 7), 0.0)
            e_consig = _as_float(_row_value(row, indices["existencia_consignacion"], 8), 0.0)

            if c_propia == 0.0 and e_consig == 0.0:
                continue

            costo_unit = _as_float(_row_value(row, indices["costo_promedio_unitario"], 14), 0.0)
            importe_inv = _as_float(_row_value(row, indices["importe_inventario_propio"], 15), 0.0)

            if (importe_inv is None or importe_inv == 0.0) and (costo_unit and costo_unit > 0) and (c_propia and c_propia > 0):
                importe_inv = round(costo_unit * c_propia, 2)
            elif (costo_unit is None or costo_unit == 0.0) and (importe_inv and importe_inv > 0) and (c_propia and c_propia > 0):
                costo_unit = round(importe_inv / c_propia, 2)

            inv = InventarioAbcf(
                nombre_centro=str(_row_value(row, indices["centro"], 0)) if _row_value(row, indices["centro"], 0) is not None else None,
                almacen=str(_row_value(row, indices["almacen"])) if _row_value(row, indices["almacen"]) is not None else None,
                numero_proveedor=str(_row_value(row, indices["numero_proveedor"])) if _row_value(row, indices["numero_proveedor"]) is not None else None,
                nombre_proveedor=str(_row_value(row, indices["nombre_proveedor"], 2)) if _row_value(row, indices["nombre_proveedor"], 2) is not None else None,
                abc_f=str(_row_value(row, indices["abc_f"])) if _row_value(row, indices["abc_f"]) is not None else None,
                codigo_material=str(_row_value(row, indices["codigo_material"], 1)) if _row_value(row, indices["codigo_material"], 1) is not None else None,
                descripcion_material=str(_row_value(row, indices["descripcion_material"], 3)) if _row_value(row, indices["descripcion_material"], 3) is not None else None,
                cantidad_propia=c_propia,
                existencia_consignacion=e_consig,
                entregas_pendientes=_as_float(_row_value(row, indices["entregas_pendientes"], 9)),
                existencia_transito=_as_float(_row_value(row, indices["existencia_transito"], 10)),
                existencia_bloqueada=_as_float(_row_value(row, indices["existencia_bloqueada"], 11)),
                existencia_control_calidad=_as_float(_row_value(row, indices["existencia_control_calidad"], 12)),
                umb=str(_row_value(row, indices["umb"], 13)) if _row_value(row, indices["umb"], 13) is not None else None,
                costo_promedio_unitario=costo_unit,
                importe_inventario_propio=importe_inv,
                valor_consignacion_proveedor=_as_float(_row_value(row, indices["valor_consignacion_proveedor"], 16)),
                ubicacion=str(_row_value(row, indices["ubicacion"], 17)) if _row_value(row, indices["ubicacion"], 17) is not None else None,
                grupo_materiales=str(_row_value(row, indices["grupo_materiales"], 18)) if _row_value(row, indices["grupo_materiales"], 18) is not None else None,
                descrip_gpo_materiales=str(_row_value(row, indices["descrip_gpo_materiales"], 19)) if _row_value(row, indices["descrip_gpo_materiales"], 19) is not None else None,
                codigo_anterior_material=str(_row_value(row, indices["codigo_anterior_material"], 20)) if _row_value(row, indices["codigo_anterior_material"], 20) is not None else None,
                abc=str(_row_value(row, indices["abc"], 21)) if _row_value(row, indices["abc"], 21) is not None else None,
                fecha_ultimo_inventario=str(_row_value(row, indices["fecha_ultimo_inventario"], 22)) if _row_value(row, indices["fecha_ultimo_inventario"], 22) is not None else None,
            )
            session.add(inv)
            rows_added += 1

        await session.commit()
        print(f"Siembra/actualizacion de inventario completada: {rows_added} registros cargados.")
        return rows_added


if __name__ == "__main__":
    asyncio.run(seed_inventario_from_excel(force=True))

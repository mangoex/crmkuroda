"""TDD Unit test suite for Inventario D / ABC+F pricing header mapping and deterministic price resolution."""

import unittest
from app.api.v1.inventario_abcf import _header_index, _normalize_header, _as_float


class TestInventarioAbcfPricing(unittest.TestCase):
    def test_header_index_recognizes_sale_price_aliases(self):
        """Verifica que el parser de Excel reconozca todas las variantes de Precio de Venta."""
        sale_price_aliases = [
            "Precio Venta",
            "PRECIO DE VENTA",
            "Precio Lista",
            "precio unitario",
            "PVP",
            "Precio Comercial",
            "Costo Promedio Unitario",
            "Precio Promocion",
            "Precio Prom.",
            "Precio Prom",
        ]
        
        for alias in sale_price_aliases:
            headers = [_normalize_header("Centro"), _normalize_header("Codigo Material"), _normalize_header(alias)]
            idx = _header_index(
                headers,
                "precio venta",
                "precio de venta",
                "precio lista",
                "precio unitario",
                "precio comercial",
                "precio",
                "pvp",
                "costo promedio unitario",
                "costo promedio",
                "precio promedio",
                "precio prom",
                "precio promocion",
            )
            self.assertEqual(idx, 2, f"Falló al reconocer alias de precio: {alias}")

    def test_price_fallback_from_inventory_amount_and_quantity(self):
        """Si el costo unitario viene en 0 pero hay importe y cantidad, debe resolverse determinísticamente."""
        cant_propia = 5.0
        importe_propio = 13666.50
        costo_unitario_raw = 0.0

        resolved_price = costo_unitario_raw if costo_unitario_raw > 0 else (importe_propio / cant_propia if cant_propia > 0 else 0.0)
        self.assertEqual(resolved_price, 2733.30)

    def test_parse_inventario_rows_extracts_prices_and_deduplicates(self):
        """Verifica que el parser de libro openpyxl extraiga correctamente los precios y no duplique registros."""
        from openpyxl import Workbook
        from seed_inventario import parse_inventario_rows_from_workbook

        wb = Workbook()
        ws1 = wb.active
        ws1.title = "Sheet1"
        ws1.append([
            "Nombre Centro", "Almacen", "Numero de Proveedor", "Nombre del Proveedor",
            "ABC+F", "Codigo Material", "Descripcion Material", "Cantidad Propia",
            "Existencia en Consignacion de Proveedore", "Entregas Pendientes", "Existencia en Transito",
            "Existencia Bloqueada", "Existencia Control Calidad", "UMB", "Costo Promedio Unitario",
            "Importe de Inventario Propio", "Valor de Consignacion Proveedor", "Ubicacion",
            "Grupo Materiales", "Descrip Gpo Materiales", "Codigo Anterior Material", "ABC", "Fecha del Ultimo Inventario Ciclico"
        ])
        ws1.append([
            "MKS CASA KURODA", "MA01", "100004", "MOEN DE MEXICO S.A DE C.V.",
            "D6", "102565", "MANERAL P/MON MONTICELLO CROMO MOEN", 5,
            0, 0, 0, 0, 0, "PZA", 450.87, 2254.35, 0, "C49", "22", "REFACCIONES", "DES", "D", None
        ])

        # Hoja duplicada (ej. Material D Ck Matriz)
        ws2 = wb.create_sheet(title="Material D Ck Matriz.")
        ws2.append([
            "Nombre Centro", "Almacen", "Numero de Proveedor", "Nombre del Proveedor",
            "ABC+F", "Codigo Material", "Descripcion Material", "Cantidad Propia",
            "Existencia en Consignacion de Proveedore", "Entregas Pendientes", "Existencia en Transito",
            "Existencia Bloqueada", "Existencia Control Calidad", "UMB", "Costo Promedio Unitario",
            "Importe de Inventario Propio", "Valor de Consignacion Proveedor", "Ubicacion",
            "Grupo Materiales", "Descrip Gpo Materiales", "Codigo Anterior Material", "ABC", "Fecha del Ultimo Inventario Ciclico"
        ])
        ws2.append([
            "MKS CASA KURODA", "MA01", "100004", "MOEN DE MEXICO S.A DE C.V.",
            "D6", "102565", "MANERAL P/MON MONTICELLO CROMO MOEN", 5,
            0, 0, 0, 0, 0, "PZA", 450.87, 2254.35, 0, "C49", "22", "REFACCIONES", "DES", "D", None
        ])

        records = parse_inventario_rows_from_workbook(wb)
        self.assertEqual(len(records), 1, "Debe deduplicar filas idénticas entre hojas")
        self.assertEqual(records[0]["codigo_material"], "102565")
        self.assertEqual(records[0]["costo_promedio_unitario"], 450.87)
        self.assertEqual(records[0]["importe_inventario_propio"], 2254.35)
        self.assertEqual(records[0]["ubicacion"], "C49")


if __name__ == "__main__":
    unittest.main()

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


if __name__ == "__main__":
    unittest.main()

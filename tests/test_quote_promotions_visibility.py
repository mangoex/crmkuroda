"""TDD Test Suite for Quote Promotions Visibility and Priority (Punto 9)."""

from datetime import date, datetime, timedelta
import unittest
from app.services.commercial_analytics import promotion_priority


class DummyItem:
    def __init__(self, codigo_material):
        self.codigo_material = codigo_material


class DummyPromo:
    def __init__(self, codigo_material, descripcion_material, precio_promocion, valido_hasta):
        self.codigo_material = codigo_material
        self.descripcion_material = descripcion_material
        self.precio_promocion = precio_promocion
        self.valido_hasta = valido_hasta


class DummyQuote:
    def __init__(self, numero_factura=None, venta_perdida="No", fecha_registro=None, materiales_cotizados=None, items=None):
        self.numero_factura = numero_factura
        self.venta_perdida = venta_perdida
        self.fecha_registro = fecha_registro
        self.materiales_cotizados = materiales_cotizados
        self.items = items or []


class TestQuotePromotionsVisibility(unittest.TestCase):
    def setUp(self):
        self.today = date.today()
        self.valid_promo_high = DummyPromo(
            codigo_material="SKU-100",
            descripcion_material="Tubo PVC 1/2",
            precio_promocion=150.0,
            valido_hasta=self.today + timedelta(days=2),  # <= 3 days -> alta
        )
        self.valid_promo_medium = DummyPromo(
            codigo_material="SKU-200",
            descripcion_material="Llave Monomando",
            precio_promocion=850.0,
            valido_hasta=self.today + timedelta(days=5),  # <= 7 days -> media
        )
        self.valid_promo_normal = DummyPromo(
            codigo_material="SKU-300",
            descripcion_material="Valvula Esfera",
            precio_promocion=95.0,
            valido_hasta=self.today + timedelta(days=15),  # > 7 days -> normal
        )

    def test_promotion_detected_from_items_detail(self):
        """Detecta promoción a través de CotizacionItems."""
        quote = DummyQuote(fecha_registro=self.today - timedelta(days=5))
        items = [DummyItem("SKU-100"), DummyItem("SKU-999")]
        promos = [self.valid_promo_high, self.valid_promo_medium]

        result = promotion_priority(quote, items, promos, self.today, quote_valid_days=30)
        self.assertTrue(result["tiene_promocion"])
        self.assertEqual(result["nivel_prioridad"], "alta")
        self.assertEqual(len(result["promociones_coincidentes"]), 1)
        self.assertEqual(result["promociones_coincidentes"][0]["codigo_material"], "SKU-100")

    def test_promotion_detected_from_raw_material_text_fallback(self):
        """Si items está vacío, detecta promoción desde el texto de materiales_cotizados."""
        quote = DummyQuote(
            fecha_registro=self.today - timedelta(days=3),
            materiales_cotizados="SKU-200, SKU-888, SKU-777",
        )
        items = []
        promos = [self.valid_promo_medium]

        result = promotion_priority(quote, items, promos, self.today, quote_valid_days=30)
        self.assertTrue(result["tiene_promocion"])
        self.assertEqual(result["nivel_prioridad"], "media")
        self.assertEqual(len(result["promociones_coincidentes"]), 1)
        self.assertEqual(result["promociones_coincidentes"][0]["codigo_material"], "SKU-200")

    def test_invoiced_or_lost_or_expired_quote_has_no_active_promo(self):
        """Las cotizaciones facturadas, perdidas o vencidas no deben marcarse con promoción."""
        invoiced_quote = DummyQuote(numero_factura="FAC-123", fecha_registro=self.today)
        lost_quote = DummyQuote(venta_perdida="Si", fecha_registro=self.today)
        expired_quote = DummyQuote(fecha_registro=self.today - timedelta(days=35))

        items = [DummyItem("SKU-100")]
        promos = [self.valid_promo_high]

        res_inv = promotion_priority(invoiced_quote, items, promos, self.today, quote_valid_days=30)
        self.assertFalse(res_inv["tiene_promocion"])

        res_lost = promotion_priority(lost_quote, items, promos, self.today, quote_valid_days=30)
        self.assertFalse(res_lost["tiene_promocion"])

        res_exp = promotion_priority(expired_quote, items, promos, self.today, quote_valid_days=30)
        self.assertFalse(res_exp["tiene_promocion"])

    def test_safe_attribute_access_without_lazy_load_error(self):
        """Si el objeto de cotización no tiene items o materiales_cotizados cargados, no genera excepción."""
        class RestrictedQuote:
            def __init__(self, today):
                self.__dict__ = {"fecha_registro": today}
            def __getattr__(self, name):
                raise RuntimeError(f"Lazy load triggered for {name}")

        quote = RestrictedQuote(self.today)
        items = []
        promos = [self.valid_promo_high]
        result = promotion_priority(quote, items, promos, self.today, quote_valid_days=30)
        self.assertFalse(result["tiene_promocion"])


if __name__ == "__main__":
    unittest.main()

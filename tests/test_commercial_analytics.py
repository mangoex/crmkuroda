import unittest
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.services.commercial_analytics import (
    aggregate_channels,
    aggregate_material_items,
    build_seller_performance,
    normalize_channel,
    normalize_contact,
    promotion_priority,
)


class CommercialAnalyticsTest(unittest.TestCase):
    def test_contact_prefers_cellphone_and_keeps_phone(self):
        result = normalize_contact(
            {"email": "cliente@example.com", "telefono": "016671111111", "celular": "6672222222"}
        )

        self.assertEqual(result["contacto_preferente"], "6672222222")
        self.assertEqual(result["tipo_contacto_preferente"], "celular")
        self.assertEqual(result["telefono"], "016671111111")

    def test_contact_falls_back_to_phone(self):
        result = normalize_contact({"telefono": "016671111111"})

        self.assertEqual(result["contacto_preferente"], "016671111111")
        self.assertEqual(result["tipo_contacto_preferente"], "telefono")

    def test_unknown_channel_is_not_hidden(self):
        self.assertEqual(normalize_channel("02"), "Sin clasificar")

    def test_configured_channel_uses_business_name(self):
        self.assertEqual(
            normalize_channel("02", {"02": "Kuroda Turbo"}),
            "Kuroda Turbo",
        )

    def test_channel_totals_use_invoiced_amount(self):
        quotes = [
            SimpleNamespace(
                canal="01",
                total=Decimal("1000"),
                importe_facturado=Decimal("800"),
                numero_factura="F-1",
            ),
            SimpleNamespace(
                canal="01",
                total=Decimal("500"),
                importe_facturado=Decimal("0"),
                numero_factura=None,
            ),
        ]

        rows = aggregate_channels(quotes, {"01": "Apartados"})

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["importe_facturado"], 800.0)
        self.assertEqual(rows[0]["importe_cotizado"], 1500.0)
        self.assertEqual(rows[0]["operaciones_facturadas"], 1)
        self.assertEqual(rows[0]["conversion"], 50.0)

    def test_material_detail_reconciles_by_seller_family_group_and_sku(self):
        quote = SimpleNamespace(vendedor_id="seller-1", vendedor_nombre="Ana")
        rows = [
            (
                SimpleNamespace(
                    familia="Pisos",
                    grupo_materiales="Cerámica",
                    codigo_material="SKU-1",
                    descripcion="Piso",
                    cantidad_cotizada=2,
                    importe_cotizado=200,
                    cantidad_facturada=1,
                    importe_facturado=100,
                ),
                quote,
            ),
            (
                SimpleNamespace(
                    familia="Pisos",
                    grupo_materiales="Cerámica",
                    codigo_material="SKU-1",
                    descripcion="Piso",
                    cantidad_cotizada=3,
                    importe_cotizado=300,
                    cantidad_facturada=2,
                    importe_facturado=200,
                ),
                quote,
            ),
        ]

        result = aggregate_material_items(rows)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["cantidad_facturada"], 3.0)
        self.assertEqual(result[0]["importe_facturado"], 300.0)

    def test_material_detail_resolves_name_from_linked_seller(self):
        seller_id = uuid4()
        quote = SimpleNamespace(vendedor_id=seller_id, vendedor_nombre=None)
        item = SimpleNamespace(
            familia="Pisos",
            grupo_materiales="Cerámica",
            codigo_material="SKU-1",
            descripcion="Piso",
            cantidad_cotizada=1,
            importe_cotizado=100,
            cantidad_facturada=1,
            importe_facturado=100,
        )

        result = aggregate_material_items(
            [(item, quote)],
            {str(seller_id): "Ana Asesora"},
        )

        self.assertEqual(result[0]["vendedor"], "Ana Asesora")

    def test_seller_performance_uses_factured_amount_and_resolves_historical_name(self):
        seller_id = uuid4()
        seller = SimpleNamespace(
            id=seller_id,
            codigo_vendedor="A01",
            nombre_completo="Ana Asesora",
            email="ana@example.com",
        )
        quotes = [
            SimpleNamespace(
                vendedor_id=None,
                vendedor_nombre="ana asesora",
                numero_factura="F-1",
                importe_facturado=Decimal("800"),
                total=Decimal("1000"),
                venta_perdida=None,
                fecha_registro=date(2026, 7, 20),
            ),
            SimpleNamespace(
                vendedor_id=seller_id,
                vendedor_nombre=None,
                numero_factura=None,
                importe_facturado=Decimal("0"),
                total=Decimal("500"),
                venta_perdida=None,
                fecha_registro=date(2026, 7, 22),
            ),
        ]
        goals = [SimpleNamespace(vendedor_id=seller_id, monto_objetivo=Decimal("2000"))]
        logs = [
            SimpleNamespace(user_id=seller_id, total_points=80, date=date(2026, 7, 20)),
            SimpleNamespace(user_id=seller_id, total_points=100, date=date(2026, 7, 21)),
        ]

        result = build_seller_performance(
            [seller],
            quotes,
            goals,
            logs,
            date(2026, 7, 26),
            30,
        )[0]

        self.assertEqual(result["venta_facturada"], 800.0)
        self.assertEqual(result["cumplimiento"], 40.0)
        self.assertEqual(result["conversion"], 50.0)
        self.assertEqual(result["ticket_promedio"], 800.0)
        self.assertEqual(result["pendientes"], 1)
        self.assertEqual(result["consistencia_promedio"], 90.0)

    def test_promotion_requires_exact_sku_and_current_validity(self):
        quote = SimpleNamespace(
            numero_factura=None,
            venta_perdida=None,
            fecha_registro=date(2026, 7, 20),
        )
        items = [SimpleNamespace(codigo_material="SKU-EXACT")]
        promotions = [
            SimpleNamespace(
                codigo_material="SKU-EXACT",
                descripcion_material="Producto",
                precio_promocion=99,
                valido_hasta=datetime(2026, 7, 29),
            ),
            SimpleNamespace(
                codigo_material="SKU",
                descripcion_material="Parecido",
                precio_promocion=50,
                valido_hasta=datetime(2026, 7, 29),
            ),
        ]

        result = promotion_priority(
            quote,
            items,
            promotions,
            date(2026, 7, 26),
        )

        self.assertTrue(result["tiene_promocion"])
        self.assertEqual(result["nivel_prioridad"], "alta")
        self.assertEqual(len(result["promociones_coincidentes"]), 1)
        self.assertEqual(
            result["promociones_coincidentes"][0]["codigo_material"],
            "SKU-EXACT",
        )

    def test_expired_promotion_does_not_prioritize(self):
        quote = SimpleNamespace(
            numero_factura=None,
            venta_perdida=None,
            fecha_registro=date(2026, 7, 20),
        )
        result = promotion_priority(
            quote,
            [SimpleNamespace(codigo_material="SKU-1")],
            [
                SimpleNamespace(
                    codigo_material="SKU-1",
                    descripcion_material="Producto",
                    precio_promocion=99,
                    valido_hasta=datetime(2026, 7, 25),
                )
            ],
            date(2026, 7, 26),
        )

        self.assertFalse(result["tiene_promocion"])

    def test_sold_or_stale_quote_does_not_prioritize(self):
        promotion = SimpleNamespace(
            codigo_material="SKU-1",
            descripcion_material="Producto",
            precio_promocion=99,
            valido_hasta=datetime(2026, 8, 30),
        )
        sold = SimpleNamespace(
            numero_factura="F-1",
            venta_perdida=None,
            fecha_registro=date(2026, 7, 20),
        )
        stale = SimpleNamespace(
            numero_factura=None,
            venta_perdida=None,
            fecha_registro=date(2026, 6, 1),
        )

        self.assertFalse(
            promotion_priority(
                sold,
                [SimpleNamespace(codigo_material="SKU-1")],
                [promotion],
                date(2026, 7, 26),
            )["tiene_promocion"]
        )
        self.assertFalse(
            promotion_priority(
                stale,
                [SimpleNamespace(codigo_material="SKU-1")],
                [promotion],
                date(2026, 7, 26),
            )["tiene_promocion"]
        )


if __name__ == "__main__":
    unittest.main()

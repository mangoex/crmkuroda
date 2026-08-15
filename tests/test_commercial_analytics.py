import unittest
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.services.commercial_analytics import (
    aggregate_channels,
    aggregate_channel_summary_rows,
    aggregate_material_items,
    build_seller_dashboard_metrics,
    build_seller_performance,
    find_clients_for_promotion,
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

    def test_channel_resolution_prioritizes_special_client_numbers(self):
        quotes = [
            SimpleNamespace(
                numero_cliente="400550",
                canal="ENTREGA INMEDIATA",
                total=Decimal("2000"),
                importe_facturado=Decimal("2000"),
                numero_factura="F-MP",
            ),
            SimpleNamespace(
                numero_cliente="400260",
                canal="ENVÍO A DOMICILIO",
                total=Decimal("1500"),
                importe_facturado=Decimal("1500"),
                numero_factura="F-AP",
            ),
        ]
        rows = aggregate_channels(quotes)
        channel_names = {r["canal"] for r in rows}
        self.assertIn("Market place", channel_names)
        self.assertIn("Apartados", channel_names)

    def test_dashboard_channel_summary_preserves_numeric_source_code(self):
        rows = aggregate_channel_summary_rows(
            [("01", 4, Decimal("1200"), 2, Decimal("900"))]
        )

        self.assertEqual(rows[0]["codigo_canal"], "01")
        self.assertEqual(rows[0]["etiqueta"], "Canal 01")
        self.assertEqual(rows[0]["importe_facturado"], 900.0)
        self.assertEqual(rows[0]["conversion"], 50.0)

    def test_dashboard_channel_summary_maps_marketplace_and_apartados_codes(self):
        rows = aggregate_channel_summary_rows(
            [
                ("400550", 10, Decimal("5000"), 8, Decimal("4000")),
                ("400260", 5, Decimal("3000"), 4, Decimal("2500")),
            ]
        )
        self.assertEqual(rows[0]["codigo_canal"], "400550")
        self.assertEqual(rows[0]["canal"], "Market place")
        self.assertEqual(rows[0]["etiqueta"], "Market place")
        self.assertEqual(rows[1]["codigo_canal"], "400260")
        self.assertEqual(rows[1]["canal"], "Apartados")
        self.assertEqual(rows[1]["etiqueta"], "Apartados")

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

    # ---- find_clients_for_promotion tests ----

    def test_find_clients_basic_match(self):
        promo = SimpleNamespace(codigo_material="SKU-A", descripcion_material="Tubo", precio_promocion=99.0, valido_hasta=datetime(2026, 12, 31))
        item = SimpleNamespace(codigo_material="SKU-A", cantidad_facturada=10, importe_facturado=500, cantidad_cotizada=10, importe_cotizado=500)
        quote = SimpleNamespace(
            numero_cliente="1001", cliente_nombre="Cliente A", vendedor_nombre="V1",
            vendedor_id=None, datos_contacto={"celular": "667111"}, numero_factura="F-1",
            importe_facturado=500, fecha_factura=date(2026, 6, 1), fecha_registro=date(2026, 5, 1),
            venta_perdida=None,
        )
        result = find_clients_for_promotion(promo, [(item, quote)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["numero_cliente"], "1001")
        self.assertEqual(result[0]["tipo_operacion"], "Facturado")

    def test_find_clients_only_invoiced_excludes_quoted(self):
        promo = SimpleNamespace(codigo_material="SKU-B", descripcion_material="Valvula", precio_promocion=50.0, valido_hasta=datetime(2026, 12, 31))
        item = SimpleNamespace(codigo_material="SKU-B", cantidad_facturada=0, importe_facturado=0, cantidad_cotizada=5, importe_cotizado=250)
        quote = SimpleNamespace(
            numero_cliente="2002", cliente_nombre="Cliente B", vendedor_nombre="V1",
            vendedor_id=None, datos_contacto={}, numero_factura=None,
            importe_facturado=0, fecha_factura=None, fecha_registro=date(2026, 5, 1),
            venta_perdida=None,
        )
        result_strict = find_clients_for_promotion(promo, [(item, quote)], only_invoiced=True)
        self.assertEqual(len(result_strict), 0)
        result_all = find_clients_for_promotion(promo, [(item, quote)], only_invoiced=False)
        self.assertEqual(len(result_all), 1)
        self.assertEqual(result_all[0]["tipo_operacion"], "Cotizado")

    def test_find_clients_deduplicates_by_client(self):
        promo = SimpleNamespace(codigo_material="SKU-C", descripcion_material="Conector", precio_promocion=30.0, valido_hasta=datetime(2026, 12, 31))
        item1 = SimpleNamespace(codigo_material="SKU-C", cantidad_facturada=3, importe_facturado=90, cantidad_cotizada=3, importe_cotizado=90)
        item2 = SimpleNamespace(codigo_material="SKU-C", cantidad_facturada=7, importe_facturado=210, cantidad_cotizada=7, importe_cotizado=210)
        quote1 = SimpleNamespace(
            numero_cliente="3003", cliente_nombre="Cliente C", vendedor_nombre="V1",
            vendedor_id=None, datos_contacto={}, numero_factura="F-1",
            importe_facturado=90, fecha_factura=date(2026, 3, 1), fecha_registro=date(2026, 2, 1),
            venta_perdida=None,
        )
        quote2 = SimpleNamespace(
            numero_cliente="3003", cliente_nombre="Cliente C", vendedor_nombre="V1",
            vendedor_id=None, datos_contacto={}, numero_factura="F-2",
            importe_facturado=210, fecha_factura=date(2026, 6, 1), fecha_registro=date(2026, 5, 1),
            venta_perdida=None,
        )
        result = find_clients_for_promotion(promo, [(item1, quote1), (item2, quote2)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["operaciones"], 2)
        self.assertEqual(result[0]["cantidad_total"], 10)

    def test_find_clients_empty_promo_code_returns_empty(self):
        promo = SimpleNamespace(codigo_material=None, descripcion_material="X", precio_promocion=10.0, valido_hasta=datetime(2026, 12, 31))
        result = find_clients_for_promotion(promo, [])
        self.assertEqual(result, [])

    def test_build_seller_dashboard_metrics_generates_canonical_channels_clients_and_materials(self):
        q_id = uuid4()
        quotes = [
            SimpleNamespace(
                id=q_id,
                canal="01",
                numero_cliente="400260",  # Resolves to Apartados
                cliente_nombre="Constructora Alpha",
                total=Decimal("50000"),
                importe_facturado=Decimal("50000"),
                numero_factura="F-100",
                vendedor_id=None,
                vendedor_nombre="Vendedor 1",
            ),
            SimpleNamespace(
                id=uuid4(),
                canal="KURODA TURBO",
                numero_cliente="1001",
                cliente_nombre="Constructora Beta",
                total=Decimal("30000"),
                importe_facturado=Decimal("30000"),
                numero_factura="F-101",
                vendedor_id=None,
                vendedor_nombre="Vendedor 1",
            ),
        ]
        items = [
            SimpleNamespace(
                cotizacion_id=q_id,
                codigo_material="TUB-01",
                descripcion="Tubo PVC 4 pulg",
                grupo_materiales="Tubería y conexiones",
                familia="Plomería",
                cantidad_facturada=Decimal("20"),
                importe_facturado=Decimal("25000"),
                cantidad_cotizada=Decimal("20"),
                importe_cotizado=Decimal("25000"),
            ),
            SimpleNamespace(
                cotizacion_id=q_id,
                codigo_material="SAN-01",
                descripcion="Inodoro Ecológico",
                grupo_materiales="Sanitarios",
                familia="Baños",
                cantidad_facturada=Decimal("5"),
                importe_facturado=Decimal("25000"),
                cantidad_cotizada=Decimal("5"),
                importe_cotizado=Decimal("25000"),
            ),
        ]

        metrics = build_seller_dashboard_metrics(quotes, items)
        
        # 1. Check totals
        self.assertEqual(metrics["totales"]["venta_total"], 80000.0)
        self.assertEqual(metrics["totales"]["cotizaciones"], 2)

        # 2. Check 5 canonical channels exist
        channel_names = [c["canal"] for c in metrics["canales"]]
        self.assertIn("Apartados", channel_names)
        self.assertIn("Kuroda Turbo", channel_names)
        self.assertIn("Material D", channel_names)
        self.assertIn("Promociones", channel_names)
        self.assertIn("Market place", channel_names)

        apartados = next(c for c in metrics["canales"] if c["canal"] == "Apartados")
        self.assertEqual(apartados["monto"], 50000.0)
        self.assertEqual(apartados["porcentaje"], 62.5)

        turbo = next(c for c in metrics["canales"] if c["canal"] == "Kuroda Turbo")
        self.assertEqual(turbo["monto"], 30000.0)
        self.assertEqual(turbo["porcentaje"], 37.5)

        # 3. Check Top Clients
        self.assertEqual(len(metrics["clientes"]), 2)
        top_client = metrics["clientes"][0]
        self.assertEqual(top_client["cliente"], "Constructora Alpha")
        self.assertEqual(top_client["venta"], 50000.0)
        self.assertEqual(top_client["porcentaje"], 62.5)

        # 4. Check Top Materials
        self.assertEqual(len(metrics["materiales"]), 2)
        self.assertEqual(metrics["materiales"][0]["monto"], 25000.0)


if __name__ == "__main__":
    unittest.main()

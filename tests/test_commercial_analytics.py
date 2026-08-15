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

    def test_seller_performance_uses_factured_amount_and_resolves_historical_name(self):
        seller_id = uuid4()
        sellers = [
            SimpleNamespace(
                id=seller_id,
                codigo_vendedor="V01",
                nombre_completo="Juan Perez",
                email="juan@example.com",
            )
        ]
        quotes = [
            SimpleNamespace(
                vendedor_id=None,
                vendedor_nombre="JUAN PEREZ",
                total=Decimal("5000"),
                importe_facturado=Decimal("4200"),
                numero_factura="F-10",
                venta_perdida="NO",
                fecha_registro=date(2026, 3, 1),
            )
        ]
        goals = [
            SimpleNamespace(
                vendedor_id=seller_id,
                monto_objetivo=Decimal("10000"),
            )
        ]
        logs = [
            SimpleNamespace(
                user_id=seller_id,
                total_points=85,
                date=date(2026, 3, 1),
            )
        ]

        rows = build_seller_performance(
            sellers,
            quotes,
            goals,
            logs,
            today=date(2026, 3, 2),
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["venta_facturada"], 4200.0)
        self.assertEqual(rows[0]["importe_cotizado"], 5000.0)
        self.assertEqual(rows[0]["cumplimiento"], 42.0)
        self.assertEqual(rows[0]["consistencia_promedio"], 85.0)

    def test_promotion_requires_exact_sku_and_current_validity(self):
        today = date(2026, 3, 2)
        quote = SimpleNamespace(
            numero_factura=None,
            venta_perdida="NO",
            fecha_registro=date(2026, 2, 20),
        )
        items = [
            SimpleNamespace(codigo_material="SKU-100"),
            SimpleNamespace(codigo_material="SKU-200"),
        ]
        promotions = [
            SimpleNamespace(
                codigo_material="SKU-100",
                descripcion_material="Producto A",
                precio_promocion=120.0,
                valido_hasta=date(2026, 3, 5),
            ),
            SimpleNamespace(
                codigo_material="SKU-999",
                descripcion_material="Producto B",
                precio_promocion=80.0,
                valido_hasta=date(2026, 3, 5),
            ),
        ]

        result = promotion_priority(quote, items, promotions, today=today)

        self.assertTrue(result["tiene_promocion"])
        self.assertEqual(result["nivel_prioridad"], "alta")
        self.assertEqual(len(result["promociones_coincidentes"]), 1)
        self.assertEqual(result["promociones_coincidentes"][0]["codigo_material"], "SKU-100")

    def test_sold_or_stale_quote_does_not_prioritize(self):
        today = date(2026, 3, 2)
        invoiced_quote = SimpleNamespace(
            numero_factura="F-100",
            venta_perdida="NO",
            fecha_registro=date(2026, 2, 20),
        )
        stale_quote = SimpleNamespace(
            numero_factura=None,
            venta_perdida="NO",
            fecha_registro=date(2026, 1, 1),
        )
        items = [SimpleNamespace(codigo_material="SKU-100")]
        promotions = [
            SimpleNamespace(
                codigo_material="SKU-100",
                descripcion_material="Producto A",
                precio_promocion=120.0,
                valido_hasta=date(2026, 3, 5),
            )
        ]

        self.assertFalse(
            promotion_priority(invoiced_quote, items, promotions, today=today)["tiene_promocion"]
        )
        self.assertFalse(
            promotion_priority(stale_quote, items, promotions, today=today)["tiene_promocion"]
        )

    def test_expired_promotion_does_not_prioritize(self):
        today = date(2026, 3, 2)
        quote = SimpleNamespace(
            numero_factura=None,
            venta_perdida="NO",
            fecha_registro=date(2026, 2, 20),
        )
        items = [SimpleNamespace(codigo_material="SKU-100")]
        promotions = [
            SimpleNamespace(
                codigo_material="SKU-100",
                descripcion_material="Producto A",
                precio_promocion=120.0,
                valido_hasta=date(2026, 3, 1),
            )
        ]

        self.assertFalse(
            promotion_priority(quote, items, promotions, today=today)["tiene_promocion"]
        )

    def test_material_detail_reconciles_by_seller_family_group_and_sku(self):
        seller_id = str(uuid4())
        quote_1 = SimpleNamespace(
            vendedor_id=seller_id,
            vendedor_nombre="Vendedor Uno",
        )
        quote_2 = SimpleNamespace(
            vendedor_id=seller_id,
            vendedor_nombre="Vendedor Uno",
        )
        items = [
            (
                SimpleNamespace(
                    familia="Tubería",
                    grupo_materiales="PVC",
                    codigo_material="TUB-01",
                    descripcion="Tubo PVC 1/2",
                    cantidad_cotizada=Decimal("10"),
                    importe_cotizado=Decimal("1500"),
                    cantidad_facturada=Decimal("8"),
                    importe_facturado=Decimal("1200"),
                ),
                quote_1,
            ),
            (
                SimpleNamespace(
                    familia="Tubería",
                    grupo_materiales="PVC",
                    codigo_material="TUB-01",
                    descripcion="Tubo PVC 1/2",
                    cantidad_cotizada=Decimal("5"),
                    importe_cotizado=Decimal("750"),
                    cantidad_facturada=Decimal("5"),
                    importe_facturado=Decimal("750"),
                ),
                quote_2,
            ),
            (
                SimpleNamespace(
                    familia="Grifería",
                    grupo_materiales="Mezcladoras",
                    codigo_material="GRIF-09",
                    descripcion="Mezcladora Baño",
                    cantidad_cotizada=Decimal("2"),
                    importe_cotizado=Decimal("2200"),
                    cantidad_facturada=Decimal("0"),
                    importe_facturado=Decimal("0"),
                ),
                quote_2,
            ),
        ]

        rows = aggregate_material_items(items)

        self.assertEqual(len(rows), 2)
        top = rows[0]
        self.assertEqual(top["codigo_material"], "TUB-01")
        self.assertEqual(top["cantidad_cotizada"], 15.0)
        self.assertEqual(top["cantidad_facturada"], 13.0)
        self.assertEqual(top["importe_cotizado"], 2250.0)
        self.assertEqual(top["importe_facturado"], 1950.0)

    def test_material_detail_resolves_name_from_linked_seller(self):
        seller_id = str(uuid4())
        quote = SimpleNamespace(
            vendedor_id=seller_id,
            vendedor_nombre=None,
        )
        item = SimpleNamespace(
            familia="Válvulas",
            grupo_materiales="Bronce",
            codigo_material="VAL-01",
            descripcion="Válvula Esfera",
            cantidad_cotizada=Decimal("1"),
            importe_cotizado=Decimal("300"),
            cantidad_facturada=Decimal("1"),
            importe_facturado=Decimal("300"),
        )

        rows = aggregate_material_items(
            [(item, quote)],
            seller_names={seller_id: "Laura Directora"},
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["vendedor"], "Laura Directora")

    def test_find_clients_basic_match(self):
        seller_id = uuid4()
        quote_facturada = SimpleNamespace(
            id=uuid4(),
            numero_factura="FAC-001",
            importe_facturado=Decimal("5000"),
            total=Decimal("5000"),
            numero_cliente="12345",
            cliente_nombre="ACME Corp",
            vendedor_nombre="Vendedor Uno",
            vendedor_id=seller_id,
            datos_contacto={"telefono": "6671000001", "celular": "6672000001", "email": "acme@example.com"},
            fecha_factura=date(2026, 2, 15),
            fecha_registro=date(2026, 2, 10),
        )
        item_1 = SimpleNamespace(
            codigo_material="SKU-001",
            cantidad_facturada=Decimal("10"),
            cantidad_cotizada=Decimal("10"),
            importe_facturado=Decimal("5000"),
            importe_cotizado=Decimal("5000"),
        )
        promo = SimpleNamespace(
            codigo_material="SKU-001",
            descripcion_material="Tubo PVC",
            precio_promocion=450.0,
            valido_hasta=date(2026, 3, 31),
        )

        clients = find_clients_for_promotion(promo, [(item_1, quote_facturada)])

        self.assertEqual(len(clients), 1)
        c = clients[0]
        self.assertEqual(c["numero_cliente"], "12345")
        self.assertEqual(c["cliente_nombre"], "ACME Corp")
        self.assertEqual(c["vendedor_nombre"], "Vendedor Uno")
        self.assertEqual(c["vendedor_id"], str(seller_id))
        self.assertEqual(c["operaciones"], 1)
        self.assertEqual(c["cantidad_total"], 10.0)
        self.assertEqual(c["importe_total"], 5000.0)
        self.assertEqual(c["ultima_compra"], "2026-02-15")
        self.assertEqual(c["tipo_operacion"], "Facturado")
        self.assertEqual(c["contacto"]["contacto_preferente"], "6672000001")
        self.assertEqual(c["contacto"]["tipo_contacto_preferente"], "celular")

    def test_find_clients_deduplicates_by_client(self):
        quote_1 = SimpleNamespace(
            id=uuid4(),
            numero_factura="FAC-001",
            importe_facturado=Decimal("2000"),
            total=Decimal("2000"),
            numero_cliente="CL-10",
            cliente_nombre="Empresa Beta",
            vendedor_nombre="Vendedor Uno",
            vendedor_id=None,
            datos_contacto={"telefono": "6671111111"},
            fecha_factura=date(2026, 1, 10),
            fecha_registro=date(2026, 1, 5),
        )
        quote_2 = SimpleNamespace(
            id=uuid4(),
            numero_factura="FAC-002",
            importe_facturado=Decimal("3000"),
            total=Decimal("3000"),
            numero_cliente="CL-10",
            cliente_nombre="Empresa Beta",
            vendedor_nombre="Vendedor Uno",
            vendedor_id=None,
            datos_contacto={"telefono": "6671111111", "celular": "6679999999"},
            fecha_factura=date(2026, 2, 20),
            fecha_registro=date(2026, 2, 18),
        )
        item_a = SimpleNamespace(
            codigo_material="SKU-PROMO",
            cantidad_facturada=Decimal("2"),
            cantidad_cotizada=Decimal("2"),
            importe_facturado=Decimal("2000"),
            importe_cotizado=Decimal("2000"),
        )
        item_b = SimpleNamespace(
            codigo_material="SKU-PROMO",
            cantidad_facturada=Decimal("3"),
            cantidad_cotizada=Decimal("3"),
            importe_facturado=Decimal("3000"),
            importe_cotizado=Decimal("3000"),
        )
        promo = SimpleNamespace(
            codigo_material="SKU-PROMO",
            descripcion_material="Codo Cobre",
            precio_promocion=100.0,
            valido_hasta=date(2026, 4, 30),
        )

        clients = find_clients_for_promotion(
            promo, [(item_a, quote_1), (item_b, quote_2)]
        )

        self.assertEqual(len(clients), 1)
        c = clients[0]
        self.assertEqual(c["operaciones"], 2)
        self.assertEqual(c["cantidad_total"], 5.0)
        self.assertEqual(c["importe_total"], 5000.0)
        self.assertEqual(c["ultima_compra"], "2026-02-20")
        self.assertEqual(c["contacto"]["contacto_preferente"], "6679999999")

    def test_find_clients_only_invoiced_excludes_quoted(self):
        quote_quoted_only = SimpleNamespace(
            id=uuid4(),
            numero_factura=None,
            importe_facturado=Decimal("0"),
            total=Decimal("4000"),
            numero_cliente="CL-20",
            cliente_nombre="Solo Cotizo",
            vendedor_nombre="Vendedor Dos",
            vendedor_id=None,
            datos_contacto={},
            fecha_factura=None,
            fecha_registro=date(2026, 2, 1),
        )
        item = SimpleNamespace(
            codigo_material="SKU-X",
            cantidad_facturada=Decimal("0"),
            cantidad_cotizada=Decimal("4"),
            importe_facturado=Decimal("0"),
            importe_cotizado=Decimal("4000"),
        )
        promo = SimpleNamespace(
            codigo_material="SKU-X",
            descripcion_material="Llave Paso",
            precio_promocion=900.0,
            valido_hasta=date(2026, 5, 1),
        )

        invoiced_clients = find_clients_for_promotion(
            promo, [(item, quote_quoted_only)], only_invoiced=True
        )
        self.assertEqual(len(invoiced_clients), 0)

        all_clients = find_clients_for_promotion(
            promo, [(item, quote_quoted_only)], only_invoiced=False
        )
        self.assertEqual(len(all_clients), 1)
        self.assertEqual(all_clients[0]["tipo_operacion"], "Cotizado")
        self.assertEqual(all_clients[0]["cantidad_total"], 4.0)
        self.assertEqual(all_clients[0]["importe_total"], 4000.0)

    def test_find_clients_empty_promo_code_returns_empty(self):
        promo = SimpleNamespace(
            codigo_material="",
            descripcion_material="Sin codigo",
            precio_promocion=10.0,
            valido_hasta=date(2026, 5, 1),
        )
        clients = find_clients_for_promotion(promo, [])
        self.assertEqual(clients, [])

    def test_build_seller_dashboard_metrics_generates_canonical_channels_clients_and_materials(self):
        q_id = uuid4()
        q2_id = uuid4()
        quotes = [
            SimpleNamespace(
                id=q_id,
                canal="01",
                numero_cliente="400260", # Maps to Apartados
                cliente_nombre="Constructora Alpha",
                total=Decimal("50000"),
                importe_facturado=Decimal("50000"),
                numero_factura="F-101",
            ),
            SimpleNamespace(
                id=q2_id,
                canal="Kuroda Turbo",
                numero_cliente="123456",
                cliente_nombre="Beta Residencial",
                total=Decimal("30000"),
                importe_facturado=Decimal("30000"),
                numero_factura="F-102",
            ),
        ]
        items = [
            SimpleNamespace(
                cotizacion_id=q_id,
                codigo_material="TUB-01",
                descripcion="Tubo Cobre 1/2",
                grupo_materiales="Tuberías",
                familia="Plomería",
                cantidad_facturada=Decimal("10"),
                importe_facturado=Decimal("25000"),
                cantidad_cotizada=Decimal("10"),
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

        # 2. Check channels with sales exist
        channel_names = [c["canal"] for c in metrics["canales"]]
        self.assertIn("Apartados", channel_names)
        self.assertIn("Kuroda Turbo", channel_names)

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

    def test_delivery_channels_normalized_properly(self):
        self.assertEqual(normalize_channel("ENVÍO A DOMICILIO"), "Envío a Domicilio")
        self.assertEqual(normalize_channel("ENTREGA INMEDIATA"), "Entrega Inmediata")
        self.assertEqual(normalize_channel("PIDE Y RECOGE"), "Pide y Recoge")
        self.assertEqual(normalize_channel("SOBREPEDIDO"), "Sobrepedido")
        self.assertEqual(normalize_channel("CTE RECO EN OTRA SUC"), "Cte Reco en Otra Suc")
        self.assertEqual(normalize_channel("ENVIO POR PAQUETERIA"), "Envío por Paquetería")
        self.assertEqual(normalize_channel("OCURRE"), "Ocurre")
        self.assertEqual(normalize_channel("MERCANCIA RESGUARDO"), "Mercancía Resguardo")


if __name__ == "__main__":
    unittest.main()

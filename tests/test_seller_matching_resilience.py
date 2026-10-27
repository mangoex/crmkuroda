"""Pruebas unitarias para vinculación y resiliencia de vendedores en CRM Kuroda.

Verifica que asesores con nombres truncados por SAP (ej. 'MARIO ALFONSO NAVARR'
por el límite de 20 caracteres) o con asignación por clave ('K96' / grupo_vendedores)
vean reflejadas sus cotizaciones, ventas, metas y analíticas comerciales sin pérdidas.
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest import TestCase
from uuid import uuid4

from app.services.commercial_goals import build_goals_dashboard, _match_seller_by_name, normalize_text


class SellerMatchingResilienceTest(TestCase):
    def test_match_seller_by_name_exact_and_truncated_sap_prefix(self):
        mario_id = str(uuid4())
        lorena_id = str(uuid4())
        sellers_by_name = {
            normalize_text("Mario Alfonso Navarro Gamez"): mario_id,
            normalize_text("Lorena Peraza"): lorena_id,
        }

        # 1. Coincidencia exacta
        self.assertEqual(_match_seller_by_name("Lorena Peraza", sellers_by_name), lorena_id)
        self.assertEqual(_match_seller_by_name("Mario Alfonso Navarro Gamez", sellers_by_name), mario_id)

        # 2. Nombre truncado por SAP a 20 caracteres ('MARIO ALFONSO NAVARR')
        self.assertEqual(_match_seller_by_name("MARIO ALFONSO NAVARR", sellers_by_name), mario_id)

        # 3. Nombre con variaciones de espacios y mayúsculas
        self.assertEqual(_match_seller_by_name("  mario alfonso navarr  ", sellers_by_name), mario_id)

        # 4. Nombre no coincidente devuelve None
        self.assertIsNone(_match_seller_by_name("VENDEDOR INEXISTENTE", sellers_by_name))
        self.assertIsNone(_match_seller_by_name("", sellers_by_name))
        self.assertIsNone(_match_seller_by_name(None, sellers_by_name))

    def test_goals_dashboard_resolves_quotes_by_truncated_sap_name(self):
        mario_id = uuid4()
        mario = SimpleNamespace(
            id=mario_id,
            nombre_completo="Mario Alfonso Navarro Gamez",
            email="mario.navarro@kuroda.com",
            codigo_vendedor=None,  # Aún sin código asignado
        )

        quotes = [
            SimpleNamespace(
                vendedor_id=None,  # Huérfano en importación
                vendedor_nombre="MARIO ALFONSO NAVARR",  # Truncado en SAP
                grupo_vendedores=None,
                organizacion_ventas="MK01",
                numero_factura="FAC-1001",
                importe_facturado=Decimal("15000.00"),
                fecha_registro=date(2026, 10, 23),
                fecha_factura=date(2026, 10, 23),
            )
        ]

        goals = [
            SimpleNamespace(
                tipo="vendedor",
                vendedor_id=mario_id,
                mes=date(2026, 10, 1),
                monto_objetivo=Decimal("500000.00"),
            )
        ]

        dashboard = build_goals_dashboard(
            [mario], quotes, goals, [], date(2026, 10, 23), "dia"
        )

        self.assertEqual(len(dashboard["vendedores"]), 1)
        mario_row = dashboard["vendedores"][0]
        self.assertEqual(mario_row["vendedor_id"], str(mario_id))
        self.assertEqual(mario_row["vendedor"], "Mario Alfonso Navarro Gamez")
        # Debe haber capturado los 15,000 facturados a pesar del nombre truncado
        self.assertEqual(mario_row["venta_facturada"], Decimal("15000.00"))

    def test_goals_dashboard_resolves_quotes_by_vendor_code_k96(self):
        mario_id = uuid4()
        mario = SimpleNamespace(
            id=mario_id,
            nombre_completo="Mario Alfonso Navarro Gamez",
            email="mario.navarro@kuroda.com",
            codigo_vendedor="K96",
        )

        quotes = [
            SimpleNamespace(
                vendedor_id=None,
                vendedor_nombre="OTRO FORMATO O VACIO",
                grupo_vendedores="K96",  # Código SAP
                organizacion_ventas="MK01",
                numero_factura="FAC-1002",
                importe_facturado=Decimal("24968.00"),
                fecha_registro=date(2026, 10, 23),
                fecha_factura=date(2026, 10, 23),
            )
        ]

        goals = [
            SimpleNamespace(
                tipo="vendedor",
                vendedor_id=mario_id,
                mes=date(2026, 10, 1),
                monto_objetivo=Decimal("500000.00"),
            )
        ]

        dashboard = build_goals_dashboard(
            [mario], quotes, goals, [], date(2026, 10, 23), "dia"
        )

        mario_row = dashboard["vendedores"][0]
        self.assertEqual(mario_row["venta_facturada"], Decimal("24968.00"))

    def test_goals_dashboard_prefers_direct_vendedor_id_when_available(self):
        mario_id = uuid4()
        mario = SimpleNamespace(
            id=mario_id,
            nombre_completo="Mario Alfonso Navarro Gamez",
            email="mario.navarro@kuroda.com",
            codigo_vendedor="K96",
        )

        quotes = [
            SimpleNamespace(
                vendedor_id=mario_id,
                vendedor_nombre="MARIO ALFONSO NAVARR",
                grupo_vendedores="K96",
                organizacion_ventas="MK01",
                numero_factura="FAC-1003",
                importe_facturado=Decimal("8500.00"),
                fecha_registro=date(2026, 10, 23),
                fecha_factura=date(2026, 10, 23),
            )
        ]

        dashboard = build_goals_dashboard(
            [mario], quotes, [], [], date(2026, 10, 23), "dia"
        )

        mario_row = dashboard["vendedores"][0]
        self.assertEqual(mario_row["venta_facturada"], Decimal("8500.00"))

import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.schemas.meta_comercial import MetaComercialCreate
from app.services.commercial_goals import (
    build_goals_dashboard,
    commercial_goal_amount,
)


class DummyUser:
    def __init__(self, id, nombre_completo, email, rol="vendedor"):
        self.id = id
        self.nombre_completo = nombre_completo
        self.email = email
        self.rol = rol


class DummyQuote:
    def __init__(self, vendedor_id, vendedor_nombre, organizacion_ventas, canal, numero_factura, importe_facturado, fecha_registro, numero_cliente=None):
        self.vendedor_id = vendedor_id
        self.vendedor_nombre = vendedor_nombre
        self.organizacion_ventas = organizacion_ventas
        self.canal = canal
        self.numero_factura = numero_factura
        self.importe_facturado = Decimal(str(importe_facturado))
        self.fecha_registro = fecha_registro
        self.fecha_factura = fecha_registro
        self.numero_cliente = numero_cliente


class DummyGoal:
    def __init__(self, tipo, mes, monto_objetivo, vendedor_id=None, sucursal=None, canal=None):
        self.tipo = tipo
        self.mes = mes
        self.monto_objetivo = Decimal(str(monto_objetivo))
        self.vendedor_id = vendedor_id
        self.sucursal = sucursal
        self.canal = canal


class CommercialGoalsChannelsTest(unittest.TestCase):
    def setUp(self):
        self.seller_id_1 = uuid4()
        self.seller_id_2 = uuid4()
        self.seller_1 = DummyUser(self.seller_id_1, "Cesar Jahir Lopez", "cesar@kuroda.com")
        self.seller_2 = DummyUser(self.seller_id_2, "Aaron Emigdio Lechug", "aaron@kuroda.com")
        self.sellers = [self.seller_1, self.seller_2]

    def test_schema_allows_canal(self):
        payload = MetaComercialCreate(
            tipo="vendedor",
            vendedor_id=self.seller_id_1,
            mes=date(2026, 8, 1),
            monto_objetivo=Decimal("500000.00"),
            canal="Entrega Inmediata",
            descripcion="Meta para mostrador e inmediata",
        )
        self.assertEqual(payload.canal, "Entrega Inmediata")

    def test_commercial_goal_amount_with_channel(self):
        goal_general = DummyGoal("general", date(2026, 8, 1), "1000000.00", canal=None)
        goal_canal_inmediata = DummyGoal("general", date(2026, 8, 1), "400000.00", canal="Entrega Inmediata")
        goals = [goal_general, goal_canal_inmediata]

        # Without channel filter (general total)
        total, found = commercial_goal_amount(goals, "general", date(2026, 8, 1), date(2026, 8, 31))
        self.assertTrue(found)
        self.assertEqual(total, Decimal("1400000.00"))

        # With channel filter
        total_ch, found_ch = commercial_goal_amount(
            goals, "general", date(2026, 8, 1), date(2026, 8, 31), canal="Entrega Inmediata"
        )
        self.assertTrue(found_ch)
        self.assertEqual(total_ch, Decimal("400000.00"))

    def test_build_goals_dashboard_channel_breakdown_deterministic(self):
        quotes = [
            DummyQuote(
                self.seller_id_1, "Cesar Jahir Lopez", "Matriz", "ENTREGA INMEDIATA", "FAC-001", "300000.00", date(2026, 8, 10)
            ),
            DummyQuote(
                self.seller_id_1, "Cesar Jahir Lopez", "Matriz", "ENVIO A DOMICILIO", "FAC-002", "100000.00", date(2026, 8, 12)
            ),
            DummyQuote(
                self.seller_id_2, "Aaron Emigdio Lechug", "Centro", "ENTREGA INMEDIATA", "FAC-003", "200000.00", date(2026, 8, 15)
            ),
        ]
        goals = [
            DummyGoal("general", date(2026, 8, 1), "600000.00", canal="Entrega Inmediata"),
            DummyGoal("general", date(2026, 8, 1), "400000.00", canal="Envío a Domicilio"),
        ]

        dashboard = build_goals_dashboard(
            self.sellers,
            quotes,
            goals,
            [],
            date(2026, 8, 19),
            "mes",
        )

        self.assertIn("canales", dashboard)
        canales = {c["canal"]: c for c in dashboard["canales"]}

        self.assertIn("Entrega Inmediata", canales)
        self.assertIn("Envío a Domicilio", canales)

        inmediata = canales["Entrega Inmediata"]
        self.assertEqual(inmediata["meta"], 600000.0)
        self.assertEqual(inmediata["venta_facturada"], 500000.0)
        self.assertAlmostEqual(inmediata["cumplimiento"], 83.33, places=1)
        self.assertAlmostEqual(inmediata["pct_meta_total"], 60.0, places=1)
        self.assertAlmostEqual(inmediata["pct_venta_total"], 83.33, places=1)

        domicilio = canales["Envío a Domicilio"]
        self.assertEqual(domicilio["meta"], 400000.0)
        self.assertEqual(domicilio["venta_facturada"], 100000.0)
        self.assertAlmostEqual(domicilio["cumplimiento"], 25.0, places=1)
        self.assertAlmostEqual(domicilio["pct_meta_total"], 40.0, places=1)
        self.assertAlmostEqual(domicilio["pct_venta_total"], 16.67, places=1)


if __name__ == "__main__":
    unittest.main()

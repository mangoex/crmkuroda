from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest import TestCase
from uuid import uuid4
from pathlib import Path

from app.schemas.meta_comercial import MetaComercialCreate
from app.services.commercial_goals import (
    build_goals_dashboard,
    period_bounds,
    prorated_monthly_amount,
)


class CommercialGoalsTests(TestCase):
    def test_monthly_goal_prorates_for_day_and_week(self):
        month = date(2026, 8, 1)
        self.assertEqual(
            prorated_monthly_amount(Decimal("3100"), month, date(2026, 8, 6), date(2026, 8, 6)),
            Decimal("100"),
        )
        start, end = period_bounds(date(2026, 8, 6), "semana")
        self.assertEqual(start, date(2026, 8, 3))
        self.assertEqual(end, date(2026, 8, 9))
        self.assertEqual(
            prorated_monthly_amount(Decimal("3100"), month, start, end),
            Decimal("700"),
        )

    def test_dashboard_uses_new_vendor_goal_and_branch_from_sales_organization(self):
        seller_id = uuid4()
        seller = SimpleNamespace(id=seller_id, nombre_completo="Ana Asesora", email="ana@example.com")
        quotes = [
            SimpleNamespace(
                vendedor_id=seller_id,
                vendedor_nombre=None,
                organizacion_ventas="Sucursal Centro",
                numero_factura="F-1",
                importe_facturado=Decimal("100"),
                fecha_registro=date(2026, 8, 6),
                fecha_factura=date(2026, 8, 6),
            )
        ]
        goals = [
            SimpleNamespace(tipo="general", mes=date(2026, 8, 1), monto_objetivo=Decimal("6200")),
            SimpleNamespace(tipo="vendedor", vendedor_id=seller_id, mes=date(2026, 8, 1), monto_objetivo=Decimal("3100")),
            SimpleNamespace(tipo="sucursal", sucursal="Sucursal Centro", mes=date(2026, 8, 1), monto_objetivo=Decimal("4650")),
        ]

        dashboard = build_goals_dashboard(
            [seller], quotes, goals, [], date(2026, 8, 6), "dia"
        )

        self.assertEqual(dashboard["general"]["meta"], 200.0)
        self.assertEqual(dashboard["general"]["venta_facturada"], 100.0)
        self.assertEqual(dashboard["vendedores"][0]["meta"], 100.0)
        self.assertEqual(dashboard["vendedores"][0]["origen_meta"], "comercial")
        self.assertEqual(dashboard["sucursales"][0]["sucursal"], "Sucursal Centro")
        self.assertEqual(dashboard["sucursales"][0]["meta"], 150.0)

    def test_dashboard_falls_back_to_legacy_vendor_goal_without_new_goal(self):
        seller_id = uuid4()
        seller = SimpleNamespace(id=seller_id, nombre_completo="Ana Asesora", email="ana@example.com")
        legacy = SimpleNamespace(
            vendedor_id=seller_id,
            monto_objetivo=Decimal("3100"),
            fecha_inicio=date(2026, 8, 1),
            fecha_limite=date(2026, 8, 31),
        )

        dashboard = build_goals_dashboard(
            [seller], [], [], [legacy], date(2026, 8, 6), "dia"
        )

        self.assertEqual(dashboard["vendedores"][0]["meta"], 100.0)
        self.assertEqual(dashboard["vendedores"][0]["origen_meta"], "legada")

    def test_schema_rejects_invalid_scope_and_non_month_start(self):
        with self.assertRaises(ValueError):
            MetaComercialCreate(
                tipo="vendedor",
                mes=date(2026, 8, 2),
                monto_objetivo="100",
            )
        with self.assertRaises(ValueError):
            MetaComercialCreate(
                tipo="sucursal",
                mes=date(2026, 8, 1),
                monto_objetivo="100",
                vendedor_id=uuid4(),
                sucursal="Centro",
            )

    def test_frontend_and_api_contract_expose_manager_section_and_seller_progress(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "static" / "index.html").read_text(encoding="utf-8")
        script = (root / "static" / "app.js").read_text(encoding="utf-8")
        routes = (root / "app" / "api" / "v1" / "metas_comerciales.py").read_text(encoding="utf-8")

        self.assertIn('data-section="metas"', html)
        self.assertIn('id="section-metas"', html)
        self.assertIn('id="metas-period"', html)
        self.assertIn('"metas"', script)
        self.assertIn('DOM.menuMetas?.classList.add("hidden")', script)
        self.assertIn('/api/v1/metas/comerciales/mis-avances', script)
        self.assertIn('@router.get("/comerciales/dashboard")', routes)
        self.assertIn('@router.get("/comerciales/mis-avances")', routes)

    def test_period_normalization_accepts_english_and_spanish_aliases(self):
        for alias in ["dia", "day", "diario", "diaria"]:
            start, end = period_bounds(date(2026, 8, 14), alias)
            self.assertEqual(start, date(2026, 8, 14))
            self.assertEqual(end, date(2026, 8, 14))

        for alias in ["semana", "week", "semanal"]:
            start, end = period_bounds(date(2026, 8, 14), alias)
            self.assertEqual(start, date(2026, 8, 10))
            self.assertEqual(end, date(2026, 8, 16))

        for alias in ["mes", "month", "mensual"]:
            start, end = period_bounds(date(2026, 8, 14), alias)
            self.assertEqual(start, date(2026, 8, 1))
            self.assertEqual(end, date(2026, 8, 31))

    def test_dashboard_matches_string_and_uuid_vendor_goals(self):
        seller_id = uuid4()
        seller = SimpleNamespace(id=seller_id, nombre_completo="Patricia Chavez", email="patricia@example.com")
        quotes = [
            SimpleNamespace(
                vendedor_id=str(seller_id),
                vendedor_nombre="Patricia Chavez",
                organizacion_ventas="Sucursal Norte",
                numero_factura="F-99",
                importe_facturado=Decimal("114818"),
                fecha_registro=date(2026, 8, 14),
                fecha_factura=date(2026, 8, 14),
            )
        ]
        goals = [
            SimpleNamespace(tipo="vendedor", vendedor_id=str(seller_id), mes=date(2026, 8, 1), monto_objetivo=Decimal("200000")),
        ]

        dashboard = build_goals_dashboard([seller], quotes, goals, [], date(2026, 8, 14), "month")
        self.assertEqual(len(dashboard["vendedores"]), 1)
        row = dashboard["vendedores"][0]
        self.assertEqual(row["vendedor_id"], str(seller_id))
        self.assertEqual(row["meta"], 200000.0)
        self.assertEqual(row["venta_facturada"], 114818.0)
        self.assertEqual(row["cumplimiento"], 57.41)
        self.assertEqual(row["origen_meta"], "comercial")

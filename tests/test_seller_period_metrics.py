"""TDD Unit test suite for seller period metrics calculation and conversion rate filtering."""

import unittest
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.services.commercial_analytics import calculate_seller_period_metrics
from app.services.commercial_goals import period_bounds


class TestSellerPeriodMetrics(unittest.TestCase):
    def setUp(self):
        self.ref_date = date(2026, 8, 21) # Viernes
        self.quotes = [
            # Cotización de ayer (2026-08-20), facturada
            SimpleNamespace(
                id="q1",
                fecha_registro=date(2026, 8, 20),
                fecha_factura=date(2026, 8, 20),
                numero_factura="F-1001",
                total=Decimal("1000.00"),
                importe_facturado=Decimal("1000.00"),
            ),
            # Cotización de hoy (2026-08-21), facturada
            SimpleNamespace(
                id="q2",
                fecha_registro=date(2026, 8, 21),
                fecha_factura=date(2026, 8, 21),
                numero_factura="F-1002",
                total=Decimal("2000.00"),
                importe_facturado=Decimal("2000.00"),
            ),
            # Cotización de hoy (2026-08-21), pendiente / no facturada
            SimpleNamespace(
                id="q3",
                fecha_registro=date(2026, 8, 21),
                fecha_factura=None,
                numero_factura=None,
                total=Decimal("3000.00"),
                importe_facturado=Decimal("0.00"),
            ),
            # Cotización del mes pasado (2026-07-15), facturada
            SimpleNamespace(
                id="q4",
                fecha_registro=date(2026, 7, 15),
                fecha_factura=date(2026, 7, 15),
                numero_factura="F-999",
                total=Decimal("5000.00"),
                importe_facturado=Decimal("5000.00"),
            ),
        ]

    def test_daily_period_metrics(self):
        """Día: Sólo q2 (facturada) y q3 (pendiente) deben contarse."""
        start, end = period_bounds(self.ref_date, "dia")
        metrics = calculate_seller_period_metrics(self.quotes, start, end)

        self.assertEqual(metrics["total_quotes"], 2)
        self.assertEqual(metrics["invoiced_quotes"], 1)
        self.assertEqual(metrics["total_quoted"], 5000.00) # 2000 + 3000
        self.assertEqual(metrics["total_invoiced"], 2000.00)
        self.assertEqual(metrics["conversion_rate"], 50.00) # 1 de 2 = 50%

    def test_weekly_period_metrics(self):
        """Semana: q1 (ayer), q2 (hoy) y q3 (hoy) pertenecen a la misma semana."""
        start, end = period_bounds(self.ref_date, "semana")
        metrics = calculate_seller_period_metrics(self.quotes, start, end)

        self.assertEqual(metrics["total_quotes"], 3)
        self.assertEqual(metrics["invoiced_quotes"], 2) # q1 y q2
        self.assertEqual(metrics["total_quoted"], 6000.00) # 1000 + 2000 + 3000
        self.assertEqual(metrics["total_invoiced"], 3000.00) # 1000 + 2000
        self.assertEqual(round(metrics["conversion_rate"], 2), 66.67) # 2/3 = 66.67%

    def test_monthly_period_metrics(self):
        """Mes: q1, q2 y q3 pertenecen a Agosto 2026. q4 es de Julio."""
        start, end = period_bounds(self.ref_date, "mes")
        metrics = calculate_seller_period_metrics(self.quotes, start, end)

        self.assertEqual(metrics["total_quotes"], 3)
        self.assertEqual(metrics["invoiced_quotes"], 2)
        self.assertEqual(metrics["total_quoted"], 6000.00)
        self.assertEqual(metrics["total_invoiced"], 3000.00)
        self.assertEqual(round(metrics["conversion_rate"], 2), 66.67)

    def test_empty_period_zero_division(self):
        """Periodo sin cotizaciones debe retornar 0.00% sin lanzar ZeroDivisionError."""
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)
        metrics = calculate_seller_period_metrics(self.quotes, start, end)

        self.assertEqual(metrics["total_quotes"], 0)
        self.assertEqual(metrics["invoiced_quotes"], 0)
        self.assertEqual(metrics["total_quoted"], 0.00)
        self.assertEqual(metrics["total_invoiced"], 0.00)
        self.assertEqual(metrics["conversion_rate"], 0.00)


if __name__ == "__main__":
    unittest.main()

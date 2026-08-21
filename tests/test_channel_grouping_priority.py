"""TDD Unit tests for strategic vs logistic channel separation and prioritization."""

import unittest
from decimal import Decimal
from types import SimpleNamespace

from app.services.commercial_analytics import (
    STRATEGIC_CHANNELS,
    LOGISTIC_CHANNELS,
    CANONICAL_CHANNELS,
    build_seller_dashboard_metrics,
)


class TestChannelGroupingPriority(unittest.TestCase):
    def test_canonical_channels_contain_strategic_and_logistic(self):
        """Verifica que los 5 canales estratégicos y los de logística estén definidos."""
        expected_strategic = {"Apartados", "Kuroda Turbo", "Material D", "Promociones", "Market place"}
        self.assertEqual(set(STRATEGIC_CHANNELS), expected_strategic)
        for sc in STRATEGIC_CHANNELS:
            self.assertIn(sc, CANONICAL_CHANNELS)
        for lc in LOGISTIC_CHANNELS:
            self.assertIn(lc, CANONICAL_CHANNELS)

    def test_seller_dashboard_metrics_separates_strategic_and_logistic(self):
        """Verifica que build_seller_dashboard_metrics identifique y agrupe canales estratégicos."""
        quotes = [
            SimpleNamespace(
                id="q1",
                canal="Apartados",
                numero_cliente="400260",
                total=Decimal("15000.00"),
                importe_facturado=Decimal("15000.00"),
                numero_factura="F-101",
                fecha_registro=None,
                fecha_factura=None,
            ),
            SimpleNamespace(
                id="q2",
                canal="Envío a Domicilio",
                numero_cliente="10001",
                total=Decimal("5000.00"),
                importe_facturado=Decimal("5000.00"),
                numero_factura="F-102",
                fecha_registro=None,
                fecha_factura=None,
            ),
            SimpleNamespace(
                id="q3",
                canal="Kuroda Turbo",
                numero_cliente="10002",
                total=Decimal("8000.00"),
                importe_facturado=Decimal("8000.00"),
                numero_factura="F-103",
                fecha_registro=None,
                fecha_factura=None,
            ),
        ]
        metrics = build_seller_dashboard_metrics(quotes)
        
        self.assertIn("canales_estrategicos", metrics)
        self.assertIn("canales_logisticos", metrics)
        
        strategic_names = [c["canal"] for c in metrics["canales_estrategicos"]]
        logistic_names = [c["canal"] for c in metrics["canales_logisticos"]]
        
        self.assertEqual(set(strategic_names), set(STRATEGIC_CHANNELS))
        self.assertEqual(set(logistic_names), set(LOGISTIC_CHANNELS))
        
        # Apartados debe tener monto 15000
        apartados = next(c for c in metrics["canales_estrategicos"] if c["canal"] == "Apartados")
        self.assertEqual(apartados["monto"], 15000.00)
        
        # Kuroda Turbo debe tener monto 8000
        turbo = next(c for c in metrics["canales_estrategicos"] if c["canal"] == "Kuroda Turbo")
        self.assertEqual(turbo["monto"], 8000.00)
        
        # Envío a Domicilio debe estar en logísticos con monto 5000
        domicilio = next(c for c in metrics["canales_logisticos"] if c["canal"] == "Envío a Domicilio")
        self.assertEqual(domicilio["monto"], 5000.00)


if __name__ == "__main__":
    unittest.main()

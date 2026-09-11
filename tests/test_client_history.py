"""Unit tests for app.services.client_history_service."""

from __future__ import annotations

import unittest
from datetime import date
from types import SimpleNamespace

from app.services.client_history_service import build_client_history


def _quote(**kwargs):
    """Convenience factory for duck-typed quote objects."""
    defaults = dict(
        id="q1",
        vendedor_id=None,
        cliente_nombre="Acme Corp",
        numero_cliente="1001",
        datos_contacto={"telefono": "6671234567", "celular": "6679876543", "email": "a@b.com"},
        items=None,
        total=1000,
        texto_propuesta=None,
        numero_cotizacion="C-001",
        fecha_registro=date(2026, 6, 15),
        canal="Apartados",
        numero_factura=None,
        fecha_factura=None,
        importe_facturado=None,
        venta_perdida=None,
        comentarios=None,
        vendedor_nombre="Vendedor A",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class ClientHistoryTest(unittest.TestCase):
    """Tests for build_client_history()."""

    def test_empty_quotes_returns_zeros(self):
        result = build_client_history("1001", [])
        self.assertEqual(result["numero_cliente"], "1001")
        self.assertIsNone(result["cliente_nombre"])
        self.assertEqual(result["resumen"]["total_cotizaciones"], 0)
        self.assertEqual(result["resumen"]["importe_cotizado"], 0)
        self.assertEqual(result["resumen"]["importe_facturado"], 0)
        self.assertEqual(result["operaciones"], [])

    def test_single_pending_quote(self):
        quotes = [_quote()]
        result = build_client_history("1001", quotes, today=date(2026, 7, 1))
        self.assertEqual(result["resumen"]["total_cotizaciones"], 1)
        self.assertEqual(result["resumen"]["total_pendientes"], 1)
        self.assertEqual(result["resumen"]["total_facturadas"], 0)
        self.assertEqual(result["operaciones"][0]["estado"], "Pendiente")

    def test_invoiced_quote(self):
        quotes = [_quote(numero_factura="F-100", importe_facturado=800)]
        result = build_client_history("1001", quotes)
        self.assertEqual(result["resumen"]["total_facturadas"], 1)
        self.assertEqual(result["resumen"]["importe_facturado"], 800)
        self.assertEqual(result["operaciones"][0]["estado"], "Facturado")

    def test_lost_sale(self):
        quotes = [_quote(venta_perdida="Si")]
        result = build_client_history("1001", quotes)
        self.assertEqual(result["resumen"]["total_perdidas"], 1)
        self.assertEqual(result["operaciones"][0]["estado"], "Venta Perdida")

    def test_expired_quote(self):
        quotes = [_quote(fecha_registro=date(2026, 1, 1))]
        result = build_client_history("1001", quotes, today=date(2026, 7, 1))
        self.assertEqual(result["resumen"]["total_expiradas"], 1)
        self.assertEqual(result["operaciones"][0]["estado"], "Expirada")

    def test_conversion_rate(self):
        quotes = [
            _quote(id="q1", numero_factura="F-1", importe_facturado=500),
            _quote(id="q2"),
            _quote(id="q3", numero_factura="F-3", importe_facturado=300),
            _quote(id="q4", venta_perdida="Si"),
        ]
        result = build_client_history("1001", quotes, today=date(2026, 7, 1))
        self.assertEqual(result["resumen"]["total_cotizaciones"], 4)
        self.assertEqual(result["resumen"]["total_facturadas"], 2)
        self.assertEqual(result["resumen"]["tasa_conversion"], 50.0)

    def test_filters_by_numero_cliente(self):
        quotes = [
            _quote(id="q1", numero_cliente="1001"),
            _quote(id="q2", numero_cliente="2002"),
            _quote(id="q3", numero_cliente="1001"),
        ]
        result = build_client_history("1001", quotes)
        self.assertEqual(result["resumen"]["total_cotizaciones"], 2)

    def test_operations_sorted_newest_first(self):
        quotes = [
            _quote(id="q1", fecha_registro=date(2026, 1, 1)),
            _quote(id="q2", fecha_registro=date(2026, 6, 15)),
            _quote(id="q3", fecha_registro=date(2026, 3, 10)),
        ]
        result = build_client_history("1001", quotes)
        dates = [op["fecha_registro"] for op in result["operaciones"]]
        self.assertEqual(dates, ["2026-06-15", "2026-03-10", "2026-01-01"])

    def test_contact_normalization(self):
        quotes = [_quote(datos_contacto={"celular": "6679876543", "telefono": "6671234567"})]
        result = build_client_history("1001", quotes)
        contact = result["operaciones"][0]["contacto"]
        self.assertEqual(contact["contacto_preferente"], "6679876543")
        self.assertEqual(contact["tipo_contacto_preferente"], "celular")

    def test_importe_totals_are_summed(self):
        quotes = [
            _quote(id="q1", total=1000, numero_factura="F-1", importe_facturado=800),
            _quote(id="q2", total=2000, numero_factura="F-2", importe_facturado=1500),
        ]
        result = build_client_history("1001", quotes)
        self.assertEqual(result["resumen"]["importe_cotizado"], 3000)
        self.assertEqual(result["resumen"]["importe_facturado"], 2300)

    def test_cliente_nombre_resolved_from_first_match(self):
        quotes = [
            _quote(id="q1", cliente_nombre="Acme Corp", fecha_registro=date(2026, 6, 1)),
            _quote(id="q2", cliente_nombre="ACME CORP S.A.", fecha_registro=date(2026, 7, 1)),
        ]
        result = build_client_history("1001", quotes)
        # Newest first, so second quote's name appears first
        self.assertEqual(result["cliente_nombre"], "ACME CORP S.A.")

    def test_projected_quote_without_heavy_columns(self):
        """Simulate SQLAlchemy load_only where items, texto_propuesta, etc. are not loaded."""
        class ProjectedQuote:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        quote = ProjectedQuote(
            id="q-proj",
            numero_cliente="400191",
            cliente_nombre="MERCADO",
            total=1500.50,
            importe_facturado=1500.50,
            numero_factura="FAC-999",
            fecha_registro=date(2026, 8, 1),
            fecha_factura=date(2026, 8, 2),
            canal="Sucursal",
            venta_perdida=None,
            vendedor_nombre="Asesor Kuroda",
            datos_contacto={"telefono": "6670000000"},
            numero_cotizacion="COT-12345",
        )
        result = build_client_history("400191", [quote])
        self.assertEqual(result["resumen"]["total_cotizaciones"], 1)
        self.assertEqual(result["resumen"]["total_facturadas"], 1)
        self.assertEqual(result["resumen"]["importe_cotizado"], 1500.50)
        self.assertEqual(result["resumen"]["importe_facturado"], 1500.50)
        self.assertEqual(result["operaciones"][0]["estado"], "Facturado")

    def test_high_volume_exact_aggregation(self):
        """Ensure calculations remain 100% exact with thousands of quotes (like MERCADO 15k+)."""
        quotes = []
        for i in range(1000):
            # 500 invoiced, 300 expired, 200 pending
            if i < 500:
                q = _quote(id=f"q{i}", total=100, importe_facturado=100, numero_factura=f"F-{i}", fecha_registro=date(2026, 5, 1))
            elif i < 800:
                q = _quote(id=f"q{i}", total=50, fecha_registro=date(2026, 1, 1)) # expired
            else:
                q = _quote(id=f"q{i}", total=25, fecha_registro=date(2026, 6, 25)) # pending
            quotes.append(q)

        result = build_client_history("1001", quotes, today=date(2026, 7, 1))
        self.assertEqual(result["resumen"]["total_cotizaciones"], 1000)
        self.assertEqual(result["resumen"]["total_facturadas"], 500)
        self.assertEqual(result["resumen"]["total_expiradas"], 300)
        self.assertEqual(result["resumen"]["total_pendientes"], 200)
        # 500*100 + 300*50 + 200*25 = 50000 + 15000 + 5000 = 70000
        self.assertEqual(result["resumen"]["importe_cotizado"], 70000.0)
        self.assertEqual(result["resumen"]["importe_facturado"], 50000.0)
        self.assertEqual(result["resumen"]["tasa_conversion"], 50.0)


if __name__ == "__main__":
    unittest.main()


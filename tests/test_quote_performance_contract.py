import unittest
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.api.v1.cotizaciones import (
    _stale_imported_quote_ids,
    serialize_cotizacion,
)


ROOT = Path(__file__).resolve().parents[1]


def build_quote(numero_cotizacion="COT-1"):
    return SimpleNamespace(
        id=uuid4(),
        vendedor_id=None,
        vendedor_nombre="Asesor histórico",
        cliente_nombre="Cliente de prueba",
        numero_cliente="CL-9",
        datos_contacto={"celular": "6671234567"},
        items=[{"producto": "Pesado"}],
        total=123.45,
        texto_propuesta="Propuesta pesada",
        numero_cotizacion=numero_cotizacion,
        fecha_registro=None,
        canal="Directo",
        numero_factura=None,
        fecha_factura=None,
        importe_facturado=None,
        venta_perdida="No",
        comentarios=None,
    )


class QuotePerformanceContractTest(unittest.TestCase):
    def test_summary_view_omits_heavy_quote_fields(self):
        payload = serialize_cotizacion(build_quote(), vista="resumen")

        self.assertNotIn("items", payload)
        self.assertNotIn("items_detalle", payload)
        self.assertNotIn("texto_propuesta", payload)
        self.assertEqual(payload["cliente_nombre"], "Cliente de prueba")

    def test_excel_reconciliation_preserves_manual_quotes_without_folio(self):
        imported_present = build_quote("COT-1")
        imported_missing = build_quote("COT-2")
        manual_quote = build_quote(None)

        stale_ids = _stale_imported_quote_ids(
            [imported_present, imported_missing, manual_quote],
            {imported_present.id},
        )

        self.assertEqual(stale_ids, {imported_missing.id})

    def test_frontend_uses_bounded_summary_requests_for_quotes_and_kanban(self):
        javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

        self.assertNotIn('limit=20000', javascript)
        self.assertIn('vista: "resumen"', javascript)
        self.assertIn('limit: String(state.quotesPageSize)', javascript)

    def test_api_contract_limits_operational_pages_and_exposes_server_filters(self):
        quotes_api = (ROOT / "app" / "api" / "v1" / "cotizaciones.py").read_text(
            encoding="utf-8"
        )

        self.assertIn('MAX_OPERATIONAL_PAGE_SIZE = 100', quotes_api)
        self.assertIn('le=MAX_OPERATIONAL_PAGE_SIZE', quotes_api)
        self.assertIn('busqueda:', quotes_api)
        self.assertIn('total_min:', quotes_api)
        self.assertIn('edad_max_dias:', quotes_api)
        self.assertIn('estado:', quotes_api)
        self.assertIn('vista:', quotes_api)

    def test_performance_indexes_are_managed_by_alembic(self):
        migrations = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "alembic" / "versions").glob("*.py"))
        )

        self.assertIn('ix_cotizaciones_vendedor_fecha', migrations)
        self.assertIn('ix_cotizaciones_fecha_numero', migrations)


if __name__ == "__main__":
    unittest.main()

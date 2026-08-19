import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InvoiceGroupingContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        cls.javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

    def test_css_contains_invoice_grouping_styles(self):
        self.assertIn(".tr-invoice-group-header", self.css)
        self.assertIn(".tr-invoice-child-row", self.css)
        self.assertIn(".badge-invoice-count", self.css)

    def test_por_entregar_has_grouping_controls(self):
        self.assertIn("btn-toggle-all-pe-invoices", self.html)
        self.assertIn("groupRecordsByInvoice", self.javascript)
        self.assertIn("toggleInvoiceGroup", self.javascript)

    def test_sobrepedidos_table_structure_exists(self):
        self.assertIn("table-sobrepedidos", self.html)
        self.assertIn("loadSobrepedidosData", self.javascript)

    def test_material_analytics_has_grouping_support(self):
        self.assertIn("table-material-analytics", self.html)


if __name__ == "__main__":
    unittest.main()

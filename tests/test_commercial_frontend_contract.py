import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CommercialFrontendContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        cls.javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        cls.quotes_api = (ROOT / "app" / "api" / "v1" / "cotizaciones.py").read_text(
            encoding="utf-8"
        )

    def test_sidebar_has_fixed_order_contract(self):
        self.assertNotIn("drag-handle", self.html)
        self.assertNotIn("item.draggable = true", self.javascript)
        self.assertNotIn("applyStoredMenuOrder();", self.javascript)

    def test_quick_period_controls_exist(self):
        for element_id in (
            "filter-quote-today",
            "filter-quote-month",
            "filter-quote-all",
            "filter-quote-period-status",
        ):
            self.assertIn(f'id="{element_id}"', self.html)

    def test_comment_history_contract_exists(self):
        self.assertIn('id="quote-comments-modal"', self.html)
        self.assertIn("openQuoteCommentsModal", self.javascript)
        self.assertIn("comentarios_seguimiento_count", self.javascript)
        self.assertIn("quote-comment-edit-btn", self.javascript)

    def test_material_analytics_and_detail_upload_exist(self):
        self.assertIn('id="table-material-analytics"', self.html)
        self.assertIn('id="file-upload-cotizacion-items"', self.html)
        self.assertIn("/detalle-materiales/upload", self.javascript)
        self.assertIn("material-group-toggle", self.javascript)

    def test_management_filters_and_unlinked_seller_exist(self):
        self.assertIn('id="coordinator-performance-start"', self.html)
        self.assertIn('id="coordinator-performance-end"', self.html)
        self.assertIn('"__unlinked__"', self.javascript)

    def test_kanban_does_not_infer_promotions_from_description(self):
        self.assertIn("q.tiene_promocion === true", self.javascript)
        self.assertNotIn("prodName.includes((p.descripcion_material", self.javascript)

    def test_static_upload_routes_precede_dynamic_uuid_route(self):
        detail_position = self.quotes_api.index('@router.post("/detalle-materiales/upload"')
        upload_position = self.quotes_api.index('@router.post("/upload"')
        uuid_position = self.quotes_api.index('@router.get("/{cotizacion_id}"')

        self.assertLess(detail_position, uuid_position)
        self.assertLess(upload_position, uuid_position)


if __name__ == "__main__":
    unittest.main()

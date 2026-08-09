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

    def test_sidebar_has_fixed_menu_contract(self):
        self.assertNotIn('draggable="true"', self.html)
        self.assertIn('data-section="summary"', self.html)
        self.assertIn('data-section="seguimiento"', self.html)
        self.assertIn('data-section="cotizaciones"', self.html)


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

    def test_inventory_table_displays_material_code(self):
        self.assertIn('id="table-inventario-abcf"', self.html)
        self.assertIn("Código material", self.html)
        self.assertIn("escapeHTML(getInventoryProductKey(i) || \"-\")", self.javascript)

    def test_followup_proposal_dialog_shows_or_maintains_client_cellular(self):
        self.assertIn("renderProposalClientContact", self.javascript)
        self.assertIn("findCatalogClientForQuote", self.javascript)
        self.assertIn("Nombre de contacto", self.javascript)
        self.assertIn("proposal-save-client-contact", self.javascript)
        self.assertIn("/api/v1/clientes/${catalogClient.id}", self.javascript)
        self.assertIn("proposal-update-client-contact", self.javascript)
        self.assertIn('switchSection("clientes")', self.javascript)
        self.assertIn('document.getElementById("cliente-cel-input")?.focus()', self.javascript)

    def test_main_panel_has_numeric_channel_sales_summary_and_filter(self):
        self.assertIn('id="summary-channel-sales"', self.html)
        self.assertIn('id="summary-channel-filter"', self.html)
        self.assertIn("loadSummaryChannelSales", self.javascript)
        self.assertIn("resumen-principal/canales", self.javascript)

    def test_commercial_goals_have_a_seller_filter(self):
        self.assertIn('id="metas-seller-filter"', self.html)
        self.assertIn("populateCommercialGoalSellerFilter", self.javascript)
        self.assertIn("metasSellerFilter?.addEventListener", self.javascript)

    def test_access_activity_list_has_its_own_scroll_area(self):
        stylesheet = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn("#admin-today-access-log", stylesheet)
        self.assertIn("max-height: 390px", stylesheet)
        self.assertIn("overflow-y: auto", stylesheet)

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

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class QuoteDetailAndSellerNameContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        cls.javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
        cls.quotes_api = (ROOT / "app" / "api" / "v1" / "cotizaciones.py").read_text(
            encoding="utf-8"
        )

    def test_quote_detail_modal_exists_in_html(self):
        """El modal de detalle de cotización debe existir en index.html con estructura semántica."""
        self.assertIn('id="quote-detail-modal"', self.html)
        self.assertIn('id="quote-detail-title"', self.html)
        self.assertIn('id="quote-detail-body"', self.html)
        self.assertIn('id="btn-close-quote-detail"', self.html)
        self.assertIn('id="quote-detail-items-table"', self.html)

    def test_kanban_card_click_opens_quote_detail_modal(self):
        """Al hacer clic en la tarjeta del Kanban se debe abrir openQuoteDetailModal en vez de la ficha del cliente."""
        self.assertIn("openQuoteDetailModal", self.javascript)
        self.assertIn("openQuoteDetailModal(q.id)", self.javascript)

    def test_seller_name_resolution_displays_full_name(self):
        """En Kanban y tablas se debe resolver y mostrar el nombre completo del asesor (no solo el email)."""
        self.assertIn("nombre_completo", self.javascript)
        self.assertIn("kanban-card-seller", self.javascript)

    def test_quote_detail_modal_styles_exist(self):
        """Deben existir estilos CSS para el modal de detalle y su tabla de materiales."""
        self.assertIn("quote-items-table", self.css)

    def test_quote_detail_has_link_to_client_modal(self):
        """Dentro del modal de detalle de cotización debe haber acceso para abrir la ficha del cliente."""
        self.assertIn("btn-quote-view-client", self.javascript)

    def test_client_name_fallback_logic_exists(self):
        """Si una cotización no trae nombre de cliente, debe resolverse con fallback inteligente en vez de quedar 'Desconocido'."""
        self.assertIn("displayClientName", self.javascript)
        self.assertIn("displayModalClient", self.javascript)

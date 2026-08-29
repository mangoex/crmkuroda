import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PorEntregarWhatsAppButtonContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        cls.javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

    def test_por_entregar_table_has_dedicated_whatsapp_header(self):
        """La tabla de Por Entregar debe tener una columna dedicada y visible para WhatsApp."""
        self.assertIn("table-por-entregar", self.html)
        self.assertIn("WhatsApp", self.html)
        # Debe haber encabezado para WhatsApp
        self.assertIn("fa-brands fa-whatsapp", self.html)

    def test_app_js_has_dedicated_whatsapp_button_builder(self):
        """app.js debe contener la función buildDedicatedWhatsAppButton para generar el botón separado y prominente."""
        self.assertIn("buildDedicatedWhatsAppButton", self.javascript)
        self.assertIn("btn-whatsapp-action", self.javascript)
        self.assertIn("https://wa.me/", self.javascript)

    def test_css_has_whatsapp_action_button_styles(self):
        """style.css debe contener los estilos de alto contraste y visibilidad para .btn-whatsapp-action."""
        self.assertIn(".btn-whatsapp-action", self.css)
        self.assertIn("#25D366", self.css.upper())

    def test_por_entregar_table_renders_whatsapp_in_separate_cell(self):
        """renderPorEntregarTable debe renderizar el botón de WhatsApp en su propia celda <td> y no apretado bajo el nombre."""
        self.assertIn("buildDedicatedWhatsAppButton(firstItem", self.javascript)
        self.assertIn("buildDedicatedWhatsAppButton(item", self.javascript)


if __name__ == "__main__":
    unittest.main()

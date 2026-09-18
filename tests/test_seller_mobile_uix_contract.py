import unittest
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


class SellerMobileUixContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
        cls.javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    def test_seller_mobile_html_structure_exists(self):
        # Contenedor raiz movil del vendedor
        self.assertIn('id="seller-mobile-view"', self.html)
        
        # 3 Pestanas esenciales
        self.assertIn('id="seller-mobile-tab-actividades"', self.html)
        self.assertIn('id="seller-mobile-tab-promociones"', self.html)
        self.assertIn('id="seller-mobile-tab-entregas"', self.html)
        
        # Dock de navegacion flotante con 3 opciones
        self.assertIn('id="seller-mobile-dock"', self.html)
        self.assertIn('data-seller-tab="actividades"', self.html)
        self.assertIn('data-seller-tab="promociones"', self.html)
        self.assertIn('data-seller-tab="entregas"', self.html)

    def test_seller_mobile_css_isolation_and_dock_styling(self):
        # Verificacion de estilos aislados para role-vendedor en movil
        self.assertIn(".role-vendedor", self.css)
        self.assertIn(".seller-mobile-dock", self.css)
        self.assertIn(".seller-mobile-view", self.css)
        
        # Estilos de dock flotante desacoplado
        self.assertIn("border-radius", self.css)
        self.assertIn("backdrop-filter", self.css)

    def test_seller_mobile_javascript_functions_exist(self):
        # Funciones controladoras de tabs y vistas moviles del vendedor
        self.assertIn("switchSellerMobileTab", self.javascript)
        self.assertIn("renderSellerMobileActividades", self.javascript)
        self.assertIn("renderSellerMobilePromociones", self.javascript)
        self.assertIn("renderSellerMobileEntregas", self.javascript)

    def test_javascript_syntax_is_valid(self):
        res = subprocess.run(["node", "-c", str(ROOT / "static" / "app.js")], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"JavaScript syntax error: {res.stderr}")


if __name__ == "__main__":
    unittest.main()

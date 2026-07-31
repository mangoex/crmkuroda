import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LightUixContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
        cls.javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    def test_light_mode_is_default_and_dark_section_removed(self):
        self.assertIn('<body class="light-mode">', self.html)
        self.assertNotIn("DARK UIX 2.0", self.css)
        self.assertNotIn("body:not(.light-mode)", self.css)

    def test_light_mode_tokens_and_base_variables_exist(self):
        for token in (
            "--bg-primary",
            "--bg-secondary",
            "--card-bg",
            "--text-primary",
            "--text-secondary",
            "--border-color",
        ):
            self.assertIn(token, self.css)

    def test_core_application_surfaces_have_light_styling(self):
        for selector in (
            ".auth-wrapper",
            ".sidebar-container",
            ".top-navbar",
            ".glass-card",
            ".data-table",
            ".kanban-column",
            ".modal-card",
            ".seller-home-dashboard",
        ):
            self.assertIn(selector, self.css)

    def test_theme_toggle_is_disabled_in_js(self):
        self.assertIn('document.body.classList.add("light-mode")', self.javascript)

    def test_stylesheet_cache_version_was_bumped(self):
        self.assertIn("/static/style.css?v=1.0.15", self.html)


if __name__ == "__main__":
    unittest.main()

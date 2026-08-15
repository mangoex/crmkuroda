import os
import unittest


class LightUixContractTest(unittest.TestCase):
    def setUp(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.html_path = os.path.join(repo_root, "static", "index.html")
        self.css_path = os.path.join(repo_root, "static", "style.css")
        self.js_path = os.path.join(repo_root, "static", "app.js")

        with open(self.html_path, "r", encoding="utf-8") as f:
            self.html = f.read()
        with open(self.css_path, "r", encoding="utf-8") as f:
            self.css = f.read()
        with open(self.js_path, "r", encoding="utf-8") as f:
            self.javascript = f.read()

    def test_light_mode_is_default_and_dark_section_removed(self):
        self.assertIn('<body class="light-mode">', self.html)
        self.assertNotIn("Modo Oscuro", self.html)
        self.assertNotIn("themeToggle", self.html)
        self.assertNotIn("theme-toggle", self.html)

    def test_light_mode_tokens_and_base_variables_exist(self):
        self.assertIn("--bg-primary: #f8fafc;", self.css)
        self.assertIn("--bg-card: #ffffff;", self.css)
        self.assertIn("--border: #e2e8f0;", self.css)
        self.assertIn("--text-primary: #1e293b;", self.css)
        self.assertIn("--text-muted: #64748b;", self.css)

    def test_core_application_surfaces_have_light_styling(self):
        for selector in (
            ".sidebar",
            ".metric-card",
            ".kuroda-table",
            ".chat-wrapper",
            ".tab-btn",
            ".seller-home-dashboard",
        ):
            self.assertIn(selector, self.css)

    def test_theme_toggle_is_disabled_in_js(self):
        self.assertIn('document.body.classList.add("light-mode")', self.javascript)

    def test_stylesheet_cache_version_was_bumped(self):
        self.assertIn("/static/style.css?v=", self.html)


if __name__ == "__main__":
    unittest.main()

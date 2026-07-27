import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DarkUixContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
        marker = "DARK UIX 2.0 — KURODA COMMAND CENTER"
        cls.dark_section = cls.css[cls.css.index(marker) :]

    def test_dark_redesign_is_scoped_away_from_light_mode(self):
        self.assertIn("body:not(.light-mode)", self.dark_section)
        self.assertNotIn("body.light-mode", self.dark_section)

    def test_dark_redesign_has_primitive_semantic_and_component_tokens(self):
        for token in (
            "--dark-ink-1000",
            "--surface-canvas-rgb",
            "--surface-card-rgb",
            "--stroke-default",
            "--shadow-card",
            "--focus-ring",
        ):
            self.assertIn(token, self.dark_section)

    def test_core_application_surfaces_are_covered(self):
        for selector in (
            ".auth-wrapper",
            ".sidebar-container",
            ".top-navbar",
            ".glass-card",
            ".data-table",
            ".kanban-column",
            ".modal-card",
            ".seller-home-dashboard",
            ".mobile-bottom-nav",
        ):
            self.assertIn(selector, self.dark_section)

    def test_dark_redesign_includes_accessibility_states(self):
        self.assertIn(":focus-visible", self.dark_section)
        self.assertIn("prefers-reduced-motion: reduce", self.dark_section)

    def test_stylesheet_cache_version_was_bumped(self):
        self.assertIn("/static/style.css?v=1.0.14", self.html)


if __name__ == "__main__":
    unittest.main()

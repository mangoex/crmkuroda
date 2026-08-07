from pathlib import Path
from unittest import TestCase


class SidebarScrollContractTest(TestCase):
    def test_desktop_sidebar_keeps_header_and_footer_while_menu_scrolls(self):
        root = Path(__file__).resolve().parents[1]
        css = (root / "static" / "style.css").read_text(encoding="utf-8")

        sidebar = css.split(".sidebar-container {", 1)[1].split("}", 1)[0]
        menu = css.split(".sidebar-menu {", 1)[1].split("}", 1)[0]
        footer = css.split(".sidebar-footer {", 1)[1].split("}", 1)[0]

        self.assertIn("height: 100vh", sidebar)
        self.assertIn("overflow: hidden", sidebar)
        self.assertIn("overflow-y: auto", menu)
        self.assertIn("min-height: 0", menu)
        self.assertIn("flex-shrink: 0", footer)

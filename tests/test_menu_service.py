import unittest

from app.services.menu_service import (
    calculate_menu_order,
    get_allowed_sections_for_role,
    normalize_role,
)


class MenuServiceTest(unittest.TestCase):
    def test_normalize_role(self):
        self.assertEqual(normalize_role("admin"), "admin")
        self.assertEqual(normalize_role("administrador"), "admin")
        self.assertEqual(normalize_role("GERENTE"), "gerente")
        self.assertEqual(normalize_role("vendedor"), "vendedor")
        self.assertEqual(normalize_role(None), "vendedor")

    def test_default_menu_order_vendedor(self):
        vendedor_sections = get_allowed_sections_for_role("vendedor")
        self.assertNotIn("vendedores", vendedor_sections)
        self.assertNotIn("asignacion", vendedor_sections)
        self.assertNotIn("api", vendedor_sections)
        self.assertEqual(vendedor_sections[0], "summary")
        self.assertEqual(vendedor_sections[1], "seguimiento")
        self.assertEqual(vendedor_sections[2], "cotizaciones")

    def test_default_menu_order_admin_and_gerente(self):
        admin_sections = get_allowed_sections_for_role("admin")
        gerente_sections = get_allowed_sections_for_role("gerente")
        self.assertIn("vendedores", admin_sections)
        self.assertIn("asignacion", admin_sections)
        self.assertIn("api", admin_sections)
        self.assertEqual(len(admin_sections), 12)
        self.assertEqual(len(gerente_sections), 12)
        self.assertEqual(admin_sections[0], "summary")
        self.assertEqual(admin_sections[1], "seguimiento")
        self.assertEqual(admin_sections[7], "vendedores")

    def test_fixed_menu_order_ignores_custom_reordering(self):
        custom = ["cotizaciones", "slight-edge", "summary", "promociones"]
        ordered = calculate_menu_order("vendedor", custom)
        allowed = get_allowed_sections_for_role("vendedor")
        self.assertEqual(ordered, allowed)

    def test_role_restriction_strips_forbidden_sections(self):
        custom = ["api", "vendedores", "cotizaciones", "asignacion", "summary"]
        ordered = calculate_menu_order("vendedor", custom)
        self.assertNotIn("api", ordered)
        self.assertNotIn("vendedores", ordered)
        self.assertNotIn("asignacion", ordered)
        self.assertEqual(ordered, get_allowed_sections_for_role("vendedor"))


if __name__ == "__main__":
    unittest.main()

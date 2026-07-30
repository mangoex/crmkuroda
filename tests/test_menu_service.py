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
        self.assertIn("summary", vendedor_sections)
        self.assertIn("cotizaciones", vendedor_sections)

    def test_default_menu_order_admin_and_gerente(self):
        admin_sections = get_allowed_sections_for_role("admin")
        gerente_sections = get_allowed_sections_for_role("gerente")
        self.assertIn("vendedores", admin_sections)
        self.assertIn("asignacion", admin_sections)
        self.assertIn("api", admin_sections)
        self.assertEqual(len(admin_sections), 12)
        self.assertEqual(len(gerente_sections), 12)

    def test_custom_reordering_vendedor(self):
        custom = ["cotizaciones", "slight-edge", "summary", "promociones"]
        ordered = calculate_menu_order("vendedor", custom)
        
        # Check that requested custom items come first in specified order
        self.assertEqual(ordered[0], "cotizaciones")
        self.assertEqual(ordered[1], "slight-edge")
        self.assertEqual(ordered[2], "summary")
        self.assertEqual(ordered[3], "promociones")

        # Check all allowed vendor items are present
        allowed = get_allowed_sections_for_role("vendedor")
        self.assertEqual(set(ordered), set(allowed))
        self.assertEqual(len(ordered), len(allowed))

    def test_role_restriction_strips_forbidden_sections(self):
        # A vendedor attempts to inject admin-only sections in custom order
        custom = ["api", "vendedores", "cotizaciones", "asignacion", "summary"]
        ordered = calculate_menu_order("vendedor", custom)

        self.assertNotIn("api", ordered)
        self.assertNotIn("vendedores", ordered)
        self.assertNotIn("asignacion", ordered)
        self.assertEqual(ordered[0], "cotizaciones")
        self.assertEqual(ordered[1], "summary")

    def test_missing_sections_appended(self):
        custom = ["seguimiento"]
        ordered = calculate_menu_order("vendedor", custom)
        
        self.assertEqual(ordered[0], "seguimiento")
        # Remaining allowed items appended
        self.assertEqual(len(ordered), len(get_allowed_sections_for_role("vendedor")))

    def test_duplicate_removal(self):
        custom = ["cotizaciones", "summary", "cotizaciones", "summary", "agentes"]
        ordered = calculate_menu_order("admin", custom)

        self.assertEqual(ordered[0], "cotizaciones")
        self.assertEqual(ordered[1], "summary")
        self.assertEqual(ordered[2], "agentes")
        self.assertEqual(len(ordered), 12)


if __name__ == "__main__":
    unittest.main()

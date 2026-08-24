"""TDD Test Suite for Extended Roles and RBAC Permissions (Punto 13)."""

import unittest
from fastapi import HTTPException
from app.core.security import RoleChecker
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioBase, UsuarioCreate


class TestRolesPermissions(unittest.TestCase):
    def test_new_roles_allowed_in_schema(self):
        """Los roles compras, logistica, marketing son válidos en la base de usuarios."""
        for role in ["compras", "logistica", "marketing", "admin", "gerente", "vendedor", "soporte"]:
            u = UsuarioBase(email=f"{role}@kuroda.com", rol=role)
            self.assertEqual(u.rol, role)

    def test_role_checker_allows_compras_for_inventory(self):
        """RoleChecker permite acceso a compras, gerente y admin para Inventario / Material D."""
        checker = RoleChecker(["admin", "gerente", "compras"])
        user_compras = Usuario(email="compras@kuroda.com", rol="compras")
        user_vendedor = Usuario(email="asesor@kuroda.com", rol="vendedor")

        # Compras debe pasar sin lanzar excepción
        self.assertEqual(checker(user_compras), user_compras)

        # Vendedor debe ser denegado con 403
        with self.assertRaises(HTTPException) as ctx:
            checker(user_vendedor)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_role_checker_allows_logistica_for_deliveries(self):
        """RoleChecker permite acceso a logistica, vendedor, gerente y admin para Sobrepedidos / Por Entregar."""
        checker = RoleChecker(["admin", "gerente", "logistica", "vendedor"])
        user_logistica = Usuario(email="logistica@kuroda.com", rol="logistica")
        user_soporte = Usuario(email="soporte@kuroda.com", rol="soporte")

        self.assertEqual(checker(user_logistica), user_logistica)

        with self.assertRaises(HTTPException) as ctx:
            checker(user_soporte)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_role_checker_allows_marketing_for_promotions(self):
        """RoleChecker permite acceso a marketing, gerente y admin para Promociones."""
        checker = RoleChecker(["admin", "gerente", "marketing"])
        user_mkt = Usuario(email="marketing@kuroda.com", rol="marketing")
        user_vendedor = Usuario(email="asesor@kuroda.com", rol="vendedor")

        self.assertEqual(checker(user_mkt), user_mkt)

        with self.assertRaises(HTTPException) as ctx:
            checker(user_vendedor)
        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()

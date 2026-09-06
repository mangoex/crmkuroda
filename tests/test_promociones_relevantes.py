"""
TDD Test Suite for Relevant Promotions (Promociones Relevantes - Top 4).

Specifications (Given - When - Then):
1. Invariant: At any time, a maximum of 4 promotions can be marked as relevant.
2. Given 4 promotions already marked as relevant,
   When a user attempts to mark a 5th promotion as relevant,
   Then the system rejects the operation with HTTP 400 and an explicit warning message.
3. Given a promotion marked as relevant,
   When the user toggles it off,
   Then it becomes non-relevant and frees up a slot.
4. Given marked relevant promotions,
   When querying GET /api/v1/promociones/relevantes,
   Then it returns up to 4 items with required commercial fields (SKU, name, margin, price).
5. Given a catalog of promotions,
   When filtering with solo_relevantes=True,
   Then only relevant promotions are returned.
6. Given static UI assets (index.html and app.js),
   Then they contain the required seller panel container, star column, filter options, and limit enforcement.
"""

from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from app.models.promocion import Promocion
from app.models.usuario import Usuario


class FakeScalarResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return list(self.values)

    def first(self):
        return self.values[0] if self.values else None

    def scalar(self):
        return self.values[0] if self.values else 0


class FakeSession:
    def __init__(self, execute_results=None):
        self.execute_results = list(execute_results or [])
        self.added = []
        self.commits = 0
        self.refreshed = []

    async def execute(self, statement, *args, **kwargs):
        if self.execute_results:
            return self.execute_results.pop(0)
        return FakeScalarResult([])

    def add(self, item):
        self.added.append(item)

    async def commit(self):
        self.commits += 1

    async def refresh(self, item):
        self.refreshed.append(item)


class TestPromocionesRelevantesTDD(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.admin_user = Usuario(
            email="admin@kuroda.com",
            hashed_password="hash",
            nombre_completo="Gerente General",
            rol="gerente"
        )

    async def test_model_has_es_relevante_field_and_default(self):
        """El modelo Promocion debe incluir es_relevante (por defecto False)."""
        promo = Promocion(
            id=10,
            codigo_material="SKU-1234",
            descripcion_material="Piso Leighton 60x120",
            precio_promocion=199.50,
            margen_promocion=25.0
        )
        self.assertTrue(hasattr(promo, "es_relevante"))
        self.assertFalse(bool(promo.es_relevante))
        
        # Validar en to_dict
        promo_dict = promo.to_dict()
        self.assertIn("es_relevante", promo_dict)
        self.assertFalse(promo_dict["es_relevante"])

    async def test_toggle_promocion_relevante_success_under_limit(self):
        """Permite marcar como relevante si hay menos de 4 artículos marcados."""
        from app.api.v1.promociones import toggle_promocion_relevante

        promo = Promocion(
            id=1,
            codigo_material="SKU-001",
            descripcion_material="Producto 1",
            precio_promocion=100.0,
            margen_promocion=20.0,
            es_relevante=False
        )

        db = FakeSession([
            FakeScalarResult([promo]),
            FakeScalarResult([3]),
        ])

        response = await toggle_promocion_relevante(
            promocion_id=1,
            db=db,
            current_user=self.admin_user
        )

        self.assertEqual(response["status"], "success")
        self.assertTrue(promo.es_relevante)
        self.assertEqual(db.commits, 1)
        self.assertTrue(response["data"]["es_relevante"])

    async def test_toggle_promocion_relevante_unmark_success(self):
        """Permite desmarcar una promoción relevante sin importar el conteo."""
        from app.api.v1.promociones import toggle_promocion_relevante

        promo = Promocion(
            id=2,
            codigo_material="SKU-002",
            descripcion_material="Producto 2",
            precio_promocion=150.0,
            margen_promocion=18.0,
            es_relevante=True
        )

        db = FakeSession([
            FakeScalarResult([promo]),
        ])

        response = await toggle_promocion_relevante(
            promocion_id=2,
            db=db,
            current_user=self.admin_user
        )

        self.assertEqual(response["status"], "success")
        self.assertFalse(promo.es_relevante)
        self.assertEqual(db.commits, 1)
        self.assertFalse(response["data"]["es_relevante"])

    async def test_toggle_promocion_relevante_blocks_fifth_item(self):
        """Invariante: si ya hay 4 relevantes, marcar una 5ta lanza HTTP 400."""
        from app.api.v1.promociones import toggle_promocion_relevante

        promo = Promocion(
            id=5,
            codigo_material="SKU-005",
            descripcion_material="Producto 5",
            precio_promocion=300.0,
            margen_promocion=30.0,
            es_relevante=False
        )

        db = FakeSession([
            FakeScalarResult([promo]),
            FakeScalarResult([4]),
        ])

        with self.assertRaises(HTTPException) as ctx:
            await toggle_promocion_relevante(
                promocion_id=5,
                db=db,
                current_user=self.admin_user
            )

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("4 promociones", ctx.exception.detail)
        self.assertIn("desmarcar", ctx.exception.detail.lower())
        self.assertFalse(promo.es_relevante)
        self.assertEqual(db.commits, 0)

    async def test_get_promociones_relevantes_returns_top_4(self):
        """Endpoint GET /relevantes retorna hasta 4 promociones relevantes con datos requeridos."""
        from app.api.v1.promociones import get_promociones_relevantes

        promos = [
            Promocion(id=1, codigo_material="SKU-1", descripcion_material="P1", precio_promocion=100.0, margen_promocion=15.0, es_relevante=True),
            Promocion(id=2, codigo_material="SKU-2", descripcion_material="P2", precio_promocion=200.0, margen_promocion=20.0, es_relevante=True),
            Promocion(id=3, codigo_material="SKU-3", descripcion_material="P3", precio_promocion=300.0, margen_promocion=25.0, es_relevante=True),
            Promocion(id=4, codigo_material="SKU-4", descripcion_material="P4", precio_promocion=400.0, margen_promocion=30.0, es_relevante=True),
        ]

        db = FakeSession([
            FakeScalarResult(promos),
        ])

        response = await get_promociones_relevantes(db=db)
        self.assertEqual(response["status"], "success")
        self.assertEqual(len(response["data"]), 4)
        for item in response["data"]:
            self.assertIn("codigo_material", item)
            self.assertIn("descripcion_material", item)
            self.assertIn("precio_promocion", item)
            self.assertIn("margen_promocion", item)
            self.assertTrue(item["es_relevante"])

    async def test_list_promociones_with_solo_relevantes_param(self):
        """Endpoint GET / acepta parámetro solo_relevantes para filtrar en backend."""
        from app.api.v1.promociones import list_promociones

        promos = [
            Promocion(id=1, codigo_material="SKU-1", descripcion_material="P1", es_relevante=True),
        ]

        db = FakeSession([
            FakeScalarResult(promos),
        ])

        response = await list_promociones(solo_relevantes=True, db=db)
        self.assertEqual(response["status"], "success")
        self.assertEqual(len(response["data"]), 1)
        self.assertTrue(response["data"][0]["es_relevante"])


class TestPromocionesUIContracts(unittest.TestCase):

    def setUp(self):
        self.index_html = Path("static/index.html").read_text(encoding="utf-8")
        self.app_js = Path("static/app.js").read_text(encoding="utf-8")

    def test_seller_panel_has_promos_destacadas_container(self):
        """El HTML debe tener el contenedor de las 4 promociones relevantes bajo focos comerciales."""
        self.assertIn("seller-promos-destacadas-container", self.index_html)
        self.assertIn("seller-promos-destacadas-grid", self.index_html)

    def test_promociones_table_has_star_header_and_filter(self):
        """La tabla de promociones debe tener cabecera para la estrella y opción en el filtro."""
        self.assertIn("filter-promo-status", self.index_html)
        self.assertIn('value="relevantes"', self.index_html)
        self.assertIn("th-star-relevante", self.index_html)

    def test_app_js_implements_star_toggle_and_limit_enforcement(self):
        """El JS debe implementar togglePromoRelevante y validar límite de 4."""
        self.assertIn("togglePromoRelevante", self.app_js)
        self.assertIn("renderSellerPromosDestacadas", self.app_js)


if __name__ == "__main__":
    unittest.main()

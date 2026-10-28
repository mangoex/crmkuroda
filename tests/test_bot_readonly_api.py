"""Suite de pruebas automatizadas para el módulo de solo lectura /api/v1/bot."""

from __future__ import annotations

import asyncio
from decimal import Decimal
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.bot import _mazatlan_today, reset_bot_rate_limiter
from app.core.database import Base, get_bot_db
from app.main import app
from app.models.usuario import Usuario
from seed_bot_data import SELLER_SPECS, seed_bot_test_data

TEST_BOT_KEY = "kuroda_bot_test_key_" + ("x" * 32)  # > 40 caracteres


class BotReadonlyApiTest(unittest.IsolatedAsyncioTestCase):
    _shared_engine = None
    _shared_session_factory = None
    _shared_seed_summary = None
    _shared_today = None

    async def asyncSetUp(self) -> None:
        reset_bot_rate_limiter()
        self.prev_bot_key = os.environ.get("BOT_API_KEY")
        self.prev_rate_limit = os.environ.get("BOT_RATE_LIMIT_PER_MINUTE")
        os.environ["BOT_API_KEY"] = TEST_BOT_KEY
        os.environ["BOT_RATE_LIMIT_PER_MINUTE"] = "60"

        if BotReadonlyApiTest._shared_engine is None:
            engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            session_factory = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            today = _mazatlan_today()
            async with session_factory() as session:
                seed_summary = await seed_bot_test_data(session, reference_date=today)

            BotReadonlyApiTest._shared_engine = engine
            BotReadonlyApiTest._shared_session_factory = session_factory
            BotReadonlyApiTest._shared_seed_summary = seed_summary
            BotReadonlyApiTest._shared_today = today

        self.TestSessionLocal = BotReadonlyApiTest._shared_session_factory
        self.seed_summary = BotReadonlyApiTest._shared_seed_summary
        self.today = BotReadonlyApiTest._shared_today

        async def _override_get_bot_db():
            async with self.TestSessionLocal() as session:
                session.info["readonly_bot"] = True
                try:
                    yield session
                finally:
                    await session.rollback()
                    await session.close()

        app.dependency_overrides[get_bot_db] = _override_get_bot_db
        self.client = TestClient(app, raise_server_exceptions=False)
        self.headers = {"X-API-Key": TEST_BOT_KEY}

    async def asyncTearDown(self) -> None:
        app.dependency_overrides.pop(get_bot_db, None)
        reset_bot_rate_limiter()
        if self.prev_bot_key is None:
            os.environ.pop("BOT_API_KEY", None)
        else:
            os.environ["BOT_API_KEY"] = self.prev_bot_key

        if self.prev_rate_limit is None:
            os.environ.pop("BOT_RATE_LIMIT_PER_MINUTE", None)
        else:
            os.environ["BOT_RATE_LIMIT_PER_MINUTE"] = self.prev_rate_limit

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._shared_engine is not None:
            asyncio.run(cls._shared_engine.dispose())
            cls._shared_engine = None

    def test_seed_counts_meet_requirements(self) -> None:
        """Verifica que la siembra creó al menos 3 vendedores, 20 ventas y 10 cotizaciones."""
        self.assertGreaterEqual(self.seed_summary["vendedores"], 3)
        self.assertGreaterEqual(self.seed_summary["ventas"], 20)
        self.assertGreaterEqual(self.seed_summary["cotizaciones_adicionales"], 10)
        self.assertGreaterEqual(self.seed_summary["metas_mes"], 3)

    def test_401_without_key_or_invalid_key_uses_compare_digest(self) -> None:
        """1) Sin clave o con clave inválida devuelve 401 con formato {'detail': '...'}."""
        r_no_key = self.client.get("/api/v1/bot/health")
        self.assertEqual(r_no_key.status_code, 401)
        self.assertIn("detail", r_no_key.json())

        with patch("app.api.v1.bot.secrets.compare_digest", wraps=__import__("secrets").compare_digest) as mock_cd:
            r_bad_key = self.client.get(
                "/api/v1/bot/vendedores",
                headers={"X-API-Key": "clave_invalida_de_prueba"},
            )
            self.assertEqual(r_bad_key.status_code, 401)
            self.assertIn("detail", r_bad_key.json())
            self.assertTrue(mock_cd.called)

    def test_405_on_post_put_delete_patch(self) -> None:
        """1) Solo métodos GET en este módulo; POST/PUT/DELETE/PATCH devuelven 405 con {'detail': '...'}."""
        endpoints = [
            "/api/v1/bot/health",
            "/api/v1/bot/vendedores",
            "/api/v1/bot/ventas",
            "/api/v1/bot/metas",
            "/api/v1/bot/avance",
            "/api/v1/bot/cotizaciones",
            "/api/v1/bot/clientes",
            "/api/v1/bot/citas",
            "/api/v1/bot/compromisos",
        ]
        for ep in endpoints:
            for method in ("POST", "PUT", "DELETE", "PATCH"):
                resp = self.client.request(method, ep, headers=self.headers)
                self.assertEqual(resp.status_code, 405, f"{method} {ep} debería devolver 405")
                self.assertIn("detail", resp.json())
                self.assertEqual(resp.headers.get("allow"), "GET")

    def test_rate_limit_enforced_per_key(self) -> None:
        """Verifica límite de peticiones por minuto por clave."""
        os.environ["BOT_RATE_LIMIT_PER_MINUTE"] = "3"
        reset_bot_rate_limiter()
        for _ in range(3):
            ok_resp = self.client.get("/api/v1/bot/health", headers=self.headers)
            self.assertEqual(ok_resp.status_code, 200)
        limited_resp = self.client.get("/api/v1/bot/health", headers=self.headers)
        self.assertEqual(limited_resp.status_code, 429)
        self.assertIn("detail", limited_resp.json())

    def test_health_endpoint_timezone_and_format(self) -> None:
        """Verifica GET /api/v1/bot/health con zona horaria America/Mazatlan."""
        resp = self.client.get("/api/v1/bot/health", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("version", data)
        self.assertTrue(
            data["hora_servidor"].endswith("-07:00") or data["hora_servidor"].endswith("-06:00"),
            f"Hora servidor sin offset America/Mazatlan: {data['hora_servidor']}",
        )

    def test_vendedores_list_filters_and_detail(self) -> None:
        """Verifica GET /api/v1/bot/vendedores y GET /api/v1/bot/vendedores/{id}."""
        resp = self.client.get("/api/v1/bot/vendedores?activo=true&limit=10&offset=0", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["total"], 3)
        self.assertEqual(payload["limit"], 10)
        self.assertEqual(payload["offset"], 0)
        self.assertEqual(len(payload["items"]), 3)

        first = payload["items"][0]
        for field in ("id", "nombre", "email", "telefono", "equipo", "activo", "fecha_alta"):
            self.assertIn(field, first)
        self.assertTrue(first["fecha_alta"].endswith("-07:00") or first["fecha_alta"].endswith("-06:00"))

        lorena_id = str(SELLER_SPECS[0]["id"])
        det_resp = self.client.get(f"/api/v1/bot/vendedores/{lorena_id}", headers=self.headers)
        self.assertEqual(det_resp.status_code, 200)
        det = det_resp.json()
        self.assertEqual(det["id"], lorena_id)
        self.assertEqual(det["ventas_total"], 40000.0)
        self.assertEqual(det["num_ventas"], 8)
        self.assertGreaterEqual(det["num_cotizaciones"], 11)
        self.assertEqual(det["meta_mes"], 100000.0)
        self.assertEqual(det["avance_pct"], 40.0)
        self.assertEqual(det["moneda"], "MXN")

        not_found = self.client.get(f"/api/v1/bot/vendedores/{uuid4()}", headers=self.headers)
        self.assertEqual(not_found.status_code, 404)
        self.assertIn("detail", not_found.json())

    def test_ventas_pagination_filters_and_detail_partidas(self) -> None:
        """Verifica GET /api/v1/bot/ventas y GET /api/v1/bot/ventas/{id} con partidas."""
        resp = self.client.get("/api/v1/bot/ventas?limit=5&offset=0", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total"], 20)
        self.assertEqual(data["limit"], 5)
        self.assertEqual(data["offset"], 0)
        self.assertEqual(len(data["items"]), 5)

        sale = data["items"][0]
        expected_fields = (
            "id",
            "folio",
            "fecha",
            "vendedor_id",
            "vendedor_nombre",
            "cliente_id",
            "cliente_nombre",
            "monto",
            "moneda",
            "estatus",
            "forma_pago",
            "cotizacion_id",
        )
        for f in expected_fields:
            self.assertIn(f, sale)
        self.assertEqual(sale["moneda"], "MXN")

        mario_id = str(SELLER_SPECS[1]["id"])
        mario_sales = self.client.get(
            f"/api/v1/bot/ventas?vendedor_id={mario_id}", headers=self.headers
        ).json()
        self.assertEqual(mario_sales["total"], 7)

        det_resp = self.client.get(f"/api/v1/bot/ventas/{sale['id']}", headers=self.headers)
        self.assertEqual(det_resp.status_code, 200)
        det = det_resp.json()
        self.assertIn("partidas", det)
        self.assertGreaterEqual(len(det["partidas"]), 1)
        partida = det["partidas"][0]
        for pf in ("producto", "cantidad", "precio_unitario", "importe"):
            self.assertIn(pf, partida)

        bad_limit = self.client.get("/api/v1/bot/ventas?limit=501", headers=self.headers)
        self.assertEqual(bad_limit.status_code, 422)
        self.assertIn("detail", bad_limit.json())

        bad_dates = self.client.get(
            "/api/v1/bot/ventas?desde=2026-10-20&hasta=2026-10-01", headers=self.headers
        )
        self.assertEqual(bad_dates.status_code, 400)
        self.assertIn("detail", bad_dates.json())

    def test_avance_matches_manual_sum_exactly(self) -> None:
        """5) Verifica que avance_pct y montos en /api/v1/bot/avance coincidan exactamente con una suma manual."""
        periodo_actual = self.today.strftime("%Y-%m")
        resp = self.client.get(f"/api/v1/bot/avance?periodo={periodo_actual}", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        avance_data = resp.json()

        ventas_resp = self.client.get(
            f"/api/v1/bot/ventas?desde={self.today.replace(day=1).isoformat()}&hasta={self.today.isoformat()}&limit=500",
            headers=self.headers,
        ).json()
        metas_resp = self.client.get(
            f"/api/v1/bot/metas?periodo={periodo_actual}&tipo=mensual&limit=500",
            headers=self.headers,
        ).json()

        manual_sales_by_seller: dict[str, Decimal] = {}
        manual_count_by_seller: dict[str, int] = {}
        for v in ventas_resp["items"]:
            sid = v["vendedor_id"]
            manual_sales_by_seller[sid] = manual_sales_by_seller.get(sid, Decimal("0")) + Decimal(str(v["monto"]))
            manual_count_by_seller[sid] = manual_count_by_seller.get(sid, 0) + 1

        manual_meta_by_seller: dict[str, Decimal] = {}
        for m in metas_resp["items"]:
            sid = m["vendedor_id"]
            manual_meta_by_seller[sid] = manual_meta_by_seller.get(sid, Decimal("0")) + Decimal(str(m["meta_monto"]))

        for item in avance_data["items"]:
            sid = item["vendedor_id"]
            expected_vendido = float(manual_sales_by_seller.get(sid, Decimal("0")))
            expected_meta = float(manual_meta_by_seller.get(sid, Decimal("0")))
            expected_pct = round((expected_vendido / expected_meta) * 100.0, 2) if expected_meta > 0 else 0.0
            expected_faltante = max(0.0, round(expected_meta - expected_vendido, 2))
            expected_num_ventas = manual_count_by_seller.get(sid, 0)

            self.assertAlmostEqual(item["vendido_monto"], expected_vendido, places=2)
            self.assertAlmostEqual(item["meta_monto"], expected_meta, places=2)
            self.assertAlmostEqual(item["avance_pct"], expected_pct, places=2)
            self.assertAlmostEqual(item["faltante"], expected_faltante, places=2)
            self.assertEqual(item["num_ventas"], expected_num_ventas)
            self.assertEqual(item["moneda"], "MXN")

        total_manual_meta = float(sum(manual_meta_by_seller.values(), Decimal("0")))
        total_manual_vendido = float(sum(manual_sales_by_seller.values(), Decimal("0")))
        total_manual_pct = round((total_manual_vendido / total_manual_meta) * 100.0, 2)
        total_manual_faltante = round(total_manual_meta - total_manual_vendido, 2)
        total_manual_ventas = sum(manual_count_by_seller.values())

        equipo = avance_data["equipo"]
        self.assertAlmostEqual(equipo["meta_monto"], total_manual_meta, places=2)
        self.assertAlmostEqual(equipo["vendido_monto"], total_manual_vendido, places=2)
        self.assertAlmostEqual(equipo["avance_pct"], total_manual_pct, places=2)
        self.assertAlmostEqual(equipo["faltante"], total_manual_faltante, places=2)
        self.assertEqual(equipo["num_ventas"], total_manual_ventas)
        self.assertEqual(equipo["moneda"], "MXN")

    def test_cotizaciones_statuses_and_detail_with_notas(self) -> None:
        """Verifica GET /api/v1/bot/cotizaciones por estatus y GET /api/v1/bot/cotizaciones/{id}."""
        all_resp = self.client.get("/api/v1/bot/cotizaciones?limit=100", headers=self.headers)
        self.assertEqual(all_resp.status_code, 200)
        all_data = all_resp.json()
        self.assertEqual(all_data["total"], 30)

        expected_by_status = {
            "aceptada": 20,
            "enviada": 6,
            "borrador": 1,
            "rechazada": 2,
            "vencida": 1,
        }
        for est, expected_count in expected_by_status.items():
            r_est = self.client.get(
                f"/api/v1/bot/cotizaciones?estatus={est}", headers=self.headers
            )
            self.assertEqual(r_est.status_code, 200)
            payload = r_est.json()
            self.assertEqual(payload["total"], expected_count, f"Estatus {est} esperado={expected_count}")
            for q_item in payload["items"]:
                self.assertEqual(q_item["estatus"], est)

        enviada_item = self.client.get(
            "/api/v1/bot/cotizaciones?estatus=enviada&limit=1", headers=self.headers
        ).json()["items"][0]
        det_resp = self.client.get(
            f"/api/v1/bot/cotizaciones/{enviada_item['id']}", headers=self.headers
        )
        self.assertEqual(det_resp.status_code, 200)
        det = det_resp.json()
        self.assertIn("partidas", det)
        self.assertIn("notas", det)
        self.assertGreaterEqual(len(det["partidas"]), 1)
        self.assertGreaterEqual(len(det["notas"]), 1)

    def test_clientes_citas_and_compromisos_endpoints(self) -> None:
        """Verifica GET /api/v1/bot/clientes, /citas y /compromisos."""
        cli_resp = self.client.get("/api/v1/bot/clientes?q=Constructora", headers=self.headers)
        self.assertEqual(cli_resp.status_code, 200)
        cli_data = cli_resp.json()
        self.assertGreaterEqual(cli_data["total"], 1)
        for field in ("id", "nombre", "empresa", "telefono", "email", "vendedor_id", "fecha_alta"):
            self.assertIn(field, cli_data["items"][0])

        citas_resp = self.client.get("/api/v1/bot/citas", headers=self.headers)
        self.assertEqual(citas_resp.status_code, 200)
        self.assertEqual(citas_resp.json()["total"], 3)

        for comp_est in ("pendiente", "cumplido", "vencido"):
            comp_resp = self.client.get(
                f"/api/v1/bot/compromisos?estatus={comp_est}", headers=self.headers
            )
            self.assertEqual(comp_resp.status_code, 200)
            self.assertEqual(comp_resp.json()["total"], 1)

    async def test_readonly_session_blocks_any_writes(self) -> None:
        """4) Verifica que la sesión de solo lectura impide cualquier INSERT/UPDATE/DELETE."""
        async with self.TestSessionLocal() as session:
            session.info["readonly_bot"] = True
            session.add(
                Usuario(
                    email="intruso@kuroda.com",
                    hashed_password="x",
                    rol="vendedor",
                )
            )
            with self.assertRaises(PermissionError):
                await session.flush()

    def test_openapi_schema_documents_all_bot_endpoints(self) -> None:
        """2 & 5) Verifica que /openapi.json incluya todos los endpoints /api/v1/bot documentados."""
        resp = self.client.get("/openapi.json")
        self.assertEqual(resp.status_code, 200)
        schema = resp.json()
        paths = schema.get("paths", {})
        expected_paths = [
            "/api/v1/bot/health",
            "/api/v1/bot/vendedores",
            "/api/v1/bot/vendedores/{vendedor_id}",
            "/api/v1/bot/ventas",
            "/api/v1/bot/ventas/{venta_id}",
            "/api/v1/bot/metas",
            "/api/v1/bot/avance",
            "/api/v1/bot/cotizaciones",
            "/api/v1/bot/cotizaciones/{cotizacion_id}",
            "/api/v1/bot/clientes",
            "/api/v1/bot/citas",
            "/api/v1/bot/compromisos",
        ]
        for ep in expected_paths:
            self.assertIn(ep, paths, f"Falta documentar {ep} en /openapi.json")
            self.assertIn("get", paths[ep])
            self.assertEqual(list(paths[ep].keys()), ["get"])


if __name__ == "__main__":
    unittest.main()

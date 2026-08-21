"""Unit tests for Agent Resilience, Deterministic Calculations, and LLM Mocking."""

import json
import unittest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
from fastapi import HTTPException

from app.agents.cotizaciones_agent import generate_proposal
from app.agents.metas_agent import generate_seller_goals
from app.agents.seguimiento_agent import (
    generate_followup_message,
    generate_whatsapp_link,
    send_whatsapp_message,
    send_whatsapp_message_direct,
    process_incoming_whatsapp_message,
)
from app.agents.slight_edge_agent import categorize_activity, run_coaching_chat
from app.agents.llm import call_llm


class TestCotizacionesAgent(unittest.IsolatedAsyncioTestCase):
    async def test_proposal_calculates_exact_math_before_llm(self):
        items = [
            {"producto": "Tubería PVC 2 pulg", "cantidad": 10, "precio_unitario": 150.50},
            {"producto": "Válvula Esfera", "cantidad": 2, "precio_unitario": 350.00},
        ]
        # 10 * 150.50 = 1505.00
        # 2 * 350.00 = 700.00
        # Total = 2205.00

        with patch("app.agents.cotizaciones_agent.call_gemini", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Estimado cliente, adjuntamos su cotización formal por $2,205.00 MXN."

            result = await generate_proposal("Empresa Constructora del Norte", items, "Entrega urgente")

            self.assertEqual(result["total"], Decimal("2205.00"))
            self.assertEqual(len(result["items_procesados"]), 2)
            self.assertEqual(result["items_procesados"][0]["subtotal"], 1505.0)
            self.assertEqual(result["items_procesados"][1]["subtotal"], 700.0)
            self.assertIn("2,205.00", result["texto_propuesta"])
            mock_llm.assert_awaited_once()


class TestMetasAgent(unittest.IsolatedAsyncioTestCase):
    async def test_generate_seller_goals_parses_json_schema(self):
        expected_output = {
            "monto_objetivo": 250000.0,
            "descripcion": "Enfoque en colocación de tubería sanitaria y válvulas en promoción.",
            "kpis_clave": ["5 cierres semanales", "Aumentar 10% ventas en promoción"],
        }

        with patch("app.agents.metas_agent.call_gemini", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = json.dumps(expected_output)

            history = [{"cliente_nombre": "Cliente A", "total": "50000", "texto_propuesta": "Cotizacion 1"}]
            promos = [{"codigo_material": "TUB01", "descripcion_material": "Tubo", "precio_promocion": 100, "moneda": "MXN"}]

            res = await generate_seller_goals("vendedor@kuroda.com", history, "Objetivo global 1M", promos)

            self.assertEqual(res["monto_objetivo"], 250000.0)
            self.assertEqual(len(res["kpis_clave"]), 2)

    async def test_generate_seller_goals_fallback_on_json_error(self):
        with patch("app.agents.metas_agent.call_gemini", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Texto no parseable en JSON"

            res = await generate_seller_goals("vendedor@kuroda.com", [], "Global")
            self.assertEqual(res["monto_objetivo"], 100000.0)
            self.assertIn("error de procesamiento", res["descripcion"])


class TestSeguimientoAgent(unittest.IsolatedAsyncioTestCase):
    def test_generate_whatsapp_link_encodes_clean_url(self):
        link = generate_whatsapp_link("+52 (667) 123-4567", "Hola Juan, ¡éxito hoy!")
        self.assertTrue(link.startswith("https://wa.me/526671234567?text="))
        self.assertIn("Hola%20Juan", link)

    async def test_send_whatsapp_message_direct_no_credentials_returns_false(self):
        with patch("app.agents.seguimiento_agent.settings") as mock_settings:
            mock_settings.META_WHATSAPP_TOKEN = ""
            mock_settings.META_PHONE_NUMBER_ID = ""
            sent = await send_whatsapp_message_direct("6671234567", "Hola")
            self.assertFalse(sent)

    async def test_send_whatsapp_message_direct_success(self):
        with patch("app.agents.seguimiento_agent.settings") as mock_settings:
            mock_settings.META_WHATSAPP_TOKEN = "test_meta_token"
            mock_settings.META_PHONE_NUMBER_ID = "123456789"

            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"messages": [{"id": "wamid.123"}]}
                mock_post.return_value = mock_resp

                sent = await send_whatsapp_message_direct("6671234567", "Mensaje de prueba")
                self.assertTrue(sent)

    async def test_process_incoming_whatsapp_message(self):
        with patch("app.agents.seguimiento_agent.call_gemini", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "¡Excelente avance! Sigue así para llegar a tu meta."
            reply = await process_incoming_whatsapp_message("Carlos", "Hoy cerré 3 cotizaciones.")
            self.assertEqual(reply, "¡Excelente avance! Sigue así para llegar a tu meta.")


class TestSlightEdgeAgent(unittest.IsolatedAsyncioTestCase):
    def test_categorize_activity(self):
        self.assertEqual(categorize_activity("Hacer 5 llamadas en frío"), "llamada")
        self.assertEqual(categorize_activity("Reunión con directores"), "cita")
        self.assertEqual(categorize_activity("Enviar cotización"), "cotizacion")
        self.assertEqual(categorize_activity("Cierre de venta y cobro"), "venta")
        self.assertEqual(categorize_activity("Lectura 10 páginas"), "otra")

    async def test_run_coaching_chat_with_tool_call(self):
        mock_msg = {
            "content": "Hemos configurado tu plan de La Ventaja.",
            "tool_calls": [
                {
                    "function": {
                        "name": "save_slight_edge_plan",
                        "arguments": json.dumps({
                            "monthly_income_goal": 50000,
                            "ticket_average": 5000,
                            "conversion_rate": 20,
                            "activities_config": [{"activity": "Llamadas", "points": 2}],
                            "daily_points_goal": 10
                        })
                    }
                }
            ]
        }

        with patch("app.agents.slight_edge_agent.call_llm_chat", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_msg
            history = [{"role": "user", "content": "Quiero ganar 50 mil"}]

            res = await run_coaching_chat(history)
            self.assertIn("Hemos configurado tu plan", res["response"])
            self.assertIsNotNone(res["tool_call"])
            self.assertEqual(res["tool_call"]["monthly_income_goal"], 50000)


class TestLLMServiceResilience(unittest.IsolatedAsyncioTestCase):
    async def test_call_llm_without_keys_raises_http_500(self):
        with patch("app.agents.llm.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "openrouter"
            mock_settings.OPENROUTER_API_KEY = ""
            mock_settings.GEMINI_API_KEY = ""

            with self.assertRaises(HTTPException) as ctx:
                await call_llm("Hola")
            self.assertEqual(ctx.exception.status_code, 500)


if __name__ == "__main__":
    unittest.main()
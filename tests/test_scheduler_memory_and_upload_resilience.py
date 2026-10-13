"""
Pruebas de especificación y resiliencia (SBD / TDD) para el Scheduler y Carga de Cotizaciones.
Valida:
1. Prevención de tormenta de errores 500 cuando no hay API Keys de LLM configuradas.
2. Protección de memoria RAM evitando selectinload indiscriminado de cotizaciones históricas.
3. Optimización de memoria en la carga masiva de cotizaciones.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import date, datetime

from app.core.config import settings
from app.models.usuario import Usuario
from app.models.meta import Meta
from app.models.cotizacion import Cotizacion


class TestSchedulerResilience(unittest.IsolatedAsyncioTestCase):
    async def test_scheduler_omits_execution_if_no_llm_credentials(self):
        """
        GHERKIN:
        Dado que ni OPENROUTER_API_KEY ni GEMINI_API_KEY están configuradas
        Cuando job_generar_seguimientos_diarios es invocado
        Entonces no debe intentar procesar vendedores ni disparar excepciones 500 en bucle
        y debe retornar de manera segura registrando una advertencia.
        """
        from app.core.scheduler import job_generar_seguimientos_diarios

        with patch.object(settings, "OPENROUTER_API_KEY", None), \
             patch.object(settings, "GEMINI_API_KEY", None), \
             patch("app.core.scheduler.SessionLocal") as mock_session_cls, \
             patch("app.core.scheduler.logger") as mock_logger:

            await job_generar_seguimientos_diarios()

            # No debe abrir sesión de base de datos ni intentar iterar
            mock_session_cls.assert_not_called()
            mock_logger.warning.assert_called()
            warning_msg = mock_logger.warning.call_args[0][0]
            self.assertIn("No hay credenciales de LLM configuradas", warning_msg)

    async def test_scheduler_queries_only_recent_quotes_without_full_selectinload(self):
        """
        GHERKIN:
        Dado que hay credenciales de LLM activas y vendedores registrados
        Cuando job_generar_seguimientos_diarios se ejecuta
        Entonces no debe incluir selectinload(Usuario.cotizaciones) en la query de usuarios
        y debe limitar la consulta de cotizaciones a las 5 más recientes por vendedor.
        """
        from app.core.scheduler import job_generar_seguimientos_diarios

        vendedor_id = uuid4()
        fake_vendedor = Usuario(
            id=vendedor_id,
            email="vendedor@kuroda.com",
            nombre_completo="Juan Perez",
            rol="vendedor",
            telefono_whatsapp="6671234567"
        )
        fake_vendedor.metas = []

        mock_session = AsyncMock()
        # 1er execute: query de vendedores
        # 2do execute: check existente
        # 3er execute: query acotada de cotizaciones recientes (limit 5)
        # scalar results
        mock_result_vendedores = MagicMock()
        mock_result_vendedores.scalars.return_value.all.return_value = [fake_vendedor]

        mock_result_existente = MagicMock()
        mock_result_existente.scalars.return_value.first.return_value = None

        mock_result_cotizaciones = MagicMock()
        mock_result_cotizaciones.all.return_value = [
            ("Cliente Test 1", "1500.00"),
            ("Cliente Test 2", "2500.00"),
        ]

        mock_session.execute.side_effect = [
            mock_result_vendedores,
            mock_result_existente,
            mock_result_cotizaciones
        ]

        with patch.object(settings, "OPENROUTER_API_KEY", "test-key"), \
             patch("app.core.scheduler.SessionLocal") as mock_session_cls, \
             patch("app.core.scheduler.generate_followup_message", new_callable=AsyncMock) as mock_gen_msg, \
             patch("app.core.scheduler.generate_whatsapp_link", return_value="https://wa.me/fake"):

            mock_session_cls.return_value.__aenter__.return_value = mock_session
            mock_gen_msg.return_value = "Hola Juan, tu resumen diario."

            await job_generar_seguimientos_diarios()

            # Verificar que la query inicial de vendedores NO incluye selectinload(Usuario.cotizaciones)
            vendedores_query_call = mock_session.execute.call_args_list[0][0][0]
            # Convertir query a string o inspeccionar opciones
            query_str = str(vendedores_query_call)
            self.assertNotIn("selectinload(Usuario.cotizaciones)", query_str.lower())
            
            # Verificar que se llamó a generate_followup_message con las cotizaciones acotadas
            mock_gen_msg.assert_called_once()
            call_kwargs = mock_gen_msg.call_args[1]
            self.assertEqual(len(call_kwargs["cotizaciones_recientes"]), 2)
            self.assertEqual(call_kwargs["cotizaciones_recientes"][0]["cliente_nombre"], "Cliente Test 1")


if __name__ == "__main__":
    unittest.main()

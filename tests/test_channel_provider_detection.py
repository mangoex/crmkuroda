"""TDD Unit test suite for channel resolution based on client AND provider numbers (400550 and 400260)."""

import unittest
from types import SimpleNamespace
from app.services.commercial_analytics import resolve_quote_effective_channel


class TestChannelProviderDetection(unittest.TestCase):
    def test_marketplace_detected_via_provider_number(self):
        """Punto 3: Verifica que 400550 en numero_proveedor o proveedor se resuelva como Market place."""
        q1 = SimpleNamespace(numero_cliente="12345", numero_proveedor="400550", canal="Normal")
        self.assertEqual(resolve_quote_effective_channel(q1), "Market place")

        q2 = SimpleNamespace(numero_cliente="", proveedor="000400550", canal="General")
        self.assertEqual(resolve_quote_effective_channel(q2), "Market place")

    def test_apartados_detected_via_provider_number(self):
        """Punto 3: Verifica que 400260 en numero_proveedor o proveedor se resuelva como Apartados."""
        q1 = SimpleNamespace(numero_cliente="9999", numero_proveedor="400260", canal="Normal")
        self.assertEqual(resolve_quote_effective_channel(q1), "Apartados")

        q2 = SimpleNamespace(numero_cliente=None, proveedor="400260.0", canal=None)
        self.assertEqual(resolve_quote_effective_channel(q2), "Apartados")

    def test_client_detection_still_works_deterministically(self):
        """Mantiene compatibilidad con detección por numero_cliente."""
        q1 = SimpleNamespace(numero_cliente="400550", numero_proveedor=None, canal="Entrega Inmediata")
        self.assertEqual(resolve_quote_effective_channel(q1), "Market place")

        q2 = SimpleNamespace(numero_cliente="400260", numero_proveedor=None, canal="Envío a Domicilio")
        self.assertEqual(resolve_quote_effective_channel(q2), "Apartados")

    def test_plazo_entrega_resolves_to_logistic_channels(self):
        """Verifica que plazo_entrega mapee a los canales canónicos/logísticos correspondientes."""
        cases = [
            ("ENTREGA INMEDIATA", "01", "Entrega Inmediata"),
            ("PIDE Y RECOGE", "01", "Pide y Recoge"),
            ("ENVÍO A DOMICILIO", "01", "Envío a Domicilio"),
            ("ENVIO A DOMICILIO", "01", "Envío a Domicilio"),
            ("SOBREPEDIDO", "01", "Sobrepedido"),
            ("ENVIO POR PAQUETERIA", "01", "Envío por Paquetería"),
            ("CTE RECO EN OTRA SUC", "01", "Cte Reco en Otra Suc"),
            ("OCURRE", "01", "Ocurre"),
            ("MERCANCIA RESGUARDO", "01", "Mercancía Resguardo"),
            ("KURODA TURBO", "01", "Kuroda Turbo"),
        ]
        for plazo, canal, expected in cases:
            q = SimpleNamespace(numero_cliente="400191", plazo_entrega=plazo, canal=canal)
            self.assertEqual(resolve_quote_effective_channel(q), expected, f"Fallo al resolver plazo: {plazo}")


if __name__ == "__main__":
    unittest.main()


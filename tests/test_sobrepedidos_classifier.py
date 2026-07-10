import unittest

from app.services.sobrepedidos_classifier import (
    STATUS_GREEN,
    STATUS_RED,
    STATUS_YELLOW,
    classify_sobrepedido,
)


class SobrepedidosClassifierTest(unittest.TestCase):
    def test_green_requires_exact_match_and_enough_quantity(self):
        result = classify_sobrepedido(
            estatus_compras="Sin Informacion de Compras",
            cantidad_pendiente=2,
            cantidad_disponible_exacta=2,
            tiene_coincidencia_factura=True,
            tiene_coincidencia_exacta=True,
        )

        self.assertEqual(result.estado_crm, STATUS_GREEN)

    def test_factura_only_match_is_yellow_not_green(self):
        result = classify_sobrepedido(
            estatus_compras="Sin Informacion de Compras",
            cantidad_pendiente=2,
            cantidad_disponible_exacta=0,
            tiene_coincidencia_factura=True,
            tiene_coincidencia_exacta=False,
        )

        self.assertEqual(result.estado_crm, STATUS_YELLOW)
        self.assertIn("no coincide el Codigo", result.motivo_estado)

    def test_back_order_without_date_is_red(self):
        result = classify_sobrepedido(
            estatus_compras="Confirmacion # 2012074 Back order sin fecha",
            cantidad_pendiente=1,
        )

        self.assertEqual(result.estado_crm, STATUS_RED)

    def test_supplier_invoice_without_logistics_is_green(self):
        result = classify_sobrepedido(
            estatus_compras="Fac 2759894 07.07.2026",
            cantidad_pendiente=1,
        )

        self.assertEqual(result.estado_crm, STATUS_GREEN)

    def test_no_purchase_info_without_logistics_is_red(self):
        result = classify_sobrepedido(
            estatus_compras="Sin Informacion de Compras",
            cantidad_pendiente=1,
        )

        self.assertEqual(result.estado_crm, STATUS_RED)


if __name__ == "__main__":
    unittest.main()

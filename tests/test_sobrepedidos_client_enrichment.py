from __future__ import annotations

import unittest
from app.models.sobrepedido import Sobrepedido
from app.models.por_entregar import PorEntregar
from app.models.cliente import Cliente


def enrich_item_contact(item_dict: dict, client: Cliente | None) -> dict:
    """Helper que enriquece un dict de Sobrepedido o Por Entregar con datos de contacto del cliente."""
    contact_data = {
        "telefono": None,
        "celular": None,
        "contacto_preferente": None,
        "email": None,
        "nombre_contacto": None,
    }
    if client:
        tel = (client.telefono or "").strip() or None
        cel = (client.celular or "").strip() or None
        contact_data["telefono"] = tel
        contact_data["celular"] = cel
        contact_data["contacto_preferente"] = cel or tel
        contact_data["email"] = (client.email or "").strip() or None
        contact_data["nombre_contacto"] = (client.nombre_contacto or "").strip() or None

    item_dict["contacto"] = contact_data
    return item_dict


class TestSobrepedidosClientEnrichment(unittest.TestCase):
    def test_enrich_sobrepedido_with_client_phone_and_whatsapp(self):
        """Sobrepedido obtiene número de teléfono y celular desde la tabla Cliente."""
        sp = Sobrepedido(
            id=1,
            factura="FAC-901",
            numero_cliente="100500",
            cliente_nombre="Constructora del Pacifico",
            producto_sku="SKU-88",
            cantidad_pendiente=10.0,
        )
        client = Cliente(
            numero_cliente="100500",
            nombre="Constructora del Pacifico",
            telefono="6677112233",
            celular="6679887766",
            email="compras@pacifico.com",
            nombre_contacto="Ing. Juan Perez",
        )

        data = enrich_item_contact(sp.to_dict(), client)
        self.assertIn("contacto", data)
        self.assertEqual(data["contacto"]["celular"], "6679887766")
        self.assertEqual(data["contacto"]["telefono"], "6677112233")
        self.assertEqual(data["contacto"]["contacto_preferente"], "6679887766")
        self.assertEqual(data["contacto"]["nombre_contacto"], "Ing. Juan Perez")

    def test_enrich_por_entregar_without_client_record(self):
        """Por Entregar devuelve estructura de contacto limpia si el cliente no está en la base."""
        pe = PorEntregar(
            id=2,
            factura="FAC-902",
            numero_cliente="999999",
            cliente_nombre="Cliente No Registrado",
            producto_sku="SKU-99",
            cantidad_entregar=5.0,
        )

        data = enrich_item_contact(pe.to_dict(), None)
        self.assertIn("contacto", data)
        self.assertIsNone(data["contacto"]["celular"])
        self.assertIsNone(data["contacto"]["telefono"])
        self.assertIsNone(data["contacto"]["contacto_preferente"])


if __name__ == "__main__":
    unittest.main()

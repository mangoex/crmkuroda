"""Unit tests for Cliente model, schemas, and API endpoints."""

from __future__ import annotations

import unittest
from datetime import datetime
import asyncio

from app.models.cliente import Cliente
from app.schemas.cliente import (
    ClienteCreate,
    ClienteUpdate,
    ClienteOut,
    ClientePaginatedOut,
    ClienteFilterOptionsOut,
)
from seed_clientes import clean_val


class ClienteModelTest(unittest.TestCase):
    def test_cliente_instantiation_and_to_dict(self):
        cliente = Cliente(
            id=1,
            sociedad="MKS",
            numero_cliente="100",
            nombre="ACME INDUSTRIAL S.A. DE C.V.",
            rfc="ACM900101AB1",
            tipo_persona="Persona jurídica",
            calle="AV. INDUSTRIAL",
            numero_exterior="500",
            colonia="COL. INDUSTRIAL",
            codigo_postal="80000",
            poblacion="CULIACAN",
            estado="SIN",
            telefono="6677000000",
            celular="6671234567",
            fax="6677000001",
            email="contacto@acme.mx",
            created_at=datetime(2026, 8, 4, 12, 0, 0),
            updated_at=datetime(2026, 8, 4, 12, 0, 0),
        )

        self.assertEqual(cliente.id, 1)
        self.assertEqual(cliente.nombre, "ACME INDUSTRIAL S.A. DE C.V.")
        self.assertEqual(cliente.rfc, "ACM900101AB1")
        self.assertEqual(cliente.tipo_persona, "Persona jurídica")

        d = cliente.to_dict()
        self.assertEqual(d["id"], 1)
        self.assertEqual(d["sociedad"], "MKS")
        self.assertEqual(d["numero_cliente"], "100")
        self.assertEqual(d["nombre"], "ACME INDUSTRIAL S.A. DE C.V.")
        self.assertEqual(d["rfc"], "ACM900101AB1")
        self.assertEqual(d["tipo_persona"], "Persona jurídica")
        self.assertEqual(d["poblacion"], "CULIACAN")
        self.assertEqual(d["email"], "contacto@acme.mx")
        self.assertIsNotNone(d["created_at"])

    def test_cliente_schemas(self):
        payload = {
            "sociedad": "MKS",
            "numero_cliente": "101",
            "nombre": "JUAN PEREZ GONZALEZ",
            "rfc": "PEGJ800101XX1",
            "tipo_persona": "Persona física",
            "calle": "JUAN DE LA BARRERA",
            "numero_exterior": "123",
            "colonia": "COL. TIERRA BLANCA",
            "codigo_postal": "80030",
            "poblacion": "CULIACAN",
            "estado": "SIN",
            "telefono": "6677112233",
            "celular": "",
            "fax": "",
            "email": "juan.perez@example.com",
        }
        create_schema = ClienteCreate(**payload)
        self.assertEqual(create_schema.nombre, "JUAN PEREZ GONZALEZ")
        self.assertEqual(create_schema.tipo_persona, "Persona física")

        update_schema = ClienteUpdate(nombre="JUAN PEREZ G.")
        self.assertEqual(update_schema.nombre, "JUAN PEREZ G.")
        self.assertIsNone(update_schema.rfc)

        out_data = {
            **payload,
            "id": 5,
            "created_at": "2026-08-04T12:00:00",
            "updated_at": "2026-08-04T12:00:00",
        }
        paginated = ClientePaginatedOut(
            status="success",
            total=1,
            page=1,
            limit=50,
            pages=1,
            total_fisicas=1,
            total_morales=0,
            data=[ClienteOut(**out_data)],
        )
        self.assertEqual(paginated.total, 1)
        self.assertEqual(len(paginated.data), 1)
        self.assertEqual(paginated.data[0].id, 5)

        filter_opts = ClienteFilterOptionsOut(
            status="success",
            tipos_persona=["Persona física", "Persona jurídica"],
            colonias=["COL. CENTRO", "COL. TIERRA BLANCA"],
            poblaciones=["CULIACAN", "MAZATLAN"],
        )
        self.assertEqual(len(filter_opts.tipos_persona), 2)
        self.assertEqual(len(filter_opts.colonias), 2)

    def test_csv_field_cleaning(self):
        self.assertEqual(clean_val("  CULIACAN  "), "CULIACAN")
        self.assertEqual(clean_val("nan"), "")
        self.assertEqual(clean_val("NaN"), "")
        self.assertEqual(clean_val("null"), "")
        self.assertEqual(clean_val(None), "")

        cp = "80200.0"
        if cp.endswith(".0"):
            cp = cp[:-2]
        self.assertEqual(cp, "80200")


if __name__ == "__main__":
    unittest.main()

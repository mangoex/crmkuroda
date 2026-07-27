import io
import unittest
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import openpyxl
from fastapi import HTTPException, UploadFile

from app.api.v1.cotizaciones import (
    _apply_imported_quote_values,
    _get_authorized_quote,
    create_quote_comment,
    update_quote_comment,
    upload_quote_material_detail,
)
from app.api.v1.commercial_analytics import sales_by_channel
from app.schemas.commercial import ComentarioCreate, ComentarioUpdate


class FakeScalarResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return list(self.values)

    def first(self):
        return self.values[0] if self.values else None


class FakeDatabase:
    def __init__(self, execute_results):
        self.execute_results = list(execute_results)
        self.added = []
        self.added_many = []
        self.commits = 0
        self.execute_calls = 0

    async def execute(self, _statement):
        self.execute_calls += 1
        if self.execute_results:
            return self.execute_results.pop(0)
        return FakeScalarResult([])

    def add(self, item):
        self.added.append(item)

    def add_all(self, items):
        self.added_many.extend(items)

    async def commit(self):
        self.commits += 1

    async def refresh(self, item):
        if item.id is None:
            item.id = uuid4()
        if getattr(item, "creado_en", None) is None:
            item.creado_en = datetime.utcnow()


def build_detail_workbook(rows):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(
        [
            "Numero de Cotizacion",
            "Codigo Material",
            "Descripcion",
            "Familia",
            "Grupo de Materiales",
            "Cantidad Cotizada",
            "Importe Cotizado",
            "Cantidad Facturada",
            "Importe Facturado",
        ]
    )
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


class CommercialApiWorkflowTest(unittest.IsolatedAsyncioTestCase):
    async def test_summary_reconciliation_preserves_followup_fields(self):
        quote_id = uuid4()
        quote = SimpleNamespace(
            id=quote_id,
            numero_cotizacion="COT-1",
            total=100,
            comentarios="motivo histórico",
            comentarios_seguimiento=["seguimiento"],
        )

        result = _apply_imported_quote_values(
            quote,
            {
                "numero_cotizacion": "COT-1",
                "total": 250,
                "cliente_nombre": "Cliente actualizado",
            },
        )

        self.assertIs(result, quote)
        self.assertEqual(result.id, quote_id)
        self.assertEqual(result.total, 250)
        self.assertEqual(result.comentarios, "motivo histórico")
        self.assertEqual(result.comentarios_seguimiento, ["seguimiento"])

    async def test_support_role_cannot_access_commercial_analytics(self):
        user = SimpleNamespace(id=uuid4(), rol="soporte")
        database = FakeDatabase([])

        with self.assertRaises(HTTPException) as raised:
            await sales_by_channel(
                fecha_inicio=None,
                fecha_fin=None,
                vendedor_id=None,
                sin_vincular=False,
                db=database,
                current_user=user,
            )

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(database.execute_calls, 0)

    async def test_support_role_cannot_add_followup_comments(self):
        user = SimpleNamespace(id=uuid4(), rol="soporte")
        database = FakeDatabase([])

        with self.assertRaises(HTTPException) as raised:
            await create_quote_comment(
                uuid4(),
                ComentarioCreate(comentario="No permitido"),
                database,
                user,
            )

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(database.execute_calls, 0)

    async def test_seller_can_open_historical_quote_linked_by_name(self):
        user_id = uuid4()
        quote = SimpleNamespace(
            id=uuid4(),
            vendedor_id=None,
            vendedor_nombre="ANA ASESORA",
        )
        user = SimpleNamespace(
            id=user_id,
            rol="vendedor",
            codigo_vendedor="A01",
            nombre_completo="Ana Asesora",
            email="ana@example.com",
        )
        database = FakeDatabase(
            [
                FakeScalarResult([quote]),
                FakeScalarResult([]),
                FakeScalarResult([user]),
            ]
        )

        result = await _get_authorized_quote(database, user, quote.id)

        self.assertIs(result, quote)

    async def test_name_fallback_cannot_override_a_different_linked_seller(self):
        user_id = uuid4()
        quote = SimpleNamespace(
            id=uuid4(),
            vendedor_id=uuid4(),
            vendedor_nombre="Ana Asesora",
        )
        user = SimpleNamespace(
            id=user_id,
            rol="vendedor",
            codigo_vendedor="A01",
            nombre_completo="Ana Asesora",
            email="ana@example.com",
        )
        database = FakeDatabase(
            [
                FakeScalarResult([quote]),
                FakeScalarResult([]),
            ]
        )

        with self.assertRaises(HTTPException) as raised:
            await _get_authorized_quote(database, user, quote.id)

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(database.execute_calls, 2)

    async def test_material_upload_replaces_detail_only_after_valid_rows(self):
        quote_id = uuid4()
        quote = SimpleNamespace(id=quote_id, numero_cotizacion="COT-1")
        database = FakeDatabase([FakeScalarResult([quote]), FakeScalarResult([])])
        upload = UploadFile(
            filename="detalle.xlsx",
            file=build_detail_workbook(
                [["COT-1", "SKU-1", "Piso", "Acabados", "Pisos", 2, 200, 1, 100]]
            ),
        )
        user = SimpleNamespace(id=uuid4(), rol="gerente")

        result = await upload_quote_material_detail(upload, database, user)

        self.assertEqual(result["aceptadas"], 1)
        self.assertEqual(result["rechazadas"], 0)
        self.assertEqual(database.added_many[0].cotizacion_id, quote_id)
        self.assertEqual(database.added_many[0].codigo_material, "SKU-1")
        self.assertEqual(database.commits, 1)
        self.assertEqual(database.execute_calls, 2)

    async def test_invalid_material_upload_does_not_delete_existing_detail(self):
        quote = SimpleNamespace(id=uuid4(), numero_cotizacion="COT-1")
        database = FakeDatabase([FakeScalarResult([quote])])
        upload = UploadFile(
            filename="detalle.xlsx",
            file=build_detail_workbook(
                [["NO-EXISTE", "SKU-1", "Piso", "Acabados", "Pisos", 2, 200, 1, 100]]
            ),
        )
        user = SimpleNamespace(id=uuid4(), rol="gerente")

        with self.assertRaises(HTTPException) as raised:
            await upload_quote_material_detail(upload, database, user)

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(database.execute_calls, 1)
        self.assertEqual(database.commits, 0)
        self.assertEqual(database.added_many, [])

    async def test_followup_comment_is_independent_from_legacy_comments(self):
        quote = SimpleNamespace(
            id=uuid4(),
            vendedor_id=uuid4(),
            vendedor_nombre="Asesor",
            comentarios='{"lost_reason":{"reasons":["precio"]}}',
        )
        database = FakeDatabase([FakeScalarResult([quote])])
        user = SimpleNamespace(
            id=uuid4(),
            rol="gerente",
            nombre_completo="Gerente",
            email="gerente@example.com",
        )

        result = await create_quote_comment(
            quote.id,
            ComentarioCreate(comentario="  Llamar el lunes  "),
            database,
            user,
        )

        self.assertEqual(result["data"]["comentario"], "Llamar el lunes")
        self.assertEqual(
            quote.comentarios,
            '{"lost_reason":{"reasons":["precio"]}}',
        )
        self.assertEqual(database.commits, 1)

    async def test_comment_author_can_edit_without_changing_legacy_comment(self):
        user_id = uuid4()
        quote = SimpleNamespace(
            id=uuid4(),
            vendedor_id=user_id,
            vendedor_nombre="Ana",
            comentarios="motivo histórico",
        )
        comment = SimpleNamespace(
            id=uuid4(),
            cotizacion_id=quote.id,
            autor_id=user_id,
            comentario="Llamar",
            creado_en=datetime.utcnow(),
            editado_en=None,
        )
        user = SimpleNamespace(
            id=user_id,
            rol="vendedor",
            codigo_vendedor="A01",
            nombre_completo="Ana",
            email="ana@example.com",
        )
        database = FakeDatabase(
            [
                FakeScalarResult([quote]),
                FakeScalarResult([]),
                FakeScalarResult([comment]),
                FakeScalarResult([user]),
            ]
        )

        result = await update_quote_comment(
            quote.id,
            comment.id,
            ComentarioUpdate(comentario="  Visita confirmada  "),
            database,
            user,
        )

        self.assertEqual(result["data"]["comentario"], "Visita confirmada")
        self.assertEqual(quote.comentarios, "motivo histórico")
        self.assertIsNotNone(comment.editado_en)
        self.assertEqual(database.commits, 1)

    async def test_seller_cannot_edit_another_authors_comment(self):
        user_id = uuid4()
        quote = SimpleNamespace(id=uuid4(), vendedor_id=user_id, vendedor_nombre="Ana")
        comment = SimpleNamespace(
            id=uuid4(),
            cotizacion_id=quote.id,
            autor_id=uuid4(),
            comentario="No editable",
        )
        user = SimpleNamespace(
            id=user_id,
            rol="vendedor",
            codigo_vendedor="A01",
            nombre_completo="Ana",
            email="ana@example.com",
        )
        database = FakeDatabase(
            [
                FakeScalarResult([quote]),
                FakeScalarResult([]),
                FakeScalarResult([comment]),
            ]
        )

        with self.assertRaises(HTTPException) as raised:
            await update_quote_comment(
                quote.id,
                comment.id,
                ComentarioUpdate(comentario="Intento"),
                database,
                user,
            )

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(database.commits, 0)


if __name__ == "__main__":
    unittest.main()

import io
import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import openpyxl
from fastapi import UploadFile

from app.api.v1.promociones import upload_promociones
from app.models.promocion import Promocion


class FakeScalarResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None

    def scalars(self):
        return self

    def scalar(self):
        return len(self._items)


class FakeDatabase:
    def __init__(self):
        self.added_all = []
        self.executed_queries = []
        self.commits = 0
        self.rollbacks = 0

    async def execute(self, query):
        self.executed_queries.append(query)
        # Mocking empty existing relevant SKUs
        return FakeScalarResult([])

    def add_all(self, items):
        self.added_all.extend(items)

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


class TestPromocionesNuevoFormatoTDD(unittest.IsolatedAsyncioTestCase):
    """
    Suite TDD bajo especificación SBD para validar el soporte integral
    del nuevo formato de base de datos de promociones (Promocion 08.10.2026.xlsx).
    """

    def setUp(self):
        self.user = SimpleNamespace(id=uuid4(), rol="admin")
        self.db = FakeDatabase()

    def build_test_workbook(self, rows):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        # Encabezados exactos del nuevo formato (15 columnas)
        headers = [
            "Centro",
            "Descrip Gpo Materiales",
            "Indicador ABC+Frecuencia de Venta",
            "Codigo Material",
            "Descripcion del Material",
            "Unidad de Medida Base",
            "Costo Promedio Unitario",
            "Costo Promedio Unitario Moneda de Venta",
            "Precio Efectivo de Promocion con IVA",
            "Moneda",
            "Valido hasta Promocion",
            "Valido desde Promocion",
            "Margen Promocion",
            "Proveedor",
            "Inventario disponible",
        ]
        ws.append(headers)
        for r in rows:
            ws.append(r)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    async def test_nuevo_formato_excel_mapea_precio_con_iva_y_fechas_correctamente(self):
        """
        GHERKIN:
        Dado un archivo Excel con encabezado 'Precio Efectivo de Promocion con IVA' y 'Valido desde Promocion'
        Cuando se procesa la importación
        Entonces precio_promocion se mapea con su valor numérico real (no None)
        Y valido_desde y valido_hasta se almacenan como fechas válidas.
        """
        rows = [
            [
                "MK01",
                "PLOMERIA CROMADA",
                "D6",
                "DC07",
                "CEPILLERO DECO CROMO",
                "PI",
                383.14,
                383.14,
                488.39,
                "MXN",
                datetime(2026, 10, 19),
                datetime(2026, 10, 8),
                18.1,
                "HELVEX",
                5.0,
            ]
        ]
        buf = self.build_test_workbook(rows)
        upload_file = UploadFile(filename="Promocion_08.10.2026_test.xlsx", file=buf)

        with patch("app.api.v1.promociones.registrar_actualizacion_datos", new=AsyncMock()):
            res = await upload_promociones(upload_file, self.db, self.user)

        self.assertEqual(res["status"], "success")
        self.assertEqual(len(self.db.added_all), 1)

        item = self.db.added_all[0]
        self.assertEqual(item.codigo_material, "DC07")
        self.assertIsNotNone(item.precio_promocion, "El precio de promoción no debe ser None")
        self.assertAlmostEqual(item.precio_promocion, 488.39, places=2)
        self.assertEqual(item.moneda, "MXN")
        self.assertTrue(hasattr(item, "valido_desde"), "El modelo Promocion debe poseer el campo valido_desde")
        self.assertEqual(item.valido_desde, datetime(2026, 10, 8))
        self.assertEqual(item.valido_hasta, datetime(2026, 10, 19))
        self.assertEqual(item.inventario_disponible, 5.0)

    async def test_nuevo_formato_descarta_filas_corruptas_o_precio_cero(self):
        """
        GHERKIN:
        Dada una fila corrupta con precio 0.0 o sin vigencias válidas (como la fila 3009)
        Cuando se procesa la importación
        Entonces la fila es omitida y no se inserta en la base de datos con precio 0.
        """
        rows = [
            # Fila válida 1
            [
                "MK01", "ACCESORIOS", "D5", "ACC107EB", "PORTACEPILLOS", "PI",
                500.0, 500.0, 688.81, "MXN", datetime(2026, 10, 19), datetime(2026, 10, 8),
                15.0, "HELVEX", 2.0
            ],
            # Fila corrupta tipo 3009 (Precio 0.0, sin fechas)
            [
                "MK01", "BOMBAS", "E5", "ROBPINT120", "BOMBA PRESURIZADOR INTELIGENTE", "PI",
                4389.45, 4389.45, 0.0, None, None, None,
                0.0, "ROTOPLAS", 0.0
            ]
        ]
        buf = self.build_test_workbook(rows)
        upload_file = UploadFile(filename="Promocion_con_corrupto.xlsx", file=buf)

        with patch("app.api.v1.promociones.registrar_actualizacion_datos", new=AsyncMock()):
            res = await upload_promociones(upload_file, self.db, self.user)

        self.assertEqual(res["status"], "success")
        self.assertEqual(len(self.db.added_all), 1, "La fila corrupta con precio 0.0 debió ser descartada")
        self.assertEqual(self.db.added_all[0].codigo_material, "ACC107EB")

    async def test_modelo_promocion_to_dict_incluye_valido_desde(self):
        """
        GHERKIN:
        Dado un objeto Promocion con valido_desde asignado
        Cuando se llama to_dict()
        Entonces el diccionario resultante contiene 'valido_desde' en formato ISO.
        """
        promo = Promocion(
            id=10,
            centro="MK01",
            codigo_material="SKU-TEST",
            descripcion_material="Producto Test",
            precio_promocion=120.50,
            valido_desde=datetime(2026, 10, 1, 0, 0, 0),
            valido_hasta=datetime(2026, 10, 31, 23, 59, 59),
        )
        data = promo.to_dict()
        self.assertIn("valido_desde", data)
        self.assertEqual(data["valido_desde"], "2026-10-01T00:00:00")
        self.assertEqual(data["valido_hasta"], "2026-10-31T23:59:59")

    async def test_archivo_real_promocion_08_10_2026_importa_sin_precios_nulos_y_filtra_corruptos(self):
        """
        Prueba de integración end-to-end con el archivo real 'Promocion 08.10.2026.xlsx'.
        Valida que de los 3066 registros:
        - Exactamente 3065 filas válidas sean procesadas (fila 3009 con $0.00 descartada).
        - El 100% de las 3065 filas tengan precio_promocion > 0 (0 precios None, 0 precios <= 0).
        - valido_desde y valido_hasta estén presentes y tipados correctamente.
        """
        real_file_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "Promocion 08.10.2026.xlsx"
        )
        if not os.path.exists(real_file_path):
            real_file_path = r"C:\Users\Miguel Gonzalez\Downloads\CRMK\Promocion 08.10.2026.xlsx"

        if not os.path.exists(real_file_path):
            self.skipTest(f"Archivo real no encontrado en {real_file_path}")

        with open(real_file_path, "rb") as f:
            file_bytes = f.read()

        upload_file = UploadFile(
            filename="Promocion 08.10.2026.xlsx", file=io.BytesIO(file_bytes)
        )

        with patch("app.api.v1.promociones.registrar_actualizacion_datos", new=AsyncMock()):
            res = await upload_promociones(upload_file, self.db, self.user)

        self.assertEqual(res["status"], "success")
        total_importadas = len(self.db.added_all)
        self.assertEqual(total_importadas, 3065, "Deben importarse 3065 filas (filtrando la corrupta de $0.0)")

        # Verificar que ni una sola fila tenga precio None ni <= 0
        precios_nulos = [p for p in self.db.added_all if p.precio_promocion is None]
        precios_cero = [p for p in self.db.added_all if p.precio_promocion <= 0]
        self.assertEqual(len(precios_nulos), 0, "No debe haber ningún registro con precio None")
        self.assertEqual(len(precios_cero), 0, "No debe haber ningún registro con precio <= 0")

        # Verificar que la fila corrupta (MK01 con precio 0.0) fue descartada, pero MK03 y MK04 con precio 6799.0 se conservaron
        rob_mk01 = [p for p in self.db.added_all if p.codigo_material == "ROBPINT120" and p.centro == "MK01"]
        self.assertEqual(len(rob_mk01), 0, "La fila corrupta de ROBPINT120 en MK01 con precio 0.0 no debe haber sido importada")

        rob_validos = [p for p in self.db.added_all if p.codigo_material == "ROBPINT120"]
        self.assertEqual(len(rob_validos), 2, "Deben existir 2 registros válidos de ROBPINT120 (MK03 y MK04)")
        self.assertTrue(all(p.precio_promocion == 6799.0 for p in rob_validos))

        # Verificar que valido_desde y valido_hasta estén poblados
        con_valido_desde = sum(1 for p in self.db.added_all if p.valido_desde is not None)
        con_valido_hasta = sum(1 for p in self.db.added_all if p.valido_hasta is not None)
        self.assertEqual(con_valido_desde, 3065)
        self.assertEqual(con_valido_hasta, 3065)

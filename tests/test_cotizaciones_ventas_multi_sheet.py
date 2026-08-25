import io
from datetime import date, time, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import unittest
from uuid import uuid4
import openpyxl

from app.models.cotizacion import Cotizacion
from app.models.cotizacion_detalle import CotizacionItem
from app.models.promocion import Promocion
from app.models.usuario import Usuario
from app.api.v1.cotizaciones import (
    process_excel_background,
    generate_excel_template_bytes,
    is_multi_sheet_quote_format,
    serialize_cotizacion,
)
from app.services.commercial_analytics import get_promociones_intelligence_summary


def create_test_multisheet_excel_bytes() -> bytes:
    wb = openpyxl.Workbook()
    # Sheet 1: Ventas
    ws_ventas = wb.active
    ws_ventas.title = "Ventas"
    ws_ventas.append([
        "Fecha de Factura",
        "Numero del Cliente",
        "Plazo de Entrega",
        "Nombre del Cliente",
        "Folio Cotizacion",
        "Folio Factura",
        "Hora de Facturacion",
        "Margen",
        "Grupo de Vendedores",
        "Nombre del Vendedor",
        "Canal de Distribucion",
    ])
    ws_ventas.append([
        datetime(2026, 1, 15),
        "400191",
        "ENTREGA INMEDIATA",
        "PRODIVERSO CASA KURODA",
        "COT-1001",
        "FAC-9001",
        time(10, 30, 0),
        35.5,
        "C82",
        "Juan Perez",
        "01",
    ])
    ws_ventas.append([
        datetime(2026, 1, 16),
        "400200",
        "SOBREPEDIDO",
        "CONSTRUCTORA DEL NORTE",
        "COT-1002",
        "FAC-9002",
        time(14, 15, 0),
        28.0,
        "C94",
        "Maria Lopez",
        "02",
    ])

    # Sheet 2: Cotizaciones
    ws_cotizaciones = wb.create_sheet(title="Cotizaciones")
    ws_cotizaciones.append([
        "Fecha de Registro",
        "Organizacion de Ventas",
        "Numero de Cotizacion",
        "Indicador ABC+Frecuencia de Venta",
        "Codigo de Material",
        "Descripcion del Material",
        "Unidad de Medida",
        "Precio de Venta",
    ])
    # Items for COT-1001 (Partida 1: SKU Promo, Partida 2: Normal)
    ws_cotizaciones.append([
        datetime(2026, 1, 10),
        "MK01",
        "COT-1001",
        "C6",
        "SKU-PROMO-01",
        "VALVULA RETENCION 25MM",
        "PZA",
        150.00,
    ])
    ws_cotizaciones.append([
        datetime(2026, 1, 10),
        "MK01",
        "COT-1001",
        "A1",
        "SKU-NORMAL-01",
        "TUBO PVC HIDRAULICO 2 PULG",
        "TRAMO",
        250.00,
    ])
    # Items for COT-1002
    ws_cotizaciones.append([
        datetime(2026, 1, 12),
        "MK01",
        "COT-1002",
        "B2",
        "SKU-NORMAL-02",
        "PISO CERAMICO 60X60",
        "M2",
        300.00,
    ])
    # COT-1003 is a pending/lost quote without invoice in Ventas
    ws_cotizaciones.append([
        datetime(2026, 1, 14),
        "MK01",
        "COT-1003",
        "D6",
        "SKU-PROMO-02",
        "INSERTO DECORATIVO BEIGE",
        "PZA",
        80.00,
    ])

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


class FakeScalarResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return list(self.values)

    def first(self):
        return self.values[0] if self.values else None


class FakeAsyncSession:
    def __init__(self, users=None, promos=None, clients=None, quotes=None):
        self.users = users or []
        self.promos = promos or []
        self.clients = clients or []
        self.quotes = quotes or []
        self.added = []
        self.added_all_list = []
        self.deleted = []
        self.commits = 0
        self.flushes = 0

    async def execute(self, statement):
        str_stmt = str(statement).lower()
        if "from promociones" in str_stmt:
            return FakeScalarResult(self.promos)
        elif "from usuarios" in str_stmt:
            return FakeScalarResult(self.users)
        elif "from clientes" in str_stmt:
            return FakeScalarResult(self.clients)
        elif "from cotizaciones" in str_stmt:
            return FakeScalarResult(self.quotes)
        return FakeScalarResult([])

    def add(self, item):
        self.added.append(item)

    def add_all(self, items):
        self.added_all_list.extend(items)

    async def flush(self):
        self.flushes += 1

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestCotizacionesVentasMultiSheet(unittest.IsolatedAsyncioTestCase):
    def test_detect_multisheet_format(self):
        excel_bytes = create_test_multisheet_excel_bytes()
        wb = openpyxl.load_workbook(io.BytesIO(excel_bytes), read_only=True)
        self.assertTrue(is_multi_sheet_quote_format(wb))

    def test_generate_excel_template_bytes(self):
        template_bytes = generate_excel_template_bytes()
        self.assertGreater(len(template_bytes), 0)

        wb = openpyxl.load_workbook(io.BytesIO(template_bytes))
        self.assertIn("Ventas", wb.sheetnames)
        self.assertIn("Cotizaciones", wb.sheetnames)
        self.assertIn("Instrucciones", wb.sheetnames)

        ws_v = wb["Ventas"]
        ventas_headers = [c.value for c in ws_v[1]]
        self.assertIn("Fecha de Factura", ventas_headers)
        self.assertIn("Folio Cotizacion", ventas_headers)
        self.assertIn("Margen", ventas_headers)
        self.assertIn("Grupo de Vendedores", ventas_headers)

        ws_c = wb["Cotizaciones"]
        cot_headers = [c.value for c in ws_c[1]]
        self.assertIn("Numero de Cotizacion", cot_headers)
        self.assertIn("Codigo de Material", cot_headers)
        self.assertIn("Precio de Venta", cot_headers)

    async def test_process_excel_background_multisheet(self):
        user_id = uuid4()
        user = Usuario(id=user_id, nombre_completo="Juan Perez", codigo_vendedor="C82", rol="vendedor")
        promo = Promocion(
            id=1,
            centro="MK01",
            codigo_material="SKU-PROMO-01",
            descripcion_material="VALVULA RETENCION 25MM",
            precio_promocion=120.0,
        )

        fake_session = FakeAsyncSession(users=[user], promos=[promo], quotes=[])

        with patch("app.core.database.SessionLocal", return_value=fake_session), \
             patch("app.services.actualizaciones_datos.registrar_actualizacion_datos", new=AsyncMock()):
            excel_bytes = create_test_multisheet_excel_bytes()
            err = await process_excel_background(excel_bytes, user_id)
            self.assertIsNone(err)

            # Check quotes added
            added_quotes = [item for item in fake_session.added if isinstance(item, Cotizacion)]
            self.assertEqual(len(added_quotes), 3)

            quote_1001 = next(q for q in added_quotes if q.numero_cotizacion == "COT-1001")
            self.assertEqual(quote_1001.cliente_nombre, "PRODIVERSO CASA KURODA")
            self.assertEqual(quote_1001.numero_factura, "FAC-9001")
            self.assertEqual(quote_1001.total, Decimal("400.00"))
            self.assertEqual(float(quote_1001.margen), 35.5)
            self.assertEqual(quote_1001.grupo_vendedores, "C82")
            self.assertEqual(quote_1001.plazo_entrega, "ENTREGA INMEDIATA")

            # Check line items added
            added_items = [item for item in fake_session.added_all_list if isinstance(item, CotizacionItem)]
            self.assertEqual(len(added_items), 4)

            promo_item = next(i for i in added_items if i.codigo_material == "SKU-PROMO-01")
            self.assertTrue(promo_item.es_promocion)
            self.assertEqual(promo_item.indicador_abcf, "C6")
            self.assertEqual(promo_item.unidad_medida, "PZA")
            self.assertEqual(promo_item.precio_venta, Decimal("150.00"))

            normal_item = next(i for i in added_items if i.codigo_material == "SKU-NORMAL-01")
            self.assertFalse(normal_item.es_promocion)

    async def test_promociones_intelligence_summary(self):
        class FakeSummaryResult:
            def __init__(self, rows):
                self.rows = rows

            def all(self):
                return self.rows

        q1 = Cotizacion(id=uuid4(), numero_cotizacion="C-1", numero_factura="F-1", vendedor_nombre="Juan Perez", total=Decimal("500"), importe_facturado=Decimal("500"))
        i1 = CotizacionItem(id=uuid4(), cotizacion_id=q1.id, codigo_material="SKU-PROMO-1", descripcion="PROMO 1", es_promocion=True, precio_venta=Decimal("200"), importe_cotizado=Decimal("200"), importe_facturado=Decimal("200"))

        q2 = Cotizacion(id=uuid4(), numero_cotizacion="C-2", numero_factura=None, vendedor_nombre="Maria Lopez", total=Decimal("300"), importe_facturado=None)
        i2 = CotizacionItem(id=uuid4(), cotizacion_id=q2.id, codigo_material="SKU-PROMO-1", descripcion="PROMO 1", es_promocion=True, precio_venta=Decimal("150"), importe_cotizado=Decimal("150"), importe_facturado=Decimal("0"))

        fake_db = AsyncMock()
        fake_db.execute.return_value = FakeSummaryResult([(i1, q1), (i2, q2)])

        metrics = await get_promociones_intelligence_summary(fake_db)
        self.assertEqual(metrics["total_cotizaciones_con_promo"], 2)
        self.assertEqual(metrics["total_cotizaciones_promo_facturadas"], 1)
        self.assertEqual(metrics["total_partidas_promo"], 2)
        self.assertEqual(metrics["total_monto_cotizado_promo"], 350.0)
        self.assertEqual(metrics["total_monto_facturado_promo"], 200.0)
        self.assertEqual(metrics["tasa_efectividad_promo"], 50.0)
        self.assertEqual(len(metrics["top_skus_promo"]), 1)
        self.assertEqual(metrics["top_skus_promo"][0]["codigo_material"], "SKU-PROMO-1")

    def test_serialize_cotizacion_resumen_contains_all_multisheet_fields(self):
        quote = Cotizacion(
            id=uuid4(),
            cliente_nombre="Cliente Test",
            numero_cliente="12345",
            datos_contacto={"telefono": "6671234567"},
            total=Decimal("1500.00"),
            numero_cotizacion="COT-TEST",
            fecha_registro=date(2026, 1, 15),
            canal="01",
            numero_factura="FAC-123",
            fecha_factura=date(2026, 1, 16),
            hora_facturacion="10:30:00",
            margen=Decimal("35.500"),
            grupo_vendedores="C82",
            plazo_entrega="ENTREGA INMEDIATA",
            importe_facturado=Decimal("1500.00"),
            venta_perdida="No",
            comentarios="Comentario de prueba",
        )
        serialized = serialize_cotizacion(quote, vista="resumen")
        self.assertEqual(serialized["hora_facturacion"], "10:30:00")
        self.assertEqual(serialized["margen"], 35.5)
        self.assertEqual(serialized["grupo_vendedores"], "C82")
        self.assertEqual(serialized["plazo_entrega"], "ENTREGA INMEDIATA")
        self.assertEqual(serialized["numero_factura"], "FAC-123")
        self.assertEqual(serialized["importe_facturado"], 1500.00)


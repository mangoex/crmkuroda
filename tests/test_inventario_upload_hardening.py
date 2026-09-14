"""TDD Test Suite for Inventario D upload hardening, reference price resolution, and auto-healing."""

import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from openpyxl import Workbook
from fastapi import UploadFile

from app.models.inventario_abcf import InventarioAbcf
from app.models.promocion import Promocion
from app.models.cotizacion import Cotizacion
from app.models.usuario import Usuario


@pytest.fixture
def mock_admin_user():
    user = MagicMock(spec=Usuario)
    user.id = "00000000-0000-0000-0000-000000000001"
    user.rol = "admin"
    return user


def create_excel_upload_file(headers, rows, sheet_name="Sheet1"):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return UploadFile(filename="test_inventario.xlsx", file=buf)


@pytest.mark.asyncio
async def test_get_reference_pricing_catalog_combines_sources():
    from app.api.v1.inventario_abcf import get_reference_pricing_catalog

    mock_db = AsyncMock()

    # 1. Existing InventarioAbcf
    mock_inv_res = MagicMock()
    mock_inv_res.all.return_value = [("VATTIUM10-220", 3755.03)]

    # 2. Promocion
    mock_promo_res = MagicMock()
    mock_promo_res.all.return_value = [("FORTISG15", 5685.00, 3597.95)]

    # 1. Cotizaciones JSONB
    mock_quote_res = MagicMock()
    mock_quote_res.all.return_value = [([{"producto": "MOEN100", "precio_unitario": 1250.00}],)]

    # 2. Existing InventarioAbcf
    mock_inv_res = MagicMock()
    mock_inv_res.all.return_value = [("VATTIUM10-220", 3755.03)]

    # 3. Promocion (highest priority)
    mock_promo_res = MagicMock()
    mock_promo_res.all.return_value = [("FORTISG15", 5685.00, 3597.95)]

    mock_db.execute.side_effect = [mock_quote_res, mock_inv_res, mock_promo_res]

    catalog = await get_reference_pricing_catalog(mock_db)

    assert catalog.get("VATTIUM10-220") == 3755.03
    assert catalog.get("FORTISG15") == 5685.00
    assert catalog.get("MOEN100") == 1250.00


@pytest.mark.asyncio
async def test_upload_preserves_prices_when_file_lacks_cost_columns(mock_admin_user):
    from app.api.v1.inventario_abcf import upload_inventario

    # SAP style export: only physical stock columns, NO cost or price columns
    headers = [
        "Centro", "Almacen", "Numero de Proveedor", "Nombre del Proveedor",
        "Indicador ABC+Frecuencia de Venta", "Codigo Material", "Descripcion Material",
        "Cantidad Propia", "Existencia en Consignacion de Proveedore"
    ]
    rows = [
        ["MKS CASA KURODA", "MA01", "103484", "ARISTON SALES", "D5", "VATTIUM10-220", "CALENTADOR VATTIUM", 2.0, 0.0],
        ["MKS CASA KURODA", "MA01", "100066", "ASIENTOS", "D6", "AV9102", "ASIENTO REDONDO", 0.0, 5.0]
    ]
    upload_file = create_excel_upload_file(headers, rows)

    mock_db = AsyncMock()
    saved_items = []
    mock_db.add = MagicMock(side_effect=lambda item: saved_items.append(item))

    # Mock pre-cache catalog: VATTIUM10-220 -> 3755.03, AV9102 -> 140.0
    with patch("app.api.v1.inventario_abcf.get_reference_pricing_catalog", new=AsyncMock(return_value={
        "VATTIUM10-220": 3755.03,
        "AV9102": 140.0
    })), patch("app.api.v1.inventario_abcf.registrar_actualizacion_datos", new=AsyncMock()):

        res = await upload_inventario(file=upload_file, db=mock_db, current_user=mock_admin_user)

        assert res["status"] == "success"
        assert len(saved_items) == 2

        vattium = next(i for i in saved_items if i.codigo_material == "VATTIUM10-220")
        assert vattium.costo_promedio_unitario == 3755.03
        assert vattium.importe_inventario_propio == 7510.06  # 3755.03 * 2

        av9102 = next(i for i in saved_items if i.codigo_material == "AV9102")
        assert av9102.costo_promedio_unitario == 140.0
        assert av9102.valor_consignacion_proveedor == 700.0  # 140.0 * 5


@pytest.mark.asyncio
async def test_list_inventario_auto_heals_zero_prices():
    from app.api.v1.inventario_abcf import list_inventario

    # Item with missing price in DB
    unpriced_item = InventarioAbcf(
        id=1,
        nombre_centro="MKS CASA KURODA",
        almacen="MA01",
        codigo_material="VATTIUM10-220",
        descripcion_material="CALENTADOR VATTIUM",
        cantidad_propia=3.0,
        existencia_consignacion=0.0,
        costo_promedio_unitario=None,
        importe_inventario_propio=None
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [unpriced_item]
    mock_db.execute.return_value = mock_result

    with patch("app.api.v1.inventario_abcf.get_reference_pricing_catalog", new=AsyncMock(return_value={
        "VATTIUM10-220": 3755.03
    })):
        res = await list_inventario(db=mock_db)

        assert res["status"] == "success"
        assert len(res["data"]) == 1
        data = res["data"][0]
        assert data["costo_promedio_unitario"] == 3755.03
        assert data["importe_inventario_propio"] == 11265.09

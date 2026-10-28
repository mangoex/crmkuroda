"""Módulo de endpoints de SOLO LECTURA (/api/v1/bot) para consulta de bot externo."""

from __future__ import annotations

from calendar import monthrange
from collections import deque
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import os
import re
import secrets
import time as time_module
from typing import Any, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import and_, case, func, literal, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_bot_db
from app.models.cliente import Cliente
from app.models.cotizacion import Cotizacion
from app.models.cotizacion_detalle import CotizacionComentario, CotizacionItem
from app.models.meta import Meta
from app.models.meta_comercial import MetaComercial
from app.models.recordatorio_seguimiento import RecordatorioSeguimiento
from app.models.usuario import Usuario
from app.schemas.bot import (
    BotAvanceEquipoSummary,
    BotAvanceResponse,
    BotAvanceVendedorItem,
    BotCitaItem,
    BotCitaListResponse,
    BotClienteItem,
    BotClienteListResponse,
    BotCompromisoItem,
    BotCompromisoListResponse,
    BotCotizacionDetailResponse,
    BotCotizacionItem,
    BotCotizacionListResponse,
    BotErrorResponse,
    BotHealthResponse,
    BotMetaItem,
    BotMetaListResponse,
    BotNotaItem,
    BotPartidaItem,
    BotVendedorDetailResponse,
    BotVendedorItem,
    BotVendedorListResponse,
    BotVendedorResumenMes,
    BotVentaDetailResponse,
    BotVentaItem,
    BotVentaListResponse,
)

MAZATLAN_TZ = ZoneInfo("America/Mazatlan")
PERIODO_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
VALID_COTIZACION_ESTATUS = {"borrador", "enviada", "aceptada", "rechazada", "vencida"}
VALID_META_TIPOS = {"mensual", "trimestral", "anual"}
VALID_COMPROMISO_ESTATUS = {"pendiente", "cumplido", "vencido"}

# Rate limiter en memoria por clave (ventana deslizante de 60 segundos)
_RATE_LIMIT_BUCKETS: dict[str, deque[float]] = {}


def reset_bot_rate_limiter() -> None:
    """Limpia los contadores de rate limit (útil para pruebas automatizadas)."""
    _RATE_LIMIT_BUCKETS.clear()


def _get_configured_bot_api_key() -> str:
    return (os.getenv("BOT_API_KEY") or settings.BOT_API_KEY or "").strip()


async def verify_bot_api_key_and_rate_limit(
    request: Request,
    x_api_key: Optional[str] = Header(
        default=None,
        alias="X-API-Key",
        description="Clave secreta de autenticación del bot (comparada en tiempo constante).",
    ),
) -> str:
    """Valida encabezado X-API-Key con secrets.compare_digest y aplica límite de peticiones."""
    if request.method != "GET":
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Método no permitido. Este módulo es exclusivamente de solo lectura (GET).",
            headers={"Allow": "GET"},
        )

    expected_key = _get_configured_bot_api_key()
    if not expected_key or not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Encabezado X-API-Key obligatorio o no válido.",
        )

    provided_bytes = x_api_key.encode("utf-8")
    expected_bytes = expected_key.encode("utf-8")
    if not secrets.compare_digest(provided_bytes, expected_bytes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave X-API-Key inválida.",
        )

    # Rate limit por clave (por defecto 60 peticiones / minuto)
    max_requests = int(os.getenv("BOT_RATE_LIMIT_PER_MINUTE") or settings.BOT_RATE_LIMIT_PER_MINUTE or 60)
    now_ts = time_module.monotonic()
    window_seconds = 60.0
    bucket = _RATE_LIMIT_BUCKETS.setdefault(x_api_key, deque())
    while bucket and (now_ts - bucket[0]) >= window_seconds:
        bucket.popleft()
    if len(bucket) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Límite de peticiones excedido ({max_requests} por minuto).",
            headers={"Retry-After": "60"},
        )
    bucket.append(now_ts)
    return x_api_key


router = APIRouter(
    dependencies=[Depends(verify_bot_api_key_and_rate_limit)],
    responses={
        400: {"model": BotErrorResponse, "description": "Parámetros de consulta inválidos"},
        401: {"model": BotErrorResponse, "description": "No autorizado (X-API-Key faltante o inválida)"},
        404: {"model": BotErrorResponse, "description": "Recurso no encontrado"},
        405: {"model": BotErrorResponse, "description": "Método no permitido (solo GET)"},
        422: {"model": BotErrorResponse, "description": "Error de validación de parámetros"},
    },
)


def _mazatlan_now() -> datetime:
    return datetime.now(MAZATLAN_TZ)


def _mazatlan_today() -> date:
    return _mazatlan_now().date()


def _parse_date_value(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(MAZATLAN_TZ).date() if value.tzinfo else value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        clean = value.strip()
        if not clean:
            return None
        try:
            return date.fromisoformat(clean[:10])
        except ValueError:
            return None
    return None


def to_mazatlan_iso(value: Any) -> Optional[str]:
    """Convierte date, datetime o cadena ISO a ISO 8601 con zona horaria America/Mazatlan."""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value.astimezone(MAZATLAN_TZ) if value.tzinfo else value.replace(tzinfo=MAZATLAN_TZ)
        return dt.isoformat(timespec="seconds")
    if isinstance(value, date):
        dt = datetime.combine(value, time(0, 0, 0), tzinfo=MAZATLAN_TZ)
        return dt.isoformat(timespec="seconds")
    if isinstance(value, str):
        clean = value.strip()
        if not clean:
            return None
        try:
            if len(clean) == 10:
                d = date.fromisoformat(clean)
                return datetime.combine(d, time(0, 0, 0), tzinfo=MAZATLAN_TZ).isoformat(timespec="seconds")
            parsed_dt = datetime.fromisoformat(clean.replace("Z", "+00:00"))
            dt = parsed_dt.astimezone(MAZATLAN_TZ) if parsed_dt.tzinfo else parsed_dt.replace(tzinfo=MAZATLAN_TZ)
            return dt.isoformat(timespec="seconds")
        except ValueError:
            return clean
    return str(value)


def _to_decimal_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(round(Decimal(str(value)), 2))
    except Exception:
        return 0.0


def _validate_date_range(desde: Optional[date], hasta: Optional[date]) -> None:
    if desde is not None and hasta is not None and desde > hasta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rango de fechas es inválido: 'desde' no puede ser mayor que 'hasta'.",
        )


def _parse_periodo(periodo: Optional[str]) -> tuple[str, date, date]:
    if not periodo:
        today = _mazatlan_today()
        periodo_str = today.strftime("%Y-%m")
    else:
        periodo_str = periodo.strip()
        if not PERIODO_REGEX.match(periodo_str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El parámetro 'periodo' debe tener el formato YYYY-MM.",
            )
    year_s, month_s = periodo_str.split("-")
    year, month = int(year_s), int(month_s)
    start_d = date(year, month, 1)
    end_d = date(year, month, monthrange(year, month)[1])
    return periodo_str, start_d, end_d


def _parse_uuid_or_400(raw_id: Optional[str], field_name: str = "id") -> Optional[UUID]:
    if raw_id is None or raw_id == "":
        return None
    try:
        return UUID(str(raw_id).strip())
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El parámetro '{field_name}' debe ser un UUID válido.",
        )


def _parse_uuid_or_404(raw_id: str, entity_label: str = "Recurso") -> UUID:
    try:
        return UUID(str(raw_id).strip())
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_label} no encontrado.",
        )


def _sql_has_invoice():
    """Condición SQL determinista para identificar una venta facturada/concretada."""
    return or_(
        and_(
            Cotizacion.numero_factura.is_not(None),
            func.length(func.trim(Cotizacion.numero_factura)) > 0,
        ),
        func.coalesce(Cotizacion.importe_facturado, 0) > 0,
    )


def _sql_venta_monto():
    """Expresión SQL para el monto efectivo de una venta."""
    return case(
        (func.coalesce(Cotizacion.importe_facturado, 0) > 0, Cotizacion.importe_facturado),
        else_=func.coalesce(Cotizacion.total, 0),
    )


def _sql_venta_fecha():
    """Expresión SQL para la fecha efectiva de una venta."""
    return func.coalesce(Cotizacion.fecha_factura, Cotizacion.fecha_registro)


def _sql_cotizacion_estatus(today: date):
    """Expresión SQL para el estatus canónico de una cotización: borrador|enviada|aceptada|rechazada|vencida."""
    has_inv = _sql_has_invoice()
    vp = func.upper(func.trim(func.coalesce(Cotizacion.venta_perdida, "")))
    cutoff = today - timedelta(days=settings.QUOTE_VALID_DAYS)
    return case(
        (has_inv, literal("aceptada")),
        (vp.in_(("SI", "SÍ", "RECHAZADA", "PERDIDA")), literal("rechazada")),
        (vp == "BORRADOR", literal("borrador")),
        (
            and_(
                Cotizacion.fecha_registro.is_not(None),
                Cotizacion.fecha_registro < cutoff,
            ),
            literal("vencida"),
        ),
        else_=literal("enviada"),
    )


def _serialize_vendedor(u: Usuario) -> BotVendedorItem:
    activo_val = getattr(u, "activo", True)
    if activo_val is None:
        activo_val = True
    fecha_alta_raw = getattr(u, "fecha_alta", None) or date(2026, 1, 1)
    equipo_val = getattr(u, "equipo", None) or getattr(u, "codigo_vendedor", None) or "General"
    return BotVendedorItem(
        id=str(u.id),
        nombre=u.nombre_completo or u.email,
        email=u.email,
        telefono=u.telefono_whatsapp,
        equipo=equipo_val,
        activo=bool(activo_val),
        fecha_alta=to_mazatlan_iso(fecha_alta_raw) or to_mazatlan_iso(date(2026, 1, 1)),
    )


def _build_partidas(
    quote: Cotizacion,
    detail_items: list[CotizacionItem],
    *,
    for_sale: bool = False,
) -> list[BotPartidaItem]:
    partidas: list[BotPartidaItem] = []
    if detail_items:
        for item in detail_items:
            if for_sale and float(item.cantidad_facturada or 0) > 0:
                cantidad = _to_decimal_float(item.cantidad_facturada)
                importe = _to_decimal_float(item.importe_facturado)
            else:
                cantidad = _to_decimal_float(item.cantidad_cotizada or 1)
                importe = _to_decimal_float(item.importe_cotizado or item.importe_facturado)
            precio_unit = _to_decimal_float(item.precio_venta)
            if precio_unit <= 0 and cantidad > 0 and importe > 0:
                precio_unit = _to_decimal_float(importe / cantidad)
            if importe <= 0 and cantidad > 0 and precio_unit > 0:
                importe = _to_decimal_float(cantidad * precio_unit)
            nombre_prod = (item.descripcion or item.codigo_material or "Producto").strip()
            partidas.append(
                BotPartidaItem(
                    producto=nombre_prod,
                    codigo_material=item.codigo_material,
                    cantidad=cantidad,
                    precio_unitario=precio_unit,
                    importe=importe,
                    moneda="MXN",
                )
            )
        return partidas

    raw_items = getattr(quote, "items", None)
    if isinstance(raw_items, list):
        for raw in raw_items:
            if not isinstance(raw, dict):
                continue
            prod = str(
                raw.get("producto")
                or raw.get("descripcion")
                or raw.get("codigo_material")
                or "Producto"
            ).strip()
            codigo = raw.get("codigo_material") or raw.get("sku")
            cantidad = _to_decimal_float(raw.get("cantidad") or raw.get("cantidad_cotizada") or 1)
            precio = _to_decimal_float(
                raw.get("precio_unitario") or raw.get("precio_venta") or raw.get("precio") or 0
            )
            importe = _to_decimal_float(raw.get("importe") or raw.get("total") or (cantidad * precio))
            if precio <= 0 and cantidad > 0 and importe > 0:
                precio = _to_decimal_float(importe / cantidad)
            partidas.append(
                BotPartidaItem(
                    producto=prod,
                    codigo_material=str(codigo) if codigo else None,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    importe=importe,
                    moneda="MXN",
                )
            )

    if not partidas:
        fallback_monto = (
            _to_decimal_float(quote.importe_facturado or quote.total)
            if for_sale
            else _to_decimal_float(quote.total)
        )
        mat_desc = (
            (quote.materiales_facturados if for_sale else quote.materiales_cotizados)
            or quote.materiales_cotizados
            or "Partida general"
        )
        partidas.append(
            BotPartidaItem(
                producto=str(mat_desc),
                codigo_material=None,
                cantidad=1.0,
                precio_unitario=fallback_monto,
                importe=fallback_monto,
                moneda="MXN",
            )
        )
    return partidas


# ---------------------------------------------------------------------------
# 1. GET /api/v1/bot/health
# ---------------------------------------------------------------------------
@router.get(
    "/health",
    response_model=BotHealthResponse,
    summary="Estado de salud del módulo Bot",
    description="Verifica disponibilidad del módulo de solo lectura y devuelve versión y hora del servidor en America/Mazatlan.",
)
async def bot_health() -> BotHealthResponse:
    return BotHealthResponse(
        status="ok",
        version="1.0.0",
        hora_servidor=_mazatlan_now().isoformat(timespec="seconds"),
    )


# ---------------------------------------------------------------------------
# 2. GET /api/v1/bot/vendedores
# ---------------------------------------------------------------------------
@router.get(
    "/vendedores",
    response_model=BotVendedorListResponse,
    summary="Listar vendedores comerciales",
    description="Consulta paginada de vendedores con filtro por estado activo.",
)
async def bot_list_vendedores(
    activo: Optional[bool] = Query(default=None, description="Filtrar por estado activo (true/false)."),
    limit: int = Query(default=100, ge=1, le=500, description="Límite de registros (máx. 500)."),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginación."),
    db: AsyncSession = Depends(get_bot_db),
) -> BotVendedorListResponse:
    conditions = [Usuario.rol == "vendedor"]
    if activo is not None:
        if activo:
            conditions.append(or_(Usuario.activo.is_(True), Usuario.activo.is_(None)))
        else:
            conditions.append(Usuario.activo.is_(False))

    total_stmt = select(func.count(Usuario.id)).where(*conditions)
    total = int((await db.execute(total_stmt)).scalar() or 0)

    stmt = (
        select(Usuario)
        .where(*conditions)
        .order_by(Usuario.nombre_completo.asc(), Usuario.email.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return BotVendedorListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[_serialize_vendedor(u) for u in rows],
    )


# ---------------------------------------------------------------------------
# 3. GET /api/v1/bot/vendedores/{id}
# ---------------------------------------------------------------------------
@router.get(
    "/vendedores/{vendedor_id}",
    response_model=BotVendedorDetailResponse,
    summary="Detalle de vendedor y resumen del mes actual",
    description=(
        "Devuelve la ficha del vendedor junto con el resumen calculado en SQL del mes en curso: "
        "ventas_total, num_ventas, num_cotizaciones, meta_mes y avance_pct."
    ),
)
async def bot_get_vendedor_detail(
    vendedor_id: str,
    db: AsyncSession = Depends(get_bot_db),
) -> BotVendedorDetailResponse:
    vid = _parse_uuid_or_404(vendedor_id, "Vendedor")
    seller = (
        await db.execute(
            select(Usuario).where(Usuario.id == vid, Usuario.rol == "vendedor")
        )
    ).scalars().first()
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendedor no encontrado.",
        )

    periodo_str, start_d, end_d = _parse_periodo(None)
    has_inv = _sql_has_invoice()
    venta_monto = _sql_venta_monto()
    venta_fecha = _sql_venta_fecha()

    sale_in_month = and_(
        has_inv,
        venta_fecha >= start_d,
        venta_fecha <= end_d,
    )
    quote_in_month = and_(
        Cotizacion.fecha_registro >= start_d,
        Cotizacion.fecha_registro <= end_d,
    )

    metrics_stmt = select(
        func.coalesce(func.sum(case((sale_in_month, venta_monto), else_=0)), 0).label("ventas_total"),
        func.coalesce(func.sum(case((sale_in_month, 1), else_=0)), 0).label("num_ventas"),
        func.coalesce(func.sum(case((quote_in_month, 1), else_=0)), 0).label("num_cotizaciones"),
    ).where(Cotizacion.vendedor_id == vid)
    m_row = (await db.execute(metrics_stmt)).mappings().one()

    mc_stmt = select(func.coalesce(func.sum(MetaComercial.monto_objetivo), 0)).where(
        MetaComercial.tipo == "vendedor",
        MetaComercial.vendedor_id == vid,
        MetaComercial.mes == start_d,
    )
    meta_mc = _to_decimal_float((await db.execute(mc_stmt)).scalar() or 0)

    if meta_mc > 0:
        meta_mes = meta_mc
    else:
        ml_stmt = select(func.coalesce(func.sum(Meta.monto_objetivo), 0)).where(
            Meta.vendedor_id == vid,
            Meta.fecha_inicio <= end_d,
            Meta.fecha_limite >= start_d,
        )
        meta_mes = _to_decimal_float((await db.execute(ml_stmt)).scalar() or 0)

    ventas_total = _to_decimal_float(m_row["ventas_total"])
    num_ventas = int(m_row["num_ventas"] or 0)
    num_cotizaciones = int(m_row["num_cotizaciones"] or 0)
    avance_pct = round((ventas_total / meta_mes) * 100.0, 2) if meta_mes > 0 else 0.0

    base_info = _serialize_vendedor(seller)
    resumen = BotVendedorResumenMes(
        periodo=periodo_str,
        ventas_total=ventas_total,
        num_ventas=num_ventas,
        num_cotizaciones=num_cotizaciones,
        meta_mes=meta_mes,
        avance_pct=avance_pct,
        moneda="MXN",
    )
    return BotVendedorDetailResponse(
        **base_info.model_dump(),
        ventas_total=ventas_total,
        num_ventas=num_ventas,
        num_cotizaciones=num_cotizaciones,
        meta_mes=meta_mes,
        avance_pct=avance_pct,
        moneda="MXN",
        resumen_mes=resumen,
    )


# ---------------------------------------------------------------------------
# 4. GET /api/v1/bot/ventas
# ---------------------------------------------------------------------------
@router.get(
    "/ventas",
    response_model=BotVentaListResponse,
    summary="Listar ventas concretadas/facturadas",
    description="Consulta paginada de ventas con filtros por vendedor, cliente, estatus y rango de fechas.",
)
async def bot_list_ventas(
    vendedor_id: Optional[str] = Query(default=None, description="UUID del vendedor."),
    cliente_id: Optional[str] = Query(default=None, description="ID o número de cliente."),
    estatus: Optional[str] = Query(default=None, description="Estatus de la venta (ej. facturada, pagada)."),
    desde: Optional[date] = Query(default=None, description="Fecha inicial YYYY-MM-DD."),
    hasta: Optional[date] = Query(default=None, description="Fecha final YYYY-MM-DD."),
    limit: int = Query(default=100, ge=1, le=500, description="Límite de registros (máx. 500)."),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginación."),
    db: AsyncSession = Depends(get_bot_db),
) -> BotVentaListResponse:
    _validate_date_range(desde, hasta)
    vid = _parse_uuid_or_400(vendedor_id, "vendedor_id")

    has_inv = _sql_has_invoice()
    venta_fecha = _sql_venta_fecha()
    venta_monto = _sql_venta_monto()

    conditions = [has_inv]
    if vid is not None:
        conditions.append(Cotizacion.vendedor_id == vid)
    if cliente_id and cliente_id.strip():
        cli_clean = cliente_id.strip()
        conditions.append(
            or_(
                Cotizacion.numero_cliente == cli_clean,
                Cotizacion.cliente_nombre.ilike(f"%{cli_clean}%"),
            )
        )
    if estatus and estatus.strip():
        est_norm = estatus.strip().lower()
        if est_norm not in ("facturada", "pagada", "completada", "concretada"):
            # Ninguna venta facturada coincide con un estatus ajeno
            conditions.append(literal(False))
    if desde is not None:
        conditions.append(venta_fecha >= desde)
    if hasta is not None:
        conditions.append(venta_fecha <= hasta)

    total_stmt = select(func.count(Cotizacion.id)).where(*conditions)
    total = int((await db.execute(total_stmt)).scalar() or 0)

    stmt = (
        select(
            Cotizacion.id,
            Cotizacion.numero_factura,
            Cotizacion.numero_cotizacion,
            venta_fecha.label("fecha_efectiva"),
            Cotizacion.vendedor_id,
            func.coalesce(Usuario.nombre_completo, Cotizacion.vendedor_nombre).label("vendedor_nombre_res"),
            Cotizacion.numero_cliente,
            Cotizacion.cliente_nombre,
            venta_monto.label("monto_efectivo"),
            Cotizacion.plazo_entrega,
            Cotizacion.canal,
        )
        .outerjoin(Usuario, Cotizacion.vendedor_id == Usuario.id)
        .where(*conditions)
        .order_by(venta_fecha.desc(), Cotizacion.id.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).mappings().all()

    items: list[BotVentaItem] = []
    for r in rows:
        folio_val = (r["numero_factura"] or "").strip() or (r["numero_cotizacion"] or "").strip() or str(r["id"])[:8]
        forma_pago_val = (r["plazo_entrega"] or "").strip() or (r["canal"] or "").strip() or "Contado / Comercial"
        fecha_iso = to_mazatlan_iso(r["fecha_efectiva"]) or to_mazatlan_iso(_mazatlan_today())
        items.append(
            BotVentaItem(
                id=str(r["id"]),
                folio=folio_val,
                fecha=fecha_iso,
                vendedor_id=str(r["vendedor_id"]) if r["vendedor_id"] else None,
                vendedor_nombre=r["vendedor_nombre_res"],
                cliente_id=r["numero_cliente"],
                cliente_nombre=r["cliente_nombre"] or "Cliente",
                monto=_to_decimal_float(r["monto_efectivo"]),
                moneda="MXN",
                estatus=(estatus.strip().lower() if estatus and estatus.strip() else "facturada"),
                forma_pago=forma_pago_val,
                cotizacion_id=str(r["id"]),
            )
        )

    return BotVentaListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


# ---------------------------------------------------------------------------
# 5. GET /api/v1/bot/ventas/{id}
# ---------------------------------------------------------------------------
@router.get(
    "/ventas/{venta_id}",
    response_model=BotVentaDetailResponse,
    summary="Detalle de venta con partidas",
    description="Devuelve la información completa de una venta y el desglose de sus partidas.",
)
async def bot_get_venta_detail(
    venta_id: str,
    db: AsyncSession = Depends(get_bot_db),
) -> BotVentaDetailResponse:
    vid = _parse_uuid_or_404(venta_id, "Venta")
    has_inv = _sql_has_invoice()
    stmt = (
        select(Cotizacion, Usuario.nombre_completo)
        .outerjoin(Usuario, Cotizacion.vendedor_id == Usuario.id)
        .where(Cotizacion.id == vid, has_inv)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venta no encontrada.",
        )
    quote, seller_full_name = row[0], row[1]
    detail_items = (
        await db.execute(
            select(CotizacionItem).where(CotizacionItem.cotizacion_id == quote.id)
        )
    ).scalars().all()

    folio_val = (quote.numero_factura or "").strip() or (quote.numero_cotizacion or "").strip() or str(quote.id)[:8]
    fecha_val = quote.fecha_factura or quote.fecha_registro or _mazatlan_today()
    monto_val = (
        _to_decimal_float(quote.importe_facturado)
        if _to_decimal_float(quote.importe_facturado) > 0
        else _to_decimal_float(quote.total)
    )
    forma_pago_val = (quote.plazo_entrega or "").strip() or (quote.canal or "").strip() or "Contado / Comercial"

    return BotVentaDetailResponse(
        id=str(quote.id),
        folio=folio_val,
        fecha=to_mazatlan_iso(fecha_val) or to_mazatlan_iso(_mazatlan_today()),
        vendedor_id=str(quote.vendedor_id) if quote.vendedor_id else None,
        vendedor_nombre=seller_full_name or quote.vendedor_nombre,
        cliente_id=quote.numero_cliente,
        cliente_nombre=quote.cliente_nombre or "Cliente",
        monto=monto_val,
        moneda="MXN",
        estatus="facturada",
        forma_pago=forma_pago_val,
        cotizacion_id=str(quote.id),
        partidas=_build_partidas(quote, list(detail_items), for_sale=True),
    )


# ---------------------------------------------------------------------------
# 6. GET /api/v1/bot/metas
# ---------------------------------------------------------------------------
@router.get(
    "/metas",
    response_model=BotMetaListResponse,
    summary="Listar metas comerciales",
    description="Consulta paginada de metas por vendedor, periodo (YYYY-MM) y tipo (mensual|trimestral|anual).",
)
async def bot_list_metas(
    vendedor_id: Optional[str] = Query(default=None, description="UUID del vendedor."),
    periodo: Optional[str] = Query(default=None, description="Periodo en formato YYYY-MM."),
    tipo: Optional[str] = Query(default=None, description="Tipo de meta: mensual, trimestral o anual."),
    limit: int = Query(default=100, ge=1, le=500, description="Límite de registros (máx. 500)."),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginación."),
    db: AsyncSession = Depends(get_bot_db),
) -> BotMetaListResponse:
    vid = _parse_uuid_or_400(vendedor_id, "vendedor_id")
    start_d: Optional[date] = None
    end_d: Optional[date] = None
    periodo_norm: Optional[str] = None
    if periodo:
        periodo_norm, start_d, end_d = _parse_periodo(periodo)

    tipo_norm: Optional[str] = None
    if tipo:
        tipo_norm = tipo.strip().lower()
        if tipo_norm not in VALID_META_TIPOS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El parámetro 'tipo' debe ser mensual, trimestral o anual.",
            )

    # 1) Consultar metas comerciales (tabla metas_comerciales)
    mc_conditions = [MetaComercial.vendedor_id.is_not(None)]
    if vid is not None:
        mc_conditions.append(MetaComercial.vendedor_id == vid)
    if start_d is not None:
        mc_conditions.append(MetaComercial.mes == start_d)

    mc_rows = []
    if tipo_norm in (None, "mensual"):
        mc_stmt = (
            select(MetaComercial, Usuario.nombre_completo, Usuario.email)
            .outerjoin(Usuario, MetaComercial.vendedor_id == Usuario.id)
            .where(*mc_conditions)
            .order_by(MetaComercial.mes.desc())
        )
        mc_rows = (await db.execute(mc_stmt)).all()

    # 2) Consultar metas operativas/legadas (tabla metas)
    ml_conditions = []
    if vid is not None:
        ml_conditions.append(Meta.vendedor_id == vid)
    if start_d is not None and end_d is not None:
        ml_conditions.append(and_(Meta.fecha_inicio <= end_d, Meta.fecha_limite >= start_d))

    ml_stmt = (
        select(Meta, Usuario.nombre_completo, Usuario.email)
        .outerjoin(Usuario, Meta.vendedor_id == Usuario.id)
        .where(*ml_conditions)
        .order_by(Meta.fecha_inicio.desc())
    )
    ml_rows = (await db.execute(ml_stmt)).all()

    combined: list[BotMetaItem] = []
    seen_seller_months: set[tuple[str, str]] = set()

    for mc, u_nombre, u_email in mc_rows:
        per = mc.mes.strftime("%Y-%m")
        sid = str(mc.vendedor_id)
        seen_seller_months.add((sid, per))
        combined.append(
            BotMetaItem(
                id=str(mc.id),
                vendedor_id=sid,
                vendedor_nombre=u_nombre or u_email or "Vendedor",
                periodo=per,
                tipo="mensual",
                meta_monto=_to_decimal_float(mc.monto_objetivo),
                moneda="MXN",
                meta_unidades=None,
            )
        )

    for ml, u_nombre, u_email in ml_rows:
        per =periodo_norm or ml.fecha_inicio.strftime("%Y-%m")
        sid = str(ml.vendedor_id)
        span_days = max(1, (ml.fecha_limite - ml.fecha_inicio).days + 1)
        if span_days <= 35:
            inferred_tipo = "mensual"
        elif span_days <= 120:
            inferred_tipo = "trimestral"
        else:
            inferred_tipo = "anual"

        if tipo_norm and inferred_tipo != tipo_norm:
            continue
        if inferred_tipo == "mensual" and (sid, per) in seen_seller_months:
            continue

        combined.append(
            BotMetaItem(
                id=str(ml.id),
                vendedor_id=sid,
                vendedor_nombre=u_nombre or u_email or "Vendedor",
                periodo=per,
                tipo=inferred_tipo,
                meta_monto=_to_decimal_float(ml.monto_objetivo),
                moneda="MXN",
                meta_unidades=None,
            )
        )

    total = len(combined)
    paginated = combined[offset : offset + limit]
    return BotMetaListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=paginated,
    )


# ---------------------------------------------------------------------------
# 7. GET /api/v1/bot/avance
# ---------------------------------------------------------------------------
@router.get(
    "/avance",
    response_model=BotAvanceResponse,
    summary="Avance de ventas contra meta por vendedor y equipo (calculado en SQL)",
    description=(
        "Calcula íntegramente en el servidor de base de datos (SQL) el avance por vendedor "
        "y el resumen consolidado del equipo para el periodo YYYY-MM."
    ),
)
async def bot_get_avance(
    periodo: Optional[str] = Query(
        default=None,
        description="Periodo en formato YYYY-MM (por defecto el mes actual en America/Mazatlan).",
    ),
    vendedor_id: Optional[str] = Query(default=None, description="Filtrar por UUID de un vendedor específico."),
    limit: int = Query(default=100, ge=1, le=500, description="Límite de registros (máx. 500)."),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginación."),
    db: AsyncSession = Depends(get_bot_db),
) -> BotAvanceResponse:
    periodo_str, start_d, end_d = _parse_periodo(periodo)
    vid = _parse_uuid_or_400(vendedor_id, "vendedor_id")
    today = _mazatlan_today()

    has_inv = _sql_has_invoice()
    venta_monto = _sql_venta_monto()
    venta_fecha = _sql_venta_fecha()
    quote_status = _sql_cotizacion_estatus(today)

    # Subconsulta SQL 1: Metas comerciales del mes por vendedor
    mc_subq = (
        select(
            MetaComercial.vendedor_id.label("vendedor_id"),
            func.coalesce(func.sum(MetaComercial.monto_objetivo), 0).label("meta_mc"),
        )
        .where(
            MetaComercial.tipo == "vendedor",
            MetaComercial.vendedor_id.is_not(None),
            MetaComercial.mes == start_d,
        )
        .group_by(MetaComercial.vendedor_id)
        .subquery("mc_subq")
    )

    # Subconsulta SQL 2: Metas legadas/operativas del mes por vendedor
    ml_subq = (
        select(
            Meta.vendedor_id.label("vendedor_id"),
            func.coalesce(func.sum(Meta.monto_objetivo), 0).label("meta_ml"),
        )
        .where(
            Meta.fecha_inicio <= end_d,
            Meta.fecha_limite >= start_d,
        )
        .group_by(Meta.vendedor_id)
        .subquery("ml_subq")
    )

    # Subconsulta SQL 3: Métricas de ventas y cotizaciones por vendedor
    sale_in_period = and_(
        has_inv,
        venta_fecha >= start_d,
        venta_fecha <= end_d,
    )
    open_quote_in_period = and_(
        quote_status.in_(("enviada", "borrador")),
        Cotizacion.fecha_registro >= start_d,
        Cotizacion.fecha_registro <= end_d,
    )
    q_subq = (
        select(
            Cotizacion.vendedor_id.label("vendedor_id"),
            func.coalesce(func.sum(case((sale_in_period, venta_monto), else_=0)), 0).label("vendido_monto"),
            func.coalesce(func.sum(case((sale_in_period, 1), else_=0)), 0).label("num_ventas"),
            func.coalesce(func.sum(case((open_quote_in_period, 1), else_=0)), 0).label("num_cotizaciones_abiertas"),
            func.max(case((has_inv, venta_fecha), else_=None)).label("ultima_venta_fecha"),
        )
        .where(Cotizacion.vendedor_id.is_not(None))
        .group_by(Cotizacion.vendedor_id)
        .subquery("q_subq")
    )

    meta_expr = case(
        (func.coalesce(mc_subq.c.meta_mc, 0) > 0, mc_subq.c.meta_mc),
        else_=func.coalesce(ml_subq.c.meta_ml, 0),
    )
    vendido_expr = func.coalesce(q_subq.c.vendido_monto, 0)
    avance_pct_expr = case(
        (meta_expr > 0, func.round((vendido_expr * 100.0) / meta_expr, 2)),
        else_=0.0,
    )
    faltante_expr = case(
        (meta_expr > vendido_expr, meta_expr - vendido_expr),
        else_=0.0,
    )

    seller_conditions = [Usuario.rol == "vendedor"]
    if vid is not None:
        seller_conditions.append(Usuario.id == vid)

    avance_base = (
        select(
            Usuario.id.label("vendedor_id"),
            func.coalesce(Usuario.nombre_completo, Usuario.email).label("vendedor_nombre"),
            meta_expr.label("meta_monto"),
            vendido_expr.label("vendido_monto"),
            avance_pct_expr.label("avance_pct"),
            faltante_expr.label("faltante"),
            func.coalesce(q_subq.c.num_ventas, 0).label("num_ventas"),
            func.coalesce(q_subq.c.num_cotizaciones_abiertas, 0).label("num_cotizaciones_abiertas"),
            q_subq.c.ultima_venta_fecha.label("ultima_venta_fecha"),
        )
        .outerjoin(mc_subq, Usuario.id == mc_subq.c.vendedor_id)
        .outerjoin(ml_subq, Usuario.id == ml_subq.c.vendedor_id)
        .outerjoin(q_subq, Usuario.id == q_subq.c.vendedor_id)
        .where(*seller_conditions)
        .subquery("avance_base")
    )

    # Totales de equipo calculados directamente en SQL
    team_meta_sum = func.coalesce(func.sum(avance_base.c.meta_monto), 0)
    team_vendido_sum = func.coalesce(func.sum(avance_base.c.vendido_monto), 0)
    team_avance_pct = case(
        (team_meta_sum > 0, func.round((team_vendido_sum * 100.0) / team_meta_sum, 2)),
        else_=0.0,
    )
    team_faltante = case(
        (team_meta_sum > team_vendido_sum, team_meta_sum - team_vendido_sum),
        else_=0.0,
    )
    team_stmt = select(
        func.count(avance_base.c.vendedor_id).label("total_vendedores"),
        team_meta_sum.label("meta_monto"),
        team_vendido_sum.label("vendido_monto"),
        team_avance_pct.label("avance_pct"),
        team_faltante.label("faltante"),
        func.coalesce(func.sum(avance_base.c.num_ventas), 0).label("num_ventas"),
        func.coalesce(func.sum(avance_base.c.num_cotizaciones_abiertas), 0).label("num_cotizaciones_abiertas"),
        func.max(avance_base.c.ultima_venta_fecha).label("ultima_venta_fecha"),
    )
    team_row = (await db.execute(team_stmt)).mappings().one()
    total_vendedores = int(team_row["total_vendedores"] or 0)

    # Listado paginado por vendedor desde la subconsulta SQL
    items_stmt = (
        select(avance_base)
        .order_by(avance_base.c.vendido_monto.desc(), avance_base.c.vendedor_nombre.asc())
        .limit(limit)
        .offset(offset)
    )
    seller_rows = (await db.execute(items_stmt)).mappings().all()

    items: list[BotAvanceVendedorItem] = []
    for r in seller_rows:
        ult_date = _parse_date_value(r["ultima_venta_fecha"])
        dias_sin = max(0, (today - ult_date).days) if ult_date else None
        items.append(
            BotAvanceVendedorItem(
                vendedor_id=str(r["vendedor_id"]),
                vendedor_nombre=r["vendedor_nombre"] or "Vendedor",
                meta_monto=_to_decimal_float(r["meta_monto"]),
                vendido_monto=_to_decimal_float(r["vendido_monto"]),
                avance_pct=_to_decimal_float(r["avance_pct"]),
                faltante=_to_decimal_float(r["faltante"]),
                num_ventas=int(r["num_ventas"] or 0),
                num_cotizaciones_abiertas=int(r["num_cotizaciones_abiertas"] or 0),
                ultima_venta_fecha=to_mazatlan_iso(ult_date) if ult_date else None,
                dias_sin_venta=dias_sin,
                moneda="MXN",
            )
        )

    team_ult_date = _parse_date_value(team_row["ultima_venta_fecha"])
    team_dias_sin = max(0, (today - team_ult_date).days) if team_ult_date else None
    equipo_summary = BotAvanceEquipoSummary(
        meta_monto=_to_decimal_float(team_row["meta_monto"]),
        vendido_monto=_to_decimal_float(team_row["vendido_monto"]),
        avance_pct=_to_decimal_float(team_row["avance_pct"]),
        faltante=_to_decimal_float(team_row["faltante"]),
        num_ventas=int(team_row["num_ventas"] or 0),
        num_cotizaciones_abiertas=int(team_row["num_cotizaciones_abiertas"] or 0),
        ultima_venta_fecha=to_mazatlan_iso(team_ult_date) if team_ult_date else None,
        dias_sin_venta=team_dias_sin,
        moneda="MXN",
    )

    return BotAvanceResponse(
        periodo=periodo_str,
        moneda="MXN",
        total=total_vendedores,
        limit=limit,
        offset=offset,
        equipo=equipo_summary,
        items=items,
    )


# ---------------------------------------------------------------------------
# 8. GET /api/v1/bot/cotizaciones
# ---------------------------------------------------------------------------
@router.get(
    "/cotizaciones",
    response_model=BotCotizacionListResponse,
    summary="Listar cotizaciones",
    description=(
        "Consulta paginada de cotizaciones con filtros por vendedor, cliente, "
        "estatus (borrador|enviada|aceptada|rechazada|vencida) y rango de fechas."
    ),
)
async def bot_list_cotizaciones(
    vendedor_id: Optional[str] = Query(default=None, description="UUID del vendedor."),
    cliente_id: Optional[str] = Query(default=None, description="ID o número de cliente."),
    estatus: Optional[str] = Query(
        default=None,
        description="Estatus: borrador | enviada | aceptada | rechazada | vencida.",
    ),
    desde: Optional[date] = Query(default=None, description="Fecha inicial YYYY-MM-DD."),
    hasta: Optional[date] = Query(default=None, description="Fecha final YYYY-MM-DD."),
    limit: int = Query(default=100, ge=1, le=500, description="Límite de registros (máx. 500)."),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginación."),
    db: AsyncSession = Depends(get_bot_db),
) -> BotCotizacionListResponse:
    _validate_date_range(desde, hasta)
    vid = _parse_uuid_or_400(vendedor_id, "vendedor_id")
    today = _mazatlan_today()
    status_expr = _sql_cotizacion_estatus(today)

    conditions = []
    if vid is not None:
        conditions.append(Cotizacion.vendedor_id == vid)
    if cliente_id and cliente_id.strip():
        cli_clean = cliente_id.strip()
        conditions.append(
            or_(
                Cotizacion.numero_cliente == cli_clean,
                Cotizacion.cliente_nombre.ilike(f"%{cli_clean}%"),
            )
        )
    if estatus and estatus.strip():
        est_norm = estatus.strip().lower()
        if est_norm not in VALID_COTIZACION_ESTATUS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El parámetro 'estatus' debe ser uno de: borrador, enviada, aceptada, rechazada, vencida.",
            )
        conditions.append(status_expr == est_norm)
    if desde is not None:
        conditions.append(Cotizacion.fecha_registro >= desde)
    if hasta is not None:
        conditions.append(Cotizacion.fecha_registro <= hasta)

    total_stmt = select(func.count(Cotizacion.id)).where(*conditions)
    total = int((await db.execute(total_stmt)).scalar() or 0)

    stmt = (
        select(
            Cotizacion.id,
            Cotizacion.numero_cotizacion,
            Cotizacion.fecha_registro,
            Cotizacion.fecha_factura,
            Cotizacion.vendedor_id,
            func.coalesce(Usuario.nombre_completo, Cotizacion.vendedor_nombre).label("vendedor_nombre_res"),
            Cotizacion.numero_cliente,
            Cotizacion.cliente_nombre,
            Cotizacion.total,
            status_expr.label("estatus_calculado"),
        )
        .outerjoin(Usuario, Cotizacion.vendedor_id == Usuario.id)
        .where(*conditions)
        .order_by(Cotizacion.fecha_registro.desc(), Cotizacion.id.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).mappings().all()

    items: list[BotCotizacionItem] = []
    for r in rows:
        fecha_emision_d = _parse_date_value(r["fecha_registro"]) or today
        fecha_venc_d = fecha_emision_d + timedelta(days=settings.QUOTE_VALID_DAYS)
        fecha_fact_d = _parse_date_value(r["fecha_factura"])
        ult_act = fecha_fact_d if (fecha_fact_d and fecha_fact_d >= fecha_emision_d) else fecha_emision_d
        dias_envio = max(0, (today - fecha_emision_d).days)
        folio_val = (r["numero_cotizacion"] or "").strip() or str(r["id"])[:8]

        items.append(
            BotCotizacionItem(
                id=str(r["id"]),
                folio=folio_val,
                fecha_emision=to_mazatlan_iso(fecha_emision_d),
                fecha_vencimiento=to_mazatlan_iso(fecha_venc_d),
                vendedor_id=str(r["vendedor_id"]) if r["vendedor_id"] else None,
                vendedor_nombre=r["vendedor_nombre_res"],
                cliente_id=r["numero_cliente"],
                cliente_nombre=r["cliente_nombre"] or "Cliente",
                monto=_to_decimal_float(r["total"]),
                moneda="MXN",
                estatus=str(r["estatus_calculado"]),
                dias_desde_envio=dias_envio,
                ultima_actualizacion=to_mazatlan_iso(ult_act),
            )
        )

    return BotCotizacionListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


# ---------------------------------------------------------------------------
# 9. GET /api/v1/bot/cotizaciones/{id}
# ---------------------------------------------------------------------------
@router.get(
    "/cotizaciones/{cotizacion_id}",
    response_model=BotCotizacionDetailResponse,
    summary="Detalle de cotización con partidas y notas",
    description="Devuelve el detalle completo de una cotización incluyendo partidas cotizadas y notas de seguimiento.",
)
async def bot_get_cotizacion_detail(
    cotizacion_id: str,
    db: AsyncSession = Depends(get_bot_db),
) -> BotCotizacionDetailResponse:
    cid = _parse_uuid_or_404(cotizacion_id, "Cotización")
    today = _mazatlan_today()
    status_expr = _sql_cotizacion_estatus(today)

    stmt = (
        select(
            Cotizacion,
            Usuario.nombre_completo,
            status_expr.label("estatus_calculado"),
        )
        .outerjoin(Usuario, Cotizacion.vendedor_id == Usuario.id)
        .where(Cotizacion.id == cid)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada.",
        )

    quote, seller_full_name, estatus_calc = row[0], row[1], row[2]
    detail_items = (
        await db.execute(
            select(CotizacionItem).where(CotizacionItem.cotizacion_id == quote.id)
        )
    ).scalars().all()
    comment_rows = (
        await db.execute(
            select(CotizacionComentario)
            .where(CotizacionComentario.cotizacion_id == quote.id)
            .order_by(CotizacionComentario.creado_en.asc())
        )
    ).scalars().all()

    fecha_emision_d = _parse_date_value(quote.fecha_registro) or today
    fecha_venc_d = fecha_emision_d + timedelta(days=settings.QUOTE_VALID_DAYS)
    ult_act: Any = quote.fecha_factura or fecha_emision_d

    notas: list[BotNotaItem] = []
    if quote.texto_propuesta and quote.texto_propuesta.strip():
        notas.append(
            BotNotaItem(
                id=None,
                tipo="propuesta",
                contenido=quote.texto_propuesta.strip(),
                fecha=to_mazatlan_iso(fecha_emision_d),
            )
        )
    if quote.comentarios and quote.comentarios.strip():
        notas.append(
            BotNotaItem(
                id=None,
                tipo="comentario",
                contenido=quote.comentarios.strip(),
                fecha=to_mazatlan_iso(fecha_emision_d),
            )
        )
    for c in comment_rows:
        if c.creado_en:
            ult_act = c.editado_en or c.creado_en
        notas.append(
            BotNotaItem(
                id=str(c.id),
                tipo="seguimiento",
                contenido=c.comentario,
                fecha=to_mazatlan_iso(c.editado_en or c.creado_en),
            )
        )

    folio_val = (quote.numero_cotizacion or "").strip() or str(quote.id)[:8]
    dias_envio = max(0, (today - fecha_emision_d).days)

    return BotCotizacionDetailResponse(
        id=str(quote.id),
        folio=folio_val,
        fecha_emision=to_mazatlan_iso(fecha_emision_d),
        fecha_vencimiento=to_mazatlan_iso(fecha_venc_d),
        vendedor_id=str(quote.vendedor_id) if quote.vendedor_id else None,
        vendedor_nombre=seller_full_name or quote.vendedor_nombre,
        cliente_id=quote.numero_cliente,
        cliente_nombre=quote.cliente_nombre or "Cliente",
        monto=_to_decimal_float(quote.total),
        moneda="MXN",
        estatus=str(estatus_calc),
        dias_desde_envio=dias_envio,
        ultima_actualizacion=to_mazatlan_iso(ult_act),
        partidas=_build_partidas(quote, list(detail_items), for_sale=False),
        notas=notas,
    )


# ---------------------------------------------------------------------------
# 10. GET /api/v1/bot/clientes
# ---------------------------------------------------------------------------
@router.get(
    "/clientes",
    response_model=BotClienteListResponse,
    summary="Listar clientes del catálogo",
    description="Consulta paginada de clientes con búsqueda por nombre (?q=) y filtro por vendedor (?vendedor_id=).",
)
async def bot_list_clientes(
    vendedor_id: Optional[str] = Query(default=None, description="UUID del vendedor asociado."),
    q: Optional[str] = Query(default=None, description="Búsqueda por nombre o razón social."),
    limit: int = Query(default=100, ge=1, le=500, description="Límite de registros (máx. 500)."),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginación."),
    db: AsyncSession = Depends(get_bot_db),
) -> BotClienteListResponse:
    vid = _parse_uuid_or_400(vendedor_id, "vendedor_id")

    # Subconsulta SQL que vincula número_cliente -> vendedor_id desde cotizaciones
    cli_seller_subq = (
        select(
            Cotizacion.numero_cliente.label("numero_cliente"),
            func.max(func.cast(Cotizacion.vendedor_id, Cliente.sociedad.type)).label("vendedor_id_str"),
        )
        .where(
            Cotizacion.numero_cliente.is_not(None),
            Cotizacion.vendedor_id.is_not(None),
        )
        .group_by(Cotizacion.numero_cliente)
        .subquery("cli_seller_subq")
    )

    conditions = []
    if q and q.strip():
        term = f"%{q.strip()}%"
        conditions.append(
            or_(
                Cliente.nombre.ilike(term),
                Cliente.nombre_contacto.ilike(term),
                Cliente.numero_cliente.ilike(term),
            )
        )
    if vid is not None:
        seller_cli_subq = (
            select(Cotizacion.numero_cliente)
            .where(
                Cotizacion.vendedor_id == vid,
                Cotizacion.numero_cliente.is_not(None),
            )
            .distinct()
        )
        conditions.append(Cliente.numero_cliente.in_(seller_cli_subq))

    total_stmt = select(func.count(Cliente.id)).where(*conditions)
    total = int((await db.execute(total_stmt)).scalar() or 0)

    stmt = (
        select(Cliente, cli_seller_subq.c.vendedor_id_str)
        .outerjoin(cli_seller_subq, Cliente.numero_cliente == cli_seller_subq.c.numero_cliente)
        .where(*conditions)
        .order_by(Cliente.id.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).all()

    items: list[BotClienteItem] = []
    for cl, resolved_vid_str in rows:
        effective_vid = str(vid) if vid is not None else resolved_vid_str
        empresa_val = cl.nombre if (cl.tipo_persona and "moral" in cl.tipo_persona.lower()) else (cl.sociedad or cl.nombre)
        tel_val = (cl.celular or "").strip() or (cl.telefono or "").strip() or None
        items.append(
            BotClienteItem(
                id=str(cl.numero_cliente or cl.id),
                nombre=cl.nombre,
                empresa=empresa_val,
                telefono=tel_val,
                email=(cl.email or "").strip() or None,
                vendedor_id=effective_vid,
                fecha_alta=to_mazatlan_iso(cl.created_at or date(2026, 1, 1)),
            )
        )

    return BotClienteListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


# ---------------------------------------------------------------------------
# 11. GET /api/v1/bot/citas & GET /api/v1/bot/compromisos
# ---------------------------------------------------------------------------
@router.get(
    "/citas",
    response_model=BotCitaListResponse,
    summary="Listar citas y seguimientos programados",
    description="Consulta paginada de citas/seguimientos programados con filtros por vendedor, fechas y estatus.",
)
async def bot_list_citas(
    vendedor_id: Optional[str] = Query(default=None, description="UUID del vendedor."),
    desde: Optional[date] = Query(default=None, description="Fecha inicial YYYY-MM-DD."),
    hasta: Optional[date] = Query(default=None, description="Fecha final YYYY-MM-DD."),
    estatus: Optional[str] = Query(default=None, description="Estatus: pendiente | cumplida | vencida."),
    limit: int = Query(default=100, ge=1, le=500, description="Límite de registros (máx. 500)."),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginación."),
    db: AsyncSession = Depends(get_bot_db),
) -> BotCitaListResponse:
    _validate_date_range(desde, hasta)
    vid = _parse_uuid_or_400(vendedor_id, "vendedor_id")
    today = _mazatlan_today()

    cita_status_expr = case(
        (RecordatorioSeguimiento.completado.is_(True), literal("cumplido")),
        (RecordatorioSeguimiento.fecha_programada < today, literal("vencido")),
        else_=literal("pendiente"),
    )

    conditions = []
    if vid is not None:
        conditions.append(RecordatorioSeguimiento.vendedor_id == vid)
    if desde is not None:
        conditions.append(RecordatorioSeguimiento.fecha_programada >= desde)
    if hasta is not None:
        conditions.append(RecordatorioSeguimiento.fecha_programada <= hasta)
    if estatus and estatus.strip():
        est_norm = estatus.strip().lower()
        if est_norm == "cumplida":
            est_norm = "cumplido"
        elif est_norm == "vencida":
            est_norm = "vencido"
        conditions.append(cita_status_expr == est_norm)

    total_stmt = select(func.count(RecordatorioSeguimiento.id)).where(*conditions)
    total = int((await db.execute(total_stmt)).scalar() or 0)

    stmt = (
        select(
            RecordatorioSeguimiento,
            Cotizacion.numero_cliente,
            Cotizacion.cliente_nombre,
            cita_status_expr.label("estatus_calc"),
        )
        .outerjoin(Cotizacion, RecordatorioSeguimiento.cotizacion_id == Cotizacion.id)
        .where(*conditions)
        .order_by(RecordatorioSeguimiento.fecha_programada.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).all()

    items: list[BotCitaItem] = []
    for rec, num_cli, nom_cli, est_calc in rows:
        items.append(
            BotCitaItem(
                id=str(rec.id),
                fecha_hora=to_mazatlan_iso(rec.fecha_programada) or to_mazatlan_iso(today),
                vendedor_id=str(rec.vendedor_id),
                cliente_id=num_cli or nom_cli,
                tipo="seguimiento_comercial",
                estatus=str(est_calc),
                notas=rec.nota,
            )
        )

    return BotCitaListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get(
    "/compromisos",
    response_model=BotCompromisoListResponse,
    summary="Listar compromisos de seguimiento comercial",
    description="Consulta paginada de compromisos con filtro por vendedor y estatus (pendiente|cumplido|vencido).",
)
async def bot_list_compromisos(
    vendedor_id: Optional[str] = Query(default=None, description="UUID del vendedor."),
    estatus: Optional[str] = Query(default=None, description="Estatus: pendiente | cumplido | vencido."),
    limit: int = Query(default=100, ge=1, le=500, description="Límite de registros (máx. 500)."),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginación."),
    db: AsyncSession = Depends(get_bot_db),
) -> BotCompromisoListResponse:
    vid = _parse_uuid_or_400(vendedor_id, "vendedor_id")
    today = _mazatlan_today()

    comp_status_expr = case(
        (RecordatorioSeguimiento.completado.is_(True), literal("cumplido")),
        (RecordatorioSeguimiento.fecha_programada < today, literal("vencido")),
        else_=literal("pendiente"),
    )

    conditions = []
    if vid is not None:
        conditions.append(RecordatorioSeguimiento.vendedor_id == vid)
    if estatus and estatus.strip():
        est_norm = estatus.strip().lower()
        if est_norm not in VALID_COMPROMISO_ESTATUS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El parámetro 'estatus' debe ser pendiente, cumplido o vencido.",
            )
        conditions.append(comp_status_expr == est_norm)

    total_stmt = select(func.count(RecordatorioSeguimiento.id)).where(*conditions)
    total = int((await db.execute(total_stmt)).scalar() or 0)

    stmt = (
        select(
            RecordatorioSeguimiento,
            Cotizacion.numero_cliente,
            Cotizacion.cliente_nombre,
            comp_status_expr.label("estatus_calc"),
        )
        .outerjoin(Cotizacion, RecordatorioSeguimiento.cotizacion_id == Cotizacion.id)
        .where(*conditions)
        .order_by(RecordatorioSeguimiento.fecha_programada.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).all()

    items: list[BotCompromisoItem] = []
    for rec, num_cli, nom_cli, est_calc in rows:
        items.append(
            BotCompromisoItem(
                id=str(rec.id),
                descripcion=rec.nota or "Seguimiento de cotización",
                vendedor_id=str(rec.vendedor_id),
                cliente_id=num_cli or nom_cli,
                fecha_compromiso=to_mazatlan_iso(rec.fecha_programada) or to_mazatlan_iso(today),
                estatus=str(est_calc),
                fecha_cumplimiento=to_mazatlan_iso(rec.completado_en) if rec.completado_en else None,
            )
        )

    return BotCompromisoListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )

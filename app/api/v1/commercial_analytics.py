from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.cotizacion import Cotizacion
from app.models.cotizacion_detalle import CanalVenta, CotizacionItem
from app.models.meta import Meta
from app.models.slight_edge_log import SlightEdgeLog
from app.models.usuario import Usuario
from app.schemas.commercial import CanalVentaUpsert
from app.services.commercial_analytics import (
    CANONICAL_CHANNELS,
    aggregate_channels,
    aggregate_material_items,
    build_seller_performance,
    normalize_text,
)
from app.services.jerarquia import get_ids_vendedores_visibles


router = APIRouter()


def _require_analytics_role(current_user: Usuario) -> None:
    if current_user.rol not in ("admin", "gerente", "vendedor"):
        raise HTTPException(
            status_code=403,
            detail="Tu rol no tiene acceso a la analítica comercial.",
        )


def _date_filters(query, start: Optional[date], end: Optional[date]):
    if start is not None:
        query = query.where(Cotizacion.fecha_registro >= start)
    if end is not None:
        query = query.where(Cotizacion.fecha_registro <= end)
    return query


async def _seller_condition(
    db: AsyncSession,
    seller_ids: list[UUID],
):
    users = (
        await db.execute(select(Usuario).where(Usuario.id.in_(seller_ids)))
    ).scalars().all()
    names = [
        user.nombre_completo.strip().upper()
        for user in users
        if user.nombre_completo and user.nombre_completo.strip()
    ]
    conditions = [Cotizacion.vendedor_id.in_(seller_ids)]
    if names:
        conditions.append(
            and_(
                Cotizacion.vendedor_id.is_(None),
                func.upper(func.trim(Cotizacion.vendedor_nombre)).in_(names),
            )
        )
    return or_(*conditions)


async def _scope_quotes(
    db: AsyncSession,
    current_user: Usuario,
    start: Optional[date],
    end: Optional[date],
    seller_id: Optional[UUID],
    unlinked: bool = False,
):
    if unlinked and seller_id is not None:
        raise HTTPException(
            status_code=400,
            detail="No combines un asesor específico con el filtro sin vincular.",
        )
    if unlinked and current_user.rol == "vendedor":
        raise HTTPException(
            status_code=403,
            detail="Solo gerencia puede consultar registros sin vincular.",
        )
    query = _date_filters(select(Cotizacion), start, end)
    visible_ids = await get_ids_vendedores_visibles(db, current_user)
    if visible_ids is not None:
        if seller_id is not None and seller_id not in visible_ids:
            raise HTTPException(status_code=403, detail="No tienes permiso para consultar ese asesor.")
        query = query.where(
            await _seller_condition(
                db,
                [seller_id] if seller_id is not None else visible_ids,
            )
        )
    elif seller_id is not None:
        query = query.where(await _seller_condition(db, [seller_id]))
    quotes = (await db.execute(query)).scalars().all()
    if not unlinked:
        return quotes
    users = (await db.execute(select(Usuario))).scalars().all()
    linked_names = {
        normalize_text(user.nombre_completo)
        for user in users
        if user.nombre_completo
    }
    return [
        quote
        for quote in quotes
        if quote.vendedor_id is None
        and normalize_text(quote.vendedor_nombre) not in linked_names
    ]


async def _channel_map(db: AsyncSession) -> dict[str, str]:
    rows = (
        await db.execute(select(CanalVenta).where(CanalVenta.activo.is_(True)))
    ).scalars().all()
    return {row.codigo_origen: row.nombre_normalizado for row in rows}


@router.get("/canales")
async def list_channel_mappings(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol not in ("admin", "gerente"):
        raise HTTPException(status_code=403, detail="No tienes permiso para configurar canales.")
    rows = (await db.execute(select(CanalVenta).order_by(CanalVenta.codigo_origen))).scalars().all()
    return {
        "status": "success",
        "canales_permitidos": list(CANONICAL_CHANNELS),
        "data": [
            {
                "id": row.id,
                "codigo_origen": row.codigo_origen,
                "nombre_normalizado": row.nombre_normalizado,
                "activo": row.activo,
            }
            for row in rows
        ],
    }


@router.put("/canales")
async def upsert_channel_mappings(
    payload: list[CanalVentaUpsert],
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol not in ("admin", "gerente"):
        raise HTTPException(status_code=403, detail="No tienes permiso para configurar canales.")
    allowed = set(CANONICAL_CHANNELS)
    for item in payload:
        if item.nombre_normalizado not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Canal no permitido: {item.nombre_normalizado}.",
            )
        code = item.codigo_origen.strip()
        existing = (
            await db.execute(
                select(CanalVenta).where(CanalVenta.codigo_origen == code)
            )
        ).scalars().first()
        if existing:
            existing.nombre_normalizado = item.nombre_normalizado
            existing.activo = item.activo
        else:
            db.add(
                CanalVenta(
                    codigo_origen=code,
                    nombre_normalizado=item.nombre_normalizado,
                    activo=item.activo,
                )
            )
    await db.commit()
    return {"status": "success", "message": "Catálogo de canales actualizado."}


@router.get("/ventas-por-canal")
async def sales_by_channel(
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    vendedor_id: Optional[UUID] = Query(default=None),
    sin_vincular: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    _require_analytics_role(current_user)
    quotes = await _scope_quotes(
        db, current_user, fecha_inicio, fecha_fin, vendedor_id, sin_vincular
    )
    data = aggregate_channels(quotes, await _channel_map(db))
    return {
        "status": "success",
        "filters": {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "vendedor_id": vendedor_id,
            "sin_vincular": sin_vincular,
        },
        "totals": {
            "importe_cotizado": round(sum(row["importe_cotizado"] for row in data), 2),
            "importe_facturado": round(sum(row["importe_facturado"] for row in data), 2),
            "cotizaciones": sum(row["cotizaciones"] for row in data),
            "operaciones_facturadas": sum(row["operaciones_facturadas"] for row in data),
        },
        "data": data,
    }


@router.get("/ventas-por-material")
async def sales_by_material(
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    vendedor_id: Optional[UUID] = Query(default=None),
    sin_vincular: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    _require_analytics_role(current_user)
    quotes = await _scope_quotes(
        db,
        current_user,
        fecha_inicio,
        fecha_fin,
        vendedor_id,
        sin_vincular,
    )
    quote_ids = [quote.id for quote in quotes]
    if not quote_ids:
        return {"status": "success", "totals": {}, "data": []}
    
    rows = []
    chunk_size = 500
    for i in range(0, len(quote_ids), chunk_size):
        chunk = quote_ids[i:i + chunk_size]
        chunk_rows = (
            await db.execute(
                select(CotizacionItem, Cotizacion)
                .join(Cotizacion, Cotizacion.id == CotizacionItem.cotizacion_id)
                .where(CotizacionItem.cotizacion_id.in_(chunk))
            )
        ).all()
        rows.extend(chunk_rows)
    users = (await db.execute(select(Usuario))).scalars().all()
    seller_names = {
        str(user.id): user.nombre_completo or user.email
        for user in users
    }
    data = aggregate_material_items(rows, seller_names)
    return {
        "status": "success",
        "totals": {
            "cantidad_cotizada": round(sum(row["cantidad_cotizada"] for row in data), 3),
            "importe_cotizado": round(sum(row["importe_cotizado"] for row in data), 2),
            "cantidad_facturada": round(sum(row["cantidad_facturada"] for row in data), 3),
            "importe_facturado": round(sum(row["importe_facturado"] for row in data), 2),
        },
        "data": data,
    }


@router.get("/rendimiento-asesores")
async def seller_performance(
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol not in ("admin", "gerente"):
        raise HTTPException(status_code=403, detail="Solo gerencia puede consultar el rendimiento del equipo.")

    try:
        today = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE)).date()
    except Exception:
        today = date.today()
    start = fecha_inicio or today.replace(day=1)
    end = fecha_fin or today
    if end < start:
        raise HTTPException(status_code=400, detail="La fecha final no puede ser anterior a la inicial.")

    sellers = (
        await db.execute(
            select(Usuario).where(Usuario.rol == "vendedor").order_by(Usuario.nombre_completo)
        )
    ).scalars().all()
    quotes = (
        await db.execute(
            select(Cotizacion).where(
                Cotizacion.fecha_registro >= start,
                Cotizacion.fecha_registro <= end,
            )
        )
    ).scalars().all()
    goals = (
        await db.execute(
            select(Meta).where(
                Meta.fecha_inicio <= end,
                Meta.fecha_limite >= start,
            )
        )
    ).scalars().all()
    logs = (
        await db.execute(
            select(SlightEdgeLog).where(
                SlightEdgeLog.date >= start,
                SlightEdgeLog.date <= end,
            )
        )
    ).scalars().all()

    data = build_seller_performance(
        sellers,
        quotes,
        goals,
        logs,
        today,
        settings.QUOTE_VALID_DAYS,
    )
    return {
        "status": "success",
        "filters": {"fecha_inicio": start, "fecha_fin": end},
        "data": data,
    }

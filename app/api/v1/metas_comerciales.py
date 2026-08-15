from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from app.core.database import get_db
from app.core.config import settings
from app.core.security import RoleChecker, get_current_user
from app.models.cotizacion import Cotizacion
from app.models.meta import Meta
from app.models.meta_comercial import MetaComercial
from app.models.usuario import Usuario
from app.schemas.meta_comercial import (
    MetaComercialCreate,
    MetaComercialUpdate,
)
from app.services.commercial_goals import (
    VALID_PERIODS,
    build_goals_dashboard,
    month_starts_between,
    period_bounds,
)
from zoneinfo import ZoneInfo


router = APIRouter()
require_admin_or_gerente = RoleChecker(["admin", "gerente"])


def _normalize_month(value: date) -> date:
    return value.replace(day=1)


def _business_today() -> date:
    try:
        return datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE)).date()
    except Exception:
        return date.today()


def _serialize(meta: MetaComercial) -> dict:
    return {
        "id": str(meta.id),
        "tipo": meta.tipo,
        "vendedor_id": str(meta.vendedor_id) if meta.vendedor_id else None,
        "sucursal": meta.sucursal,
        "mes": meta.mes.isoformat(),
        "monto_objetivo": float(meta.monto_objetivo),
        "descripcion": meta.descripcion,
        "creado_por_id": str(meta.creado_por_id) if meta.creado_por_id else None,
        "creado_en": meta.creado_en.isoformat() if meta.creado_en else None,
        "actualizado_en": meta.actualizado_en.isoformat() if meta.actualizado_en else None,
    }


async def _load_dashboard_data(db: AsyncSession, reference: date, periodo: str) -> dict:
    start, end = period_bounds(reference, periodo)
    months = month_starts_between(start, end)
    sellers = (
        await db.execute(
            select(Usuario).where(Usuario.rol == "vendedor").order_by(Usuario.nombre_completo)
        )
    ).scalars().all()
    quotes = (
        await db.execute(
            select(Cotizacion)
            .options(
                load_only(
                    Cotizacion.vendedor_id,
                    Cotizacion.vendedor_nombre,
                    Cotizacion.organizacion_ventas,
                    Cotizacion.numero_factura,
                    Cotizacion.importe_facturado,
                    Cotizacion.fecha_registro,
                    Cotizacion.fecha_factura,
                )
            )
            .where(Cotizacion.fecha_registro >= start, Cotizacion.fecha_registro <= end)
        )
    ).scalars().all()
    commercial_goals = (
        await db.execute(select(MetaComercial).where(MetaComercial.mes.in_(months)))
    ).scalars().all()
    legacy_goals = (
        await db.execute(
            select(Meta).where(Meta.fecha_inicio <= end, Meta.fecha_limite >= start)
        )
    ).scalars().all()
    return build_goals_dashboard(
        sellers,
        quotes,
        commercial_goals,
        legacy_goals,
        reference,
        periodo,
    )


@router.get("/comerciales")
async def list_commercial_goals(
    mes: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente),
):
    """Lista las metas configurables del mes presente o futuro seleccionado."""
    selected_month = _normalize_month(mes or _business_today())
    rows = (
        await db.execute(
            select(MetaComercial)
            .where(MetaComercial.mes == selected_month)
            .order_by(MetaComercial.tipo, MetaComercial.sucursal, MetaComercial.creado_en)
        )
    ).scalars().all()
    return {
        "status": "success",
        "filters": {"mes": selected_month.isoformat()},
        "data": [_serialize(row) for row in rows],
    }


@router.post("/comerciales", status_code=status.HTTP_201_CREATED)
async def create_commercial_goal(
    payload: MetaComercialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente),
):
    if payload.tipo == "vendedor":
        seller = (
            await db.execute(
                select(Usuario).where(
                    Usuario.id == payload.vendedor_id,
                    Usuario.rol == "vendedor",
                )
            )
        ).scalars().first()
        if not seller:
            raise HTTPException(status_code=404, detail="El vendedor seleccionado no existe.")

    selected_month = _normalize_month(payload.mes)
    existing_query = select(MetaComercial).where(
        MetaComercial.tipo == payload.tipo,
        MetaComercial.mes == selected_month,
    )
    if payload.tipo == "vendedor":
        existing_query = existing_query.where(MetaComercial.vendedor_id == payload.vendedor_id)
    elif payload.tipo == "sucursal":
        existing_query = existing_query.where(MetaComercial.sucursal == payload.sucursal.strip())
    existing = (await db.execute(existing_query)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una meta para ese alcance y mes. Edítala desde la tabla.",
        )

    goal = MetaComercial(
        tipo=payload.tipo,
        vendedor_id=payload.vendedor_id,
        sucursal=payload.sucursal.strip() if payload.sucursal else None,
        mes=selected_month,
        monto_objetivo=payload.monto_objetivo,
        descripcion=payload.descripcion.strip() if payload.descripcion else None,
        creado_por_id=current_user.id,
    )
    db.add(goal)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe una meta para ese alcance y mes. Edítala desde la tabla.",
        )
    await db.refresh(goal)
    return {"status": "success", "message": "Meta comercial creada.", "data": _serialize(goal)}


@router.put("/comerciales/{meta_id}")
async def update_commercial_goal(
    meta_id: UUID,
    payload: MetaComercialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente),
):
    goal = (await db.execute(select(MetaComercial).where(MetaComercial.id == meta_id))).scalars().first()
    if not goal:
        raise HTTPException(status_code=404, detail="La meta comercial no existe.")
    if payload.monto_objetivo is not None:
        goal.monto_objetivo = payload.monto_objetivo
    if payload.descripcion is not None:
        goal.descripcion = payload.descripcion.strip() or None
    await db.commit()
    await db.refresh(goal)
    return {"status": "success", "message": "Meta comercial actualizada.", "data": _serialize(goal)}


@router.delete("/comerciales/{meta_id}")
async def delete_commercial_goal(
    meta_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente),
):
    goal = (await db.execute(select(MetaComercial).where(MetaComercial.id == meta_id))).scalars().first()
    if not goal:
        raise HTTPException(status_code=404, detail="La meta comercial no existe.")
    await db.delete(goal)
    await db.commit()
    return {"status": "success", "message": "Meta comercial eliminada."}


@router.get("/comerciales/dashboard")
async def commercial_goals_dashboard(
    periodo: str = Query(default="mes"),
    fecha: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente),
):
    if periodo not in VALID_PERIODS:
        raise HTTPException(status_code=422, detail="Periodo inválido. Usa dia, semana o mes.")
    data = await _load_dashboard_data(db, fecha or _business_today(), periodo)
    return {"status": "success", "data": data}


@router.get("/comerciales/mis-avances")
async def my_commercial_goal_progress(
    periodo: str = Query(default="mes"),
    fecha: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol != "vendedor":
        raise HTTPException(status_code=403, detail="Este avance está disponible para vendedores.")
    if periodo not in VALID_PERIODS:
        raise HTTPException(status_code=422, detail="Periodo inválido. Usa dia, semana o mes.")
    dashboard = await _load_dashboard_data(db, fecha or _business_today(), periodo)
    seller = next(
        (row for row in dashboard["vendedores"] if row["vendedor_id"] == str(current_user.id)),
        None,
    )
    if seller is None:
        seller = {
            "vendedor_id": str(current_user.id),
            "vendedor": current_user.nombre_completo or current_user.email,
            "meta": 0,
            "venta_facturada": 0,
            "cumplimiento": 0,
            "origen_meta": "sin_meta",
        }
    return {"status": "success", "periodo": dashboard["periodo"], "data": seller}

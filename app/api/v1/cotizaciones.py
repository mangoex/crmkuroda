from collections import defaultdict
from datetime import date, datetime, timedelta
import io
import unicodedata
from zoneinfo import ZoneInfo

import openpyxl
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, case, delete, func, or_
from sqlalchemy.orm import load_only
from uuid import UUID
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.usuario import Usuario
from app.models.cotizacion import Cotizacion
from app.models.cotizacion_detalle import CotizacionComentario, CotizacionItem
from app.models.recordatorio_seguimiento import RecordatorioSeguimiento
from app.models.promocion import Promocion
from app.schemas.cotizacion import (
    CotizacionCreate,
    CotizacionCreateManual,
    CotizacionUpdate,
    RecordatorioCreate,
    RecordatorioUpdate,
)
from app.schemas.commercial import ComentarioCreate, ComentarioUpdate
from app.agents.cotizaciones_agent import generate_proposal
from app.services.jerarquia import get_ids_vendedores_visibles
from app.services.commercial_analytics import normalize_contact, normalize_text, promotion_priority
from app.services.client_history_service import build_client_history
from app.core.config import settings

require_admin_or_gerente = RoleChecker(["admin", "gerente"])

router = APIRouter()

MAX_OPERATIONAL_PAGE_SIZE = 100
VALID_QUOTE_STATES = {"all", "total", "concretadas", "pendientes", "vencidas"}
VALID_QUOTE_VIEWS = {"completa", "resumen"}

def _normalize_seller_text(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.upper().split())


def _seller_ids_by_name(users: list[Usuario]) -> dict[str, UUID]:
    """Crea un índice de nombres solo cuando la coincidencia es inequívoca."""
    matches: dict[str, Optional[UUID]] = {}
    for user in users:
        normalized_name = _normalize_seller_text(user.nombre_completo)
        if not normalized_name:
            continue
        if normalized_name in matches and matches[normalized_name] != user.id:
            matches[normalized_name] = None
        else:
            matches[normalized_name] = user.id
    return {name: seller_id for name, seller_id in matches.items() if seller_id is not None}


def _business_today() -> date:
    try:
        return datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE)).date()
    except Exception:
        return date.today()


def _quote_status_conditions(today: date) -> dict[str, object]:
    """Condiciones SQL deterministas que comparten listado y KPI."""
    has_invoice = and_(
        Cotizacion.numero_factura.is_not(None),
        func.length(func.trim(Cotizacion.numero_factura)) > 0,
    )
    explicitly_lost = (
        func.upper(func.trim(func.coalesce(Cotizacion.venta_perdida, ""))) == "SI"
    )
    expired_by_age = and_(
        Cotizacion.fecha_registro.is_not(None),
        Cotizacion.fecha_registro < today - timedelta(days=settings.QUOTE_VALID_DAYS),
    )
    expired = and_(~has_invoice, or_(explicitly_lost, expired_by_age))
    return {
        "total": ~expired,
        "concretadas": has_invoice,
        "pendientes": and_(~has_invoice, ~expired),
        "vencidas": expired,
    }


async def _quote_summary(db: AsyncSession, query, conditions: dict[str, object]) -> dict:
    """Obtiene KPI por SQL sin materializar cotizaciones en Python."""
    metrics = []
    for status_name in ("total", "concretadas", "pendientes", "vencidas"):
        condition = conditions[status_name]
        metrics.extend(
            [
                func.coalesce(
                    func.sum(case((condition, 1), else_=0)), 0
                ).label(f"{status_name}_count"),
                func.coalesce(
                    func.sum(case((condition, Cotizacion.total), else_=0)), 0
                ).label(f"{status_name}_amount"),
                func.coalesce(
                    func.sum(
                        case((condition, Cotizacion.importe_facturado), else_=0)
                    ),
                    0,
                ).label(f"{status_name}_invoiced_amount"),
            ]
        )
    row = (await db.execute(query.with_only_columns(*metrics))).mappings().one()
    return {
        status_name: {
            "count": int(row[f"{status_name}_count"] or 0),
            "amount": float(row[f"{status_name}_amount"] or 0),
            "invoiced_amount": float(row[f"{status_name}_invoiced_amount"] or 0),
        }
        for status_name in ("total", "concretadas", "pendientes", "vencidas")
    }


def serialize_cotizacion(
    c: Cotizacion,
    resolved_vendedor_id: Optional[UUID] = None,
    enrichment: Optional[dict] = None,
    vista: str = "completa",
) -> dict:
    vendedor_id = c.vendedor_id or resolved_vendedor_id
    enrichment = enrichment or {}
    data = {
        "id": str(c.id),
        "vendedor_id": str(vendedor_id) if vendedor_id else None,
        "vendedor_nombre": c.vendedor_nombre,
        "vendedor_sin_vincular": vendedor_id is None,
        "cliente_nombre": c.cliente_nombre,
        "numero_cliente": c.numero_cliente,
        "datos_contacto": normalize_contact(c.datos_contacto),
        "total": float(c.total),
        "numero_cotizacion": c.numero_cotizacion,
        "fecha_registro": c.fecha_registro.isoformat() if c.fecha_registro else None,
        "canal": c.canal,
        "numero_factura": c.numero_factura,
        "fecha_factura": c.fecha_factura.isoformat() if c.fecha_factura else None,
        "importe_facturado": float(c.importe_facturado) if c.importe_facturado is not None else None,
        "venta_perdida": c.venta_perdida,
        "comentarios": c.comentarios,
        "comentarios_seguimiento_count": enrichment.get("comentarios_seguimiento_count", 0),
        "tiene_promocion": enrichment.get("tiene_promocion", False),
        "nivel_prioridad": enrichment.get("nivel_prioridad"),
        "promociones_coincidentes": enrichment.get("promociones_coincidentes", []),
    }
    if vista != "resumen":
        data.update(
            {
                "items": c.items,
                "items_detalle": enrichment.get("items_detalle", []),
                "texto_propuesta": c.texto_propuesta,
            }
        )
    return data


async def _load_quote_enrichment(
    db: AsyncSession,
    quotes: list[Cotizacion],
    include_items_detail: bool = True,
) -> dict[UUID, dict]:
    if not quotes:
        return {}
    quote_ids = [quote.id for quote in quotes]
    detail_rows = (
        await db.execute(
            select(CotizacionItem).where(CotizacionItem.cotizacion_id.in_(quote_ids))
        )
    ).scalars().all()
    details_by_quote: dict[UUID, list[CotizacionItem]] = defaultdict(list)
    for row in detail_rows:
        details_by_quote[row.cotizacion_id].append(row)

    item_codes = {
        normalize_text(item.codigo_material)
        for item in detail_rows
        if normalize_text(item.codigo_material)
    }
    promotions = (
        (await db.execute(select(Promocion))).scalars().all()
        if item_codes
        else []
    )

    comment_counts = dict(
        (
            await db.execute(
                select(
                    CotizacionComentario.cotizacion_id,
                    func.count(CotizacionComentario.id),
                )
                .where(CotizacionComentario.cotizacion_id.in_(quote_ids))
                .group_by(CotizacionComentario.cotizacion_id)
            )
        ).all()
    )
    try:
        today = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE)).date()
    except Exception:
        today = date.today()

    result = {}
    for quote in quotes:
        items = details_by_quote.get(quote.id, [])
        promo = promotion_priority(
            quote,
            items,
            promotions,
            today,
            settings.QUOTE_VALID_DAYS,
        )
        result[quote.id] = {
            **promo,
            "comentarios_seguimiento_count": comment_counts.get(quote.id, 0),
            "items_detalle": [
                {
                    "id": str(item.id),
                    "codigo_material": item.codigo_material,
                    "descripcion": item.descripcion,
                    "familia": item.familia,
                    "grupo_materiales": item.grupo_materiales,
                    "cantidad_cotizada": float(item.cantidad_cotizada),
                    "importe_cotizado": float(item.importe_cotizado),
                    "cantidad_facturada": float(item.cantidad_facturada),
                    "importe_facturado": float(item.importe_facturado),
                }
                for item in items
            ] if include_items_detail else [],
        }
    return result


async def _get_authorized_quote(
    db: AsyncSession,
    current_user: Usuario,
    cotizacion_id: UUID,
) -> Cotizacion:
    cotizacion = (
        await db.execute(select(Cotizacion).where(Cotizacion.id == cotizacion_id))
    ).scalars().first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="La cotización solicitada no existe.")
    if current_user.rol == "vendedor":
        ids_visibles = await get_ids_vendedores_visibles(db, current_user) or [current_user.id]
        if cotizacion.vendedor_id not in ids_visibles:
            if cotizacion.vendedor_id is not None:
                raise HTTPException(
                    status_code=403,
                    detail="No tienes permiso para consultar esta cotización.",
                )
            visible_users = (
                await db.execute(select(Usuario).where(Usuario.id.in_(ids_visibles)))
            ).scalars().all()
            visible_names = {
                _normalize_seller_text(user.nombre_completo)
                for user in visible_users
                if user.nombre_completo
            }
            if _normalize_seller_text(cotizacion.vendedor_nombre) not in visible_names:
                raise HTTPException(
                    status_code=403,
                    detail="No tienes permiso para consultar esta cotización.",
                )
    return cotizacion

@router.get("/", status_code=status.HTTP_200_OK)
async def list_cotizaciones(
    vendedor_id: Optional[UUID] = None,
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    busqueda: Optional[str] = Query(default=None, max_length=120),
    total_min: Optional[float] = Query(default=None, ge=0),
    total_max: Optional[float] = Query(default=None, gt=0),
    edad_min_dias: Optional[int] = Query(default=None, ge=0),
    edad_max_dias: Optional[int] = Query(default=None, ge=0),
    sin_vincular: bool = Query(default=False),
    estado: str = Query(default="all"),
    vista: str = Query(default="completa"),
    orden: str = Query(default="desc"),
    limit: int = Query(default=50, ge=1, le=MAX_OPERATIONAL_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    lite: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lists all quotes. Salespeople can only list their own.
    Admins and Managers can list all or filter by seller.
    """
    if str(estado).isdigit():
        if edad_max_dias is None:
            edad_max_dias = int(estado)
        estado = "all"

    if estado not in VALID_QUOTE_STATES:
        raise HTTPException(status_code=422, detail="Estado de cotización inválido.")
    if vista not in VALID_QUOTE_VIEWS:
        raise HTTPException(status_code=422, detail="Vista de cotización inválida.")
    if lite and vista == "completa":
        # Compatibilidad con la optimización previa: la vista resumen es más
        # estricta porque tampoco serializa JSON de partidas ni propuestas.
        vista = "resumen"
    if orden not in {"asc", "desc"}:
        raise HTTPException(status_code=422, detail="Orden de cotización inválido.")
    if total_min is not None and total_max is not None and total_min >= total_max:
        raise HTTPException(status_code=422, detail="El rango de total es inválido.")
    if (
        edad_min_dias is not None
        and edad_max_dias is not None
        and edad_min_dias > edad_max_dias
    ):
        raise HTTPException(status_code=422, detail="El rango de antigüedad es inválido.")

    # Filter by vendedor_id based on role
    if current_user.rol == "vendedor":
        # Vendedor: propio + hijos (jerarquia 1 nivel)
        ids_visibles = await get_ids_vendedores_visibles(db, current_user)
        query = select(Cotizacion)
        count_query = select(func.count()).select_from(Cotizacion)
        if ids_visibles is not None:
            visible_users = (
                await db.execute(select(Usuario).where(Usuario.id.in_(ids_visibles)))
            ).scalars().all()
            visible_names = [
                user.nombre_completo.strip().upper()
                for user in visible_users
                if user.nombre_completo and user.nombre_completo.strip()
            ]
            seller_filters = [Cotizacion.vendedor_id.in_(ids_visibles)]
            if visible_names:
                seller_filters.append(
                    and_(
                        Cotizacion.vendedor_id.is_(None),
                        func.upper(func.trim(Cotizacion.vendedor_nombre)).in_(visible_names),
                    )
                )
            seller_condition = or_(*seller_filters)
            query = query.filter(seller_condition)
            count_query = count_query.filter(seller_condition)

    else:
        query = select(Cotizacion)
        count_query = select(func.count()).select_from(Cotizacion)
        if vendedor_id is not None:
            selected_seller = (await db.execute(select(Usuario).where(Usuario.id == vendedor_id))).scalars().first()
            seller_filters = [Cotizacion.vendedor_id == vendedor_id]
            if selected_seller and selected_seller.nombre_completo:
                # Incluye registros históricos donde el Excel guardó el nombre,
                # pero no logró vincular el UUID del usuario al importar.
                seller_filters.append(
                    and_(
                        Cotizacion.vendedor_id.is_(None),
                        func.upper(func.trim(Cotizacion.vendedor_nombre))
                        == selected_seller.nombre_completo.strip().upper(),
                    )
                )
            seller_condition = or_(*seller_filters)
            query = query.filter(seller_condition)
            count_query = count_query.filter(seller_condition)

    if sin_vincular:
        # Los registros con nombre que se resuelve de manera inequívoca siguen
        # siendo visibles por su vendedor; este filtro muestra únicamente los
        # que no tienen un UUID persistido para revisión administrativa.
        query = query.filter(Cotizacion.vendedor_id.is_(None))
        count_query = count_query.filter(Cotizacion.vendedor_id.is_(None))

    # El filtro se resuelve en PostgreSQL para evitar ambigüedades de formato
    # o zona horaria en el navegador.
    if fecha_inicio is not None:
        query = query.filter(Cotizacion.fecha_registro >= fecha_inicio)
        count_query = count_query.filter(Cotizacion.fecha_registro >= fecha_inicio)
    if fecha_fin is not None:
        query = query.filter(Cotizacion.fecha_registro <= fecha_fin)
        count_query = count_query.filter(Cotizacion.fecha_registro <= fecha_fin)

    if busqueda and busqueda.strip():
        search_term = f"%{busqueda.strip()}%"
        search_condition = or_(
            Cotizacion.cliente_nombre.ilike(search_term),
            Cotizacion.numero_cliente.ilike(search_term),
        )
        query = query.filter(search_condition)
        count_query = count_query.filter(search_condition)

    if total_min is not None:
        query = query.filter(Cotizacion.total >= total_min)
        count_query = count_query.filter(Cotizacion.total >= total_min)
    if total_max is not None:
        query = query.filter(Cotizacion.total < total_max)
        count_query = count_query.filter(Cotizacion.total < total_max)

    # La antigüedad se traduce a fechas de corte en Python, con la zona de
    # negocio, y PostgreSQL sólo compara columnas indexables de fecha.
    today = _business_today()
    if edad_min_dias is not None:
        max_date = today - timedelta(days=edad_min_dias)
        query = query.filter(Cotizacion.fecha_registro <= max_date)
        count_query = count_query.filter(Cotizacion.fecha_registro <= max_date)
    if edad_max_dias is not None:
        min_date = today - timedelta(days=edad_max_dias)
        query = query.filter(Cotizacion.fecha_registro >= min_date)
        count_query = count_query.filter(Cotizacion.fecha_registro >= min_date)

    summary = None
    status_conditions = _quote_status_conditions(today)
    if vista == "resumen":
        summary = await _quote_summary(db, query, status_conditions)

    if estado != "all":
        status_condition = status_conditions[estado]
        query = query.filter(status_condition)
        count_query = count_query.filter(status_condition)

    # Count total quotes
    count_res = await db.execute(count_query)
    total = count_res.scalar_one()

    # List quotes
    if vista == "resumen":
        query = query.options(
            load_only(
                Cotizacion.id,
                Cotizacion.vendedor_id,
                Cotizacion.vendedor_nombre,
                Cotizacion.cliente_nombre,
                Cotizacion.numero_cliente,
                Cotizacion.datos_contacto,
                Cotizacion.total,
                Cotizacion.numero_cotizacion,
                Cotizacion.fecha_registro,
                Cotizacion.canal,
                Cotizacion.numero_factura,
                Cotizacion.fecha_factura,
                Cotizacion.importe_facturado,
                Cotizacion.venta_perdida,
                Cotizacion.comentarios,
            )
        )
    date_order = (
        Cotizacion.fecha_registro.asc().nullslast()
        if orden == "asc"
        else Cotizacion.fecha_registro.desc().nullslast()
    )
    number_order = (
        Cotizacion.numero_cotizacion.asc().nullslast()
        if orden == "asc"
        else Cotizacion.numero_cotizacion.desc().nullslast()
    )
    query = query.order_by(date_order, number_order).offset(offset).limit(limit)
    res = await db.execute(query)
    cotizaciones = res.scalars().all()

    # Las cotizaciones históricas pueden traer solo el nombre del vendedor desde
    # Excel. Se resuelven al serializar, sin alterar la base, para que los filtros
    # administrativos funcionen también con esos registros.
    users = (await db.execute(select(Usuario))).scalars().all()
    seller_ids_by_name = _seller_ids_by_name(users)
    enrichment = await _load_quote_enrichment(
        db,
        list(cotizaciones),
        include_items_detail=vista != "resumen",
    )
    data = [
        serialize_cotizacion(
            c,
            seller_ids_by_name.get(_normalize_seller_text(c.vendedor_nombre)),
            enrichment.get(c.id),
            vista=vista,
        )
        for c in cotizaciones
    ]

    payload = {
        "status": "success",
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total
        },
        "data": data
    }
    if summary is not None:
        payload["summary"] = summary
    return payload


@router.get("/historial-cliente", status_code=status.HTTP_200_OK)
async def get_client_history(
    numero_cliente: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Return aggregate purchase history for a client identified by ``numero_cliente``.

    Salespeople only see operations linked to themselves (or their hierarchy).
    Admins/Managers see all operations for the client.
    """
    if current_user.rol == "soporte":
        raise HTTPException(
            status_code=403,
            detail="El rol de soporte no tiene acceso a la analítica comercial.",
        )

    query = select(Cotizacion).where(
        func.upper(func.trim(Cotizacion.numero_cliente)) == numero_cliente.strip().upper()
    )

    if current_user.rol == "vendedor":
        ids_visibles = await get_ids_vendedores_visibles(db, current_user)
        if ids_visibles is not None:
            visible_users = (
                await db.execute(select(Usuario).where(Usuario.id.in_(ids_visibles)))
            ).scalars().all()
            visible_names = [
                user.nombre_completo.strip().upper()
                for user in visible_users
                if user.nombre_completo and user.nombre_completo.strip()
            ]
            seller_filters = [Cotizacion.vendedor_id.in_(ids_visibles)]
            if visible_names:
                seller_filters.append(
                    and_(
                        Cotizacion.vendedor_id.is_(None),
                        func.upper(func.trim(Cotizacion.vendedor_nombre)).in_(visible_names),
                    )
                )
            query = query.filter(or_(*seller_filters))

    result = await db.execute(query)
    quotes = result.scalars().all()

    try:
        today = datetime.now(ZoneInfo(settings.BUSINESS_TIMEZONE)).date()
    except Exception:
        today = date.today()

    history = build_client_history(
        numero_cliente,
        quotes,
        quote_valid_days=settings.QUOTE_VALID_DAYS,
        today=today,
    )

    return {"status": "success", "data": history}


@router.get("/recordatorios/pendientes", status_code=status.HTTP_200_OK)
async def list_pending_reminders(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Returns pending follow-up reminders (completado = False).
    Vendedores see their own + hierarchy.
    Admins / Gerentes see all.
    """
    if current_user.rol == "soporte":
        raise HTTPException(
            status_code=403,
            detail="El rol de soporte no tiene acceso a esta funcionalidad.",
        )

    query = select(RecordatorioSeguimiento).where(
        RecordatorioSeguimiento.completado == False
    )

    if current_user.rol == "vendedor":
        ids_visibles = await get_ids_vendedores_visibles(db, current_user) or [current_user.id]
        query = query.where(RecordatorioSeguimiento.vendedor_id.in_(ids_visibles))

    result = await db.execute(query.order_by(RecordatorioSeguimiento.fecha_programada.asc()))
    reminders = result.scalars().all()

    # Enrich with quote details
    quote_ids = [r.cotizacion_id for r in reminders]
    quotes_map = {}
    if quote_ids:
        quotes_res = await db.execute(select(Cotizacion).where(Cotizacion.id.in_(quote_ids)))
        quotes_map = {q.id: q for q in quotes_res.scalars().all()}

    data = []
    for r in reminders:
        q = quotes_map.get(r.cotizacion_id)
        data.append({
            "id": str(r.id),
            "cotizacion_id": str(r.cotizacion_id),
            "vendedor_id": str(r.vendedor_id),
            "fecha_programada": r.fecha_programada.isoformat(),
            "nota": r.nota,
            "completado": r.completado,
            "creado_en": r.creado_en.isoformat(),
            "cliente_nombre": q.cliente_nombre if q else "Cliente",
            "numero_cliente": q.numero_cliente if q else None,
            "numero_cotizacion": q.numero_cotizacion if q else None,
            "total": float(q.total) if q else 0,
        })

    return {"status": "success", "data": data}


@router.post("/{cotizacion_id}/recordatorio", status_code=status.HTTP_201_CREATED)
async def create_quote_reminder(
    cotizacion_id: UUID,
    payload: RecordatorioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Creates a new follow-up reminder for a specific quote.
    """
    cotizacion = await _get_authorized_quote(db, current_user, cotizacion_id)

    reminder = RecordatorioSeguimiento(
        cotizacion_id=cotizacion.id,
        vendedor_id=current_user.id,
        fecha_programada=payload.fecha_programada,
        nota=payload.nota.strip() if payload.nota else None,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)

    return {
        "status": "success",
        "message": "Recordatorio de seguimiento agendado exitosamente.",
        "data": {
            "id": str(reminder.id),
            "cotizacion_id": str(reminder.cotizacion_id),
            "vendedor_id": str(reminder.vendedor_id),
            "fecha_programada": reminder.fecha_programada.isoformat(),
            "nota": reminder.nota,
            "completado": reminder.completado,
            "creado_en": reminder.creado_en.isoformat(),
        },
    }


@router.patch("/recordatorios/{recordatorio_id}", status_code=status.HTTP_200_OK)
async def update_reminder(
    recordatorio_id: UUID,
    payload: RecordatorioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Updates or marks a follow-up reminder as completed.
    """
    res = await db.execute(
        select(RecordatorioSeguimiento).where(RecordatorioSeguimiento.id == recordatorio_id)
    )
    reminder = res.scalars().first()
    if not reminder:
        raise HTTPException(status_code=404, detail="El recordatorio solicitado no existe.")

    if current_user.rol == "vendedor" and reminder.vendedor_id != current_user.id:
        ids_visibles = await get_ids_vendedores_visibles(db, current_user) or [current_user.id]
        if reminder.vendedor_id not in ids_visibles:
            raise HTTPException(status_code=403, detail="No tienes permiso para modificar este recordatorio.")

    if payload.fecha_programada is not None:
        reminder.fecha_programada = payload.fecha_programada
    if payload.nota is not None:
        reminder.nota = payload.nota.strip() if payload.nota else None
    if payload.completado is not None:
        reminder.completado = payload.completado
        reminder.completado_en = datetime.utcnow() if payload.completado else None

    await db.commit()
    await db.refresh(reminder)

    return {
        "status": "success",
        "message": "Recordatorio actualizado exitosamente.",
        "data": {
            "id": str(reminder.id),
            "cotizacion_id": str(reminder.cotizacion_id),
            "vendedor_id": str(reminder.vendedor_id),
            "fecha_programada": reminder.fecha_programada.isoformat(),
            "nota": reminder.nota,
            "completado": reminder.completado,
            "completado_en": reminder.completado_en.isoformat() if reminder.completado_en else None,
        },
    }


def _serialize_comment(comment: CotizacionComentario, author: Optional[Usuario] = None) -> dict:
    return {
        "id": str(comment.id),
        "cotizacion_id": str(comment.cotizacion_id),
        "autor_id": str(comment.autor_id) if comment.autor_id else None,
        "autor_nombre": (
            (author.nombre_completo or author.email)
            if author
            else "Usuario eliminado"
        ),
        "comentario": comment.comentario,
        "creado_en": comment.creado_en.isoformat(),
        "editado_en": comment.editado_en.isoformat() if comment.editado_en else None,
    }


@router.get("/{cotizacion_id}/comentarios", status_code=status.HTTP_200_OK)
async def list_quote_comments(
    cotizacion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    await _get_authorized_quote(db, current_user, cotizacion_id)
    rows = (
        await db.execute(
            select(CotizacionComentario, Usuario)
            .outerjoin(Usuario, Usuario.id == CotizacionComentario.autor_id)
            .where(CotizacionComentario.cotizacion_id == cotizacion_id)
            .order_by(CotizacionComentario.creado_en.asc())
        )
    ).all()
    return {
        "status": "success",
        "data": [_serialize_comment(comment, author) for comment, author in rows],
    }


@router.post(
    "/{cotizacion_id}/comentarios",
    status_code=status.HTTP_201_CREATED,
)
async def create_quote_comment(
    cotizacion_id: UUID,
    payload: ComentarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol not in ("admin", "gerente", "vendedor"):
        raise HTTPException(
            status_code=403,
            detail="Tu rol no puede agregar comentarios de seguimiento.",
        )
    await _get_authorized_quote(db, current_user, cotizacion_id)
    text = payload.comentario.strip()
    if not text:
        raise HTTPException(status_code=400, detail="El comentario no puede estar vacío.")
    comment = CotizacionComentario(
        cotizacion_id=cotizacion_id,
        autor_id=current_user.id,
        comentario=text,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return {
        "status": "success",
        "message": "Comentario agregado.",
        "data": _serialize_comment(comment, current_user),
    }


@router.put(
    "/{cotizacion_id}/comentarios/{comentario_id}",
    status_code=status.HTTP_200_OK,
)
async def update_quote_comment(
    cotizacion_id: UUID,
    comentario_id: UUID,
    payload: ComentarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.rol not in ("admin", "gerente", "vendedor"):
        raise HTTPException(
            status_code=403,
            detail="Tu rol no puede editar comentarios de seguimiento.",
        )
    await _get_authorized_quote(db, current_user, cotizacion_id)
    comment = (
        await db.execute(
            select(CotizacionComentario).where(
                CotizacionComentario.id == comentario_id,
                CotizacionComentario.cotizacion_id == cotizacion_id,
            )
        )
    ).scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="El comentario no existe.")
    if current_user.rol not in ("admin", "gerente") and comment.autor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes editar comentarios de otro usuario.")
    text = payload.comentario.strip()
    if not text:
        raise HTTPException(status_code=400, detail="El comentario no puede estar vacío.")
    comment.comentario = text
    comment.editado_en = datetime.utcnow()
    await db.commit()
    await db.refresh(comment)
    author = (
        await db.execute(select(Usuario).where(Usuario.id == comment.autor_id))
    ).scalars().first()
    return {
        "status": "success",
        "message": "Comentario actualizado.",
        "data": _serialize_comment(comment, author),
    }


def _excel_identifier(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    return text or None


def _excel_number(value) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"valor numérico inválido: {value}")


def _apply_imported_quote_values(cotizacion: Cotizacion, values: dict) -> Cotizacion:
    """Actualiza únicamente campos provenientes del Excel y conserva seguimiento."""
    for field, value in values.items():
        setattr(cotizacion, field, value)
    return cotizacion


def _stale_imported_quote_ids(
    existing_quotes: list[Cotizacion],
    retained_ids: set[UUID],
) -> set[UUID]:
    """Sólo las filas importadas con folio pueden ser removidas al reconciliar."""
    return {
        quote.id
        for quote in existing_quotes
        if _excel_identifier(quote.numero_cotizacion)
        and quote.id not in retained_ids
    }


@router.post("/detalle-materiales/upload", status_code=status.HTTP_201_CREATED)
async def upload_quote_material_detail(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente),
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El detalle debe ser un archivo .xlsx.")
    contents = await file.read()
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
        worksheet = workbook.active
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el Excel: {exc}")

    headers = {
        normalize_text(cell.value): index
        for index, cell in enumerate(worksheet[1])
        if cell.value is not None
    }
    required = {
        "numero_cotizacion": "NUMERO DE COTIZACION",
        "codigo_material": "CODIGO MATERIAL",
        "descripcion": "DESCRIPCION",
        "familia": "FAMILIA",
        "grupo_materiales": "GRUPO DE MATERIALES",
        "cantidad_cotizada": "CANTIDAD COTIZADA",
        "importe_cotizado": "IMPORTE COTIZADO",
        "cantidad_facturada": "CANTIDAD FACTURADA",
        "importe_facturado": "IMPORTE FACTURADO",
    }
    missing = [label for label in required.values() if label not in headers]
    if missing:
        raise HTTPException(
            status_code=400,
            detail="Faltan columnas requeridas: " + ", ".join(missing),
        )

    quote_rows = (await db.execute(select(Cotizacion))).scalars().all()
    quotes_by_number: dict[str, list[Cotizacion]] = defaultdict(list)
    for quote in quote_rows:
        number = _excel_identifier(quote.numero_cotizacion)
        if number:
            quotes_by_number[number].append(quote)

    accepted: list[CotizacionItem] = []
    rejected = []
    for row_number, row in enumerate(
        worksheet.iter_rows(min_row=2, values_only=True),
        start=2,
    ):
        if not any(value not in (None, "") for value in row):
            continue
        try:
            quote_number = _excel_identifier(row[headers[required["numero_cotizacion"]]])
            matches = quotes_by_number.get(quote_number or "", [])
            if len(matches) != 1:
                reason = (
                    "cotización inexistente"
                    if not matches
                    else "número de cotización ambiguo"
                )
                rejected.append({"fila": row_number, "cotizacion": quote_number, "motivo": reason})
                continue
            code = _excel_identifier(row[headers[required["codigo_material"]]])
            if not code:
                rejected.append(
                    {"fila": row_number, "cotizacion": quote_number, "motivo": "SKU vacío"}
                )
                continue
            accepted.append(
                CotizacionItem(
                    cotizacion_id=matches[0].id,
                    codigo_material=code,
                    descripcion=_excel_identifier(row[headers[required["descripcion"]]]),
                    familia=_excel_identifier(row[headers[required["familia"]]]),
                    grupo_materiales=_excel_identifier(
                        row[headers[required["grupo_materiales"]]]
                    ),
                    cantidad_cotizada=_excel_number(
                        row[headers[required["cantidad_cotizada"]]]
                    ),
                    importe_cotizado=_excel_number(
                        row[headers[required["importe_cotizado"]]]
                    ),
                    cantidad_facturada=_excel_number(
                        row[headers[required["cantidad_facturada"]]]
                    ),
                    importe_facturado=_excel_number(
                        row[headers[required["importe_facturado"]]]
                    ),
                )
            )
        except Exception as exc:
            rejected.append(
                {"fila": row_number, "cotizacion": None, "motivo": str(exc)}
            )

    if not accepted:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Ninguna partida válida; el detalle existente no fue modificado.",
                "rechazadas": rejected[:100],
            },
        )
    accepted_quote_ids = {item.cotizacion_id for item in accepted}
    await db.execute(
        delete(CotizacionItem).where(
            CotizacionItem.cotizacion_id.in_(accepted_quote_ids)
        )
    )
    db.add_all(accepted)
    await db.commit()
    return {
        "status": "success",
        "message": "Detalle de materiales reemplazado correctamente.",
        "aceptadas": len(accepted),
        "rechazadas": len(rejected),
        "detalle_rechazos": rejected[:100],
    }


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_cotizaciones(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(require_admin_or_gerente),
):
    if not file.filename or not file.filename.lower().endswith((".xls", ".xlsx")):
        raise HTTPException(
            status_code=400,
            detail="Formato de archivo inválido. Sube un archivo de Excel.",
        )
    contents = await file.read()
    error_msg = await process_excel_background(contents, current_user.id)
    if error_msg:
        raise HTTPException(status_code=500, detail=error_msg)
    return {"message": "El archivo se ha procesado exitosamente."}


@router.get("/{cotizacion_id}", status_code=status.HTTP_200_OK)
async def get_cotizacion(
    cotizacion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Retrieves detailed information of a single quote. Enforces ownership check for salespeople."""
    cotizacion = await _get_authorized_quote(db, current_user, cotizacion_id)
    enrichment = await _load_quote_enrichment(db, [cotizacion])

    return {
        "status": "success",
        "data": serialize_cotizacion(cotizacion, enrichment=enrichment.get(cotizacion.id))
    }

@router.post("/manual", status_code=status.HTTP_201_CREATED)
async def create_cotizacion_manual(
    quote_in: CotizacionCreateManual,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Creates a quote manually with preset total and proposal text."""
    # Vendedores can only create quotes for themselves.
    # Managers/Admins can assign a quote to any seller (using current_user as fallback)
    new_quote = Cotizacion(
        vendedor_id=current_user.id,
        cliente_nombre=quote_in.cliente_nombre,
        datos_contacto=quote_in.datos_contacto,
        items=quote_in.items,
        total=quote_in.total,
        texto_propuesta=quote_in.texto_propuesta
    )

    db.add(new_quote)
    await db.commit()
    await db.refresh(new_quote)

    return {
        "status": "success",
        "message": "Cotización creada manualmente con éxito.",
        "data": serialize_cotizacion(new_quote)
    }

@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_cotizacion_agente(
    quote_in: CotizacionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Creates a quote automatically. Invokes the Cotizaciones Agent to
    mathematically compute the total and draft a formal commercial proposal.
    """
    req_adicionales = quote_in.requerimientos_adicionales or ""
    
    # Trigger AI generation
    generated = await generate_proposal(
        cliente_nombre=quote_in.cliente_nombre,
        items=quote_in.items,
        requerimientos_adicionales=req_adicionales
    )

    new_quote = Cotizacion(
        vendedor_id=current_user.id,
        cliente_nombre=quote_in.cliente_nombre,
        datos_contacto=quote_in.datos_contacto,
        items=generated["items_procesados"],
        total=generated["total"],
        texto_propuesta=generated["texto_propuesta"]
    )

    db.add(new_quote)
    await db.commit()
    await db.refresh(new_quote)

    return {
        "status": "success",
        "message": "Cotización generada exitosamente por el Agente de Cotizaciones.",
        "data": serialize_cotizacion(new_quote)
    }

@router.put("/{cotizacion_id}", status_code=status.HTTP_200_OK)
async def update_cotizacion(
    cotizacion_id: UUID,
    quote_in: CotizacionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Updates a quote. Salespeople can only update their own quotes.
    Admins and Managers can update any quote.
    """
    cotizacion = await _get_authorized_quote(db, current_user, cotizacion_id)

    # Update fields
    update_data = quote_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cotizacion, key, value)

    # Automatically set fecha_factura if numero_factura is set
    if "numero_factura" in update_data and update_data["numero_factura"]:
        from datetime import date
        if not cotizacion.fecha_factura:
            cotizacion.fecha_factura = date.today()

    await db.commit()
    await db.refresh(cotizacion)
    enrichment = await _load_quote_enrichment(db, [cotizacion])

    return {
        "status": "success",
        "message": "Cotización actualizada con éxito.",
        "data": serialize_cotizacion(
            cotizacion,
            enrichment=enrichment.get(cotizacion.id),
        )
    }


async def process_excel_background(contents: bytes, uploaded_by_id: UUID):
    from app.core.database import SessionLocal
    from app.models.cotizacion import Cotizacion
    from app.models.usuario import Usuario
    from app.services.actualizaciones_datos import registrar_actualizacion_datos
    from sqlalchemy.future import select
    from sqlalchemy import delete
    
    async with SessionLocal() as db:
        try:
            wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
            ws = wb.active
            
            users_res = await db.execute(select(Usuario))
            users = users_res.scalars().all()
            users_by_code = {
                _normalize_seller_text(user.codigo_vendedor): user.id
                for user in users
                if _normalize_seller_text(user.codigo_vendedor)
            }
            users_by_name = _seller_ids_by_name(users)
            
            existing_quotes = (await db.execute(select(Cotizacion))).scalars().all()
            existing_by_number: dict[str, Cotizacion] = {}
            for existing in existing_quotes:
                number = _excel_identifier(existing.numero_cotizacion)
                if not number:
                    continue
                if number in existing_by_number:
                    raise ValueError(
                        f"El número de cotización {number} está duplicado en la base actual."
                    )
                existing_by_number[number] = existing
            
            synced_count = 0
            new_quotes = []
            seen_numbers: set[str] = set()
            retained_ids: set[UUID] = set()
            
            def safe_float(v):
                try:
                    return float(v) if v is not None else 0.0
                except ValueError:
                    return 0.0
                    
            def safe_date(v):
                if hasattr(v, 'date'):
                    return v.date()
                if isinstance(v, str):
                    try:
                        return datetime.strptime(v.strip().split(' ')[0], '%Y-%m-%d').date()
                    except Exception:
                        pass
                return v

            iter_rows = ws.iter_rows(min_row=2, values_only=True)
            
            for row in iter_rows:
                if not row or not row[0]:
                    continue
                    
                fecha_reg = safe_date(row[0])
                org_ventas = str(row[1]).strip() if row[1] is not None else None
                num_cot_val = str(row[2]).strip() if row[2] is not None else None
                canal_val = str(row[3]).strip() if row[3] is not None else None
                vend_codigo = str(row[4]).strip() if row[4] is not None else None
                vend_nombre = str(row[5]).strip() if row[5] is not None else None
                num_cliente = str(row[6]).strip() if row[6] is not None else None
                cliente_nombre = str(row[7]).strip() if row[7] is not None else None
                telefono = str(row[8]).strip() if row[8] is not None else None
                celular = str(row[9]).strip() if row[9] is not None else None
                email = str(row[10]).strip() if row[10] is not None else None
                num_factura = str(row[11]).strip() if row[11] is not None else None
                fecha_fac = safe_date(row[12])
                
                importe_cot = safe_float(row[13])
                importe_fac = safe_float(row[14])
                pct_importe = safe_float(row[15])
                mat_cot = str(row[16]).strip() if row[16] is not None else None
                mat_fac = str(row[17]).strip() if row[17] is not None else None
                pct_mat = safe_float(row[18])
                
                if not num_cot_val:
                    continue
                if num_cot_val in seen_numbers:
                    raise ValueError(
                        f"El número de cotización {num_cot_val} está duplicado en el Excel."
                    )
                seen_numbers.add(num_cot_val)

                vendedor_id = (
                    users_by_code.get(_normalize_seller_text(vend_codigo))
                    or users_by_name.get(_normalize_seller_text(vend_nombre))
                )

                datos_contacto = {
                    "email": email,
                    "telefono": telefono,
                    "celular": celular
                }

                imported_values = {
                    "numero_cotizacion": num_cot_val,
                    "fecha_registro": fecha_reg,
                    "organizacion_ventas": org_ventas,
                    "canal": canal_val,
                    "vendedor_id": vendedor_id,
                    "vendedor_nombre": vend_nombre,
                    "numero_cliente": num_cliente,
                    "cliente_nombre": cliente_nombre or "Cliente Desconocido",
                    "datos_contacto": datos_contacto,
                    "items": [],
                    "numero_factura": num_factura,
                    "fecha_factura": fecha_fac,
                    "total": importe_cot,
                    "importe_facturado": importe_fac,
                    "porcentaje_importe": pct_importe,
                    "materiales_cotizados": mat_cot,
                    "materiales_facturados": mat_fac,
                    "porcentaje_materiales": pct_mat,
                }
                existing_quote = existing_by_number.get(num_cot_val)
                if existing_quote is not None:
                    _apply_imported_quote_values(existing_quote, imported_values)
                    retained_ids.add(existing_quote.id)
                else:
                    new_quotes.append(Cotizacion(**imported_values))
                synced_count += 1
                    
            stale_ids = _stale_imported_quote_ids(existing_quotes, retained_ids)
            if stale_ids:
                await db.execute(delete(Cotizacion).where(Cotizacion.id.in_(stale_ids)))
            db.add_all(new_quotes)
            await registrar_actualizacion_datos(db, "cotizaciones", uploaded_by_id)
            await db.commit()
            print(
                "Background upload finished. "
                f"Reconciled {synced_count} cotizaciones and preserved existing follow-up history."
            )
            return None
            
        except Exception as e:
            await db.rollback()
            err = f"Error procesando cotizaciones: {str(e)}"
            print(err)
            return err

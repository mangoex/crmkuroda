from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from uuid import UUID
from typing import Optional

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.usuario import Usuario
from app.models.meta import Meta
from app.models.cotizacion import Cotizacion
from app.schemas.meta import MetaCreate, MetaUpdate
from app.agents.metas_agent import generate_seller_goals

router = APIRouter()

# Instantiate RBAC dependencies
require_admin_or_gerente = RoleChecker(["admin", "gerente"])

@router.get("/", status_code=status.HTTP_200_OK)
async def list_metas(
    vendedor_id: Optional[UUID] = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lists sales goals. Salespeople can only see their own goals.
    Admins and Managers can see all or filter by seller.
    """
    # Enforce salesperson filter
    if current_user.rol == "vendedor":
        vendedor_filter_id = current_user.id
    else:
        vendedor_filter_id = vendedor_id

    query = select(Meta)
    count_query = select(func.count()).select_from(Meta)

    if vendedor_filter_id is not None:
        query = query.filter(Meta.vendedor_id == vendedor_filter_id)
        count_query = count_query.filter(Meta.vendedor_id == vendedor_filter_id)

    # Execute count
    count_res = await db.execute(count_query)
    total = count_res.scalar_one()

    # Execute list
    query = query.offset(offset).limit(limit)
    res = await db.execute(query)
    metas = res.scalars().all()

    data = [
        {
            "id": str(m.id),
            "vendedor_id": str(m.vendedor_id),
            "descripcion": m.descripcion,
            "monto_objetivo": float(m.monto_objetivo),
            "fecha_inicio": m.fecha_inicio.isoformat(),
            "fecha_limite": m.fecha_limite.isoformat(),
            "estado": m.estado
        }
        for m in metas
    ]

    return {
        "status": "success",
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total
        },
        "data": data
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_meta_manual(
    meta_in: MetaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente)
):
    """Allows administrators or managers to manually assign a goal to a salesperson."""
    # Ensure seller exists
    res = await db.execute(select(Usuario).filter(Usuario.id == meta_in.vendedor_id, Usuario.rol == "vendedor"))
    vendedor = res.scalars().first()
    if not vendedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El vendedor especificado no existe o no tiene el rol correspondiente."
        )

    new_meta = Meta(
        vendedor_id=meta_in.vendedor_id,
        descripcion=meta_in.descripcion,
        monto_objetivo=meta_in.monto_objetivo,
        fecha_inicio=meta_in.fecha_inicio,
        fecha_limite=meta_in.fecha_limite,
        estado="pendiente"
    )

    db.add(new_meta)
    await db.commit()
    await db.refresh(new_meta)

    return {
        "status": "success",
        "message": "Meta manual creada y asignada exitosamente.",
        "data": {
            "id": str(new_meta.id),
            "vendedor_id": str(new_meta.vendedor_id),
            "descripcion": new_meta.descripcion,
            "monto_objetivo": float(new_meta.monto_objetivo),
            "fecha_inicio": new_meta.fecha_inicio.isoformat(),
            "fecha_limite": new_meta.fecha_limite.isoformat(),
            "estado": new_meta.estado
        }
    }

@router.post("/generate/{vendedor_id}", status_code=status.HTTP_201_CREATED)
async def generate_meta_agente(
    vendedor_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente)
):
    """
    Triggers Metas Agent to automatically analyze recent sales quotes history
    and generate a realistic monthly goal for the salesperson.
    """
    # Ensure seller exists
    res = await db.execute(select(Usuario).filter(Usuario.id == vendedor_id, Usuario.rol == "vendedor"))
    vendedor = res.scalars().first()
    if not vendedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El vendedor especificado no existe o no posee el rol de vendedor."
        )

    objetivos_globales = payload.get("objetivos_globales", "Aumentar un 10% el volumen de cotizaciones cerradas.")

    # Fetch last 10 quotes for history analysis
    quotes_res = await db.execute(
        select(Cotizacion).filter(Cotizacion.vendedor_id == vendedor_id).limit(10)
    )
    quotes = quotes_res.scalars().all()

    historial = [
        {
            "cliente_nombre": q.cliente_nombre,
            "total": float(q.total),
            "texto_propuesta": q.texto_propuesta or ""
        }
        for q in quotes
    ]

    # Generate meta from Agent
    generated = await generate_seller_goals(vendedor.email, historial, objetivos_globales)

    # Persist goal
    new_meta = Meta(
        vendedor_id=vendedor_id,
        descripcion=generated.get("descripcion", "Meta de ventas por IA."),
        monto_objetivo=generated.get("monto_objetivo", 100000.00),
        fecha_inicio=date.today(),
        fecha_limite=date.today() + timedelta(days=30),
        estado="pendiente"
    )

    db.add(new_meta)
    await db.commit()
    await db.refresh(new_meta)

    return {
        "status": "success",
        "message": "Meta de ventas analizada e inyectada exitosamente por el Agente de Metas.",
        "data": {
            "id": str(new_meta.id),
            "vendedor_id": str(new_meta.vendedor_id),
            "descripcion": new_meta.descripcion,
            "monto_objetivo": float(new_meta.monto_objetivo),
            "fecha_inicio": new_meta.fecha_inicio.isoformat(),
            "fecha_limite": new_meta.fecha_limite.isoformat(),
            "estado": new_meta.estado,
            "kpis_clave": generated.get("kpis_clave", [])
        }
    }

@router.put("/{meta_id}", status_code=status.HTTP_200_OK)
async def update_meta(
    meta_id: UUID,
    meta_update: MetaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Updates a goal. Admins and managers can edit any field.
    Salespeople can only update the status ('estado') of their own goals.
    """
    result = await db.execute(select(Meta).filter(Meta.id == meta_id))
    meta = result.scalars().first()
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La meta especificada no fue encontrada."
        )

    # Ownership & field constraints check for salesperson
    if current_user.rol == "vendedor":
        if meta.vendedor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado. No tienes permisos para actualizar metas ajenas."
            )
        # Block seller from editing fields other than 'estado'
        if (meta_update.descripcion is not None or
            meta_update.monto_objetivo is not None or
            meta_update.fecha_inicio is not None or
            meta_update.fecha_limite is not None):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado. Los vendedores sólo están autorizados a modificar el estado de sus metas."
            )

    # Perform update
    if meta_update.descripcion is not None:
        meta.descripcion = meta_update.descripcion
    if meta_update.monto_objetivo is not None:
        meta.monto_objetivo = meta_update.monto_objetivo
    if meta_update.fecha_inicio is not None:
        meta.fecha_inicio = meta_update.fecha_inicio
    if meta_update.fecha_limite is not None:
        meta.fecha_limite = meta_update.fecha_limite
    if meta_update.estado is not None:
        meta.estado = meta_update.estado

    await db.commit()
    await db.refresh(meta)

    return {
        "status": "success",
        "message": "Meta actualizada correctamente.",
        "data": {
            "id": str(meta.id),
            "vendedor_id": str(meta.vendedor_id),
            "descripcion": meta.descripcion,
            "monto_objetivo": float(meta.monto_objetivo),
            "fecha_inicio": meta.fecha_inicio.isoformat(),
            "fecha_limite": meta.fecha_limite.isoformat(),
            "estado": meta.estado
        }
    }

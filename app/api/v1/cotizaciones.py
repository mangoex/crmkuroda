from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from uuid import UUID
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.models.cotizacion import Cotizacion
from app.schemas.cotizacion import CotizacionCreate, CotizacionCreateManual
from app.agents.cotizaciones_agent import generate_proposal

router = APIRouter()

def serialize_cotizacion(c: Cotizacion) -> dict:
    return {
        "id": str(c.id),
        "vendedor_id": str(c.vendedor_id),
        "cliente_nombre": c.cliente_nombre,
        "datos_contacto": c.datos_contacto,
        "items": c.items,
        "total": float(c.total),
        "texto_propuesta": c.texto_propuesta,
        "numero_cotizacion": c.numero_cotizacion,
        "fecha_registro": c.fecha_registro.isoformat() if c.fecha_registro else None,
        "canal": c.canal,
        "numero_factura": c.numero_factura,
        "fecha_factura": c.fecha_factura.isoformat() if c.fecha_factura else None,
        "venta_perdida": c.venta_perdida,
        "comentarios": c.comentarios
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def list_cotizaciones(
    vendedor_id: Optional[UUID] = None,
    limit: int = Query(default=10, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lists all quotes. Salespeople can only list their own.
    Admins and Managers can list all or filter by seller.
    """
    # Filter by vendedor_id based on role
    if current_user.rol == "vendedor":
        vendedor_filter_id = current_user.id
    else:
        vendedor_filter_id = vendedor_id

    query = select(Cotizacion)
    count_query = select(func.count()).select_from(Cotizacion)

    if vendedor_filter_id is not None:
        query = query.filter(Cotizacion.vendedor_id == vendedor_filter_id)
        count_query = count_query.filter(Cotizacion.vendedor_id == vendedor_filter_id)

    # Count total quotes
    count_res = await db.execute(count_query)
    total = count_res.scalar_one()

    # List quotes
    query = query.offset(offset).limit(limit)
    res = await db.execute(query)
    cotizaciones = res.scalars().all()

    data = [serialize_cotizacion(c) for c in cotizaciones]

    return {
        "status": "success",
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total
        },
        "data": data
    }

@router.get("/{cotizacion_id}", status_code=status.HTTP_200_OK)
async def get_cotizacion(
    cotizacion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Retrieves detailed information of a single quote. Enforces ownership check for salespeople."""
    result = await db.execute(select(Cotizacion).filter(Cotizacion.id == cotizacion_id))
    cotizacion = result.scalars().first()
    if not cotizacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La cotización solicitada no existe."
        )

    # Ownership check
    if current_user.rol == "vendedor" and cotizacion.vendedor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. No tienes permisos para visualizar esta cotización."
        )

    return {
        "status": "success",
        "data": serialize_cotizacion(cotizacion)
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

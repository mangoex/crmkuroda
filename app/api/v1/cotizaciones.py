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
from app.schemas.cotizacion import CotizacionCreate, CotizacionCreateManual, CotizacionUpdate
from app.agents.cotizaciones_agent import generate_proposal

import httpx
import csv
import io
from app.models.company import Company
from app.core.security import RoleChecker
from datetime import datetime

require_admin_or_gerente = RoleChecker(["admin", "gerente"])

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
            detail="Acceso denegado. No tienes permisos para actualizar esta cotización."
        )

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

    return {
        "status": "success",
        "message": "Cotización actualizada con éxito.",
        "data": serialize_cotizacion(cotizacion)
    }

@router.post("/sync-csv", status_code=status.HTTP_200_OK)
async def sync_cotizaciones_csv(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente)
):
    """Syncs quotes from Google Drive CSV linked to the company."""
    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()
    
    if not company or not company.csv_drive_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se ha configurado la URL del archivo CSV en la pestana de Conexion."
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(company.csv_drive_url, timeout=15.0)
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar el CSV: {str(e)}")

    csv_text = response.text
    reader = csv.DictReader(io.StringIO(csv_text))
    
    synced_count = 0
    for row in reader:
        # Assuming CSV has columns: cliente_nombre, datos_contacto, total, comentarios
        if "cliente_nombre" not in row or not row["cliente_nombre"].strip():
            continue
            
        new_quote = Cotizacion(
            vendedor_id=current_user.id,
            cliente_nombre=row.get("cliente_nombre", "Sin nombre"),
            datos_contacto=row.get("datos_contacto", ""),
            items=[{"nombre": "Sincronizado desde CSV", "cantidad": 1, "precio_unitario": float(row.get("total", 0))}],
            total=float(row.get("total", 0) or 0),
            comentarios=row.get("comentarios", "Importado desde CSV")
        )
        db.add(new_quote)
        synced_count += 1
        
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Sincronizacion exitosa. Se insertaron {synced_count} cotizaciones."
    }

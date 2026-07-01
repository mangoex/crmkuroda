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


from fastapi import UploadFile, File
import openpyxl

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_cotizaciones(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente)
):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")
    
    contents = await file.read()
    
    try:
        from datetime import datetime
        wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
        ws = wb.active
        
        # 1. Fetch all sellers
        users_res = await db.execute(select(Usuario))
        users = users_res.scalars().all()
        
        # 2. Fetch all existing quotes and map them by numero_cotizacion
        # To avoid massive memory, only select numero_cotizacion and id if possible, but 
        # since we want to UPSERT, we need the ORM objects to modify them.
        # SQLAlchemy tracks them via the session.
        existing_res = await db.execute(select(Cotizacion).filter(Cotizacion.numero_cotizacion.isnot(None)))
        existing_quotes = existing_res.scalars().all()
        quote_map = {q.numero_cotizacion: q for q in existing_quotes}
        
        synced_count = 0
        updated_count = 0
        
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
            if not row or not row[0]: # Skip empty rows
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

            vendedor_id = None
            for u in users:
                if u.codigo_vendedor == vend_codigo or u.nombre == vend_nombre:
                    vendedor_id = u.id
                    break

            datos_contacto = {
                "email": email,
                "telefono": telefono,
                "celular": celular
            }

            existing_quote = quote_map.get(num_cot_val)

            if existing_quote:
                existing_quote.fecha_registro = fecha_reg
                existing_quote.organizacion_ventas = org_ventas
                existing_quote.canal = canal_val
                existing_quote.vendedor_id = vendedor_id
                existing_quote.vendedor_nombre = vend_nombre
                existing_quote.numero_cliente = num_cliente
                existing_quote.cliente_nombre = cliente_nombre or existing_quote.cliente_nombre
                existing_quote.datos_contacto = datos_contacto
                existing_quote.numero_factura = num_factura
                existing_quote.fecha_factura = fecha_fac
                existing_quote.total = importe_cot
                existing_quote.importe_facturado = importe_fac
                existing_quote.porcentaje_importe = pct_importe
                existing_quote.materiales_cotizados = mat_cot
                existing_quote.materiales_facturados = mat_fac
                existing_quote.porcentaje_materiales = pct_mat
                updated_count += 1
            else:
                new_quote = Cotizacion(
                    numero_cotizacion=num_cot_val,
                    fecha_registro=fecha_reg,
                    organizacion_ventas=org_ventas,
                    canal=canal_val,
                    vendedor_id=vendedor_id,
                    vendedor_nombre=vend_nombre,
                    numero_cliente=num_cliente,
                    cliente_nombre=cliente_nombre or "Cliente Desconocido",
                    datos_contacto=datos_contacto,
                    items=[],
                    numero_factura=num_factura,
                    fecha_factura=fecha_fac,
                    total=importe_cot,
                    importe_facturado=importe_fac,
                    porcentaje_importe=pct_importe,
                    materiales_cotizados=mat_cot,
                    materiales_facturados=mat_fac,
                    porcentaje_materiales=pct_mat
                )
                db.add(new_quote)
                synced_count += 1
            
        await db.commit()
        return {
            "status": "success", 
            "message": f"Se importaron {synced_count} cotizaciones nuevas y se actualizaron {updated_count} existentes."
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {str(e)}")

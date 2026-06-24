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
            detail="No se ha configurado la URL del archivo CSV en la pestaña de Conexión."
        )

    # 1. Download CSV content
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(company.csv_drive_url, timeout=15.0)
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo descargar el CSV: {str(e)}"
        )

    csv_text = response.text
    f = io.StringIO(csv_text.strip())
    reader = csv.DictReader(f)
    
    # 2. Get existing quote numbers to prevent duplicates
    existing_quotes_res = await db.execute(select(Cotizacion.numero_cotizacion).filter(Cotizacion.numero_cotizacion.isnot(None)))
    existing_quote_numbers = {q for q in existing_quotes_res.scalars().all()}
    
    # 3. Get all sellers to map quotes to them
    sellers_res = await db.execute(select(Usuario).filter(Usuario.codigo_vendedor.isnot(None)))
    sellers_map = {u.codigo_vendedor.strip().upper(): u.id for u in sellers_res.scalars().all()}
    
    synced_count = 0
    duplicates_count = 0
    
    def find_key(row_keys, matches):
        for k in row_keys:
            if k.strip().lower() in matches:
                return k
        return None

    # Matches for columns
    name_matches = {"cliente_nombre", "nombre del cliente", "cliente", "nombre", "client_name", "client", "name"}
    contact_matches = {"datos_contacto", "contacto", "contact_info"}
    email_matches = {"direccion correo electronico", "email", "correo", "mail", "email_cli"}
    phone_matches = {"numero de telefono", "telefono", "tel", "phone"}
    mobile_matches = {"numero de celular", "celular", "cel", "mobile"}
    num_client_matches = {"numero del cliente", "numero_cliente", "num_cli", "client_number"}
    total_matches = {"total", "importe cotizado c/iva", "importe", "monto", "amount"}
    comment_matches = {"comentarios", "comentario", "notes", "comments", "comment"}
    vendedor_matches = {"vendedor", "codigo_vendedor", "seller", "vendedor_id"}
    quote_num_matches = {"numero_cotizacion", "numero de cotizacion", "cotizacion", "numero", "quote_number", "num_cot"}
    date_reg_matches = {"fecha_registro", "fecha de registro", "fecha", "date", "fecha_reg"}
    channel_matches = {"canal", "canal", "channel"}
    invoice_num_matches = {"numero_factura", "numero de factura", "factura", "invoice", "num_fac"}
    invoice_date_matches = {"fecha_factura", "fecha de factura", "fecha_fac"}
    lost_matches = {"venta_perdida", "venta perdida?", "perdida"}

    def safe_float(val, default=0.0):
        if val is None or str(val).strip() == "":
            return default
        try:
            clean_val = str(val).replace("$", "").replace(",", "").strip()
            return float(clean_val)
        except ValueError:
            return default

    def safe_date(val):
        if val is None or str(val).strip() == "":
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(str(val).strip(), fmt).date()
            except ValueError:
                continue
        return None

    row_keys = reader.fieldnames if reader.fieldnames else []
    
    k_name = find_key(row_keys, name_matches)
    k_contact = find_key(row_keys, contact_matches)
    k_email = find_key(row_keys, email_matches)
    k_phone = find_key(row_keys, phone_matches)
    k_mobile = find_key(row_keys, mobile_matches)
    k_num_client = find_key(row_keys, num_client_matches)
    k_total = find_key(row_keys, total_matches)
    k_comment = find_key(row_keys, comment_matches)
    k_vendedor = find_key(row_keys, vendedor_matches)
    k_quote_num = find_key(row_keys, quote_num_matches)
    k_date_reg = find_key(row_keys, date_reg_matches)
    k_channel = find_key(row_keys, channel_matches)
    k_invoice_num = find_key(row_keys, invoice_num_matches)
    k_invoice_date = find_key(row_keys, invoice_date_matches)
    k_lost = find_key(row_keys, lost_matches)

    for row in reader:
        client_name = row.get(k_name) if k_name else None
        if not client_name or not client_name.strip():
            continue
        client_name = client_name.strip()

        num_cot = None
        if k_quote_num:
            val = row.get(k_quote_num)
            if val is not None:
                # Format to int if ended in .0
                val_str = str(val).strip()
                if val_str.endswith(".0"):
                    try:
                        num_cot = str(int(float(val_str)))
                    except ValueError:
                        num_cot = val_str
                else:
                    num_cot = val_str
        
        if num_cot and num_cot in existing_quote_numbers:
            duplicates_count += 1
            continue

        vendedor_id = current_user.id
        if k_vendedor:
            v_code = str(row.get(k_vendedor) or "").strip().upper()
            if v_code in sellers_map:
                vendedor_id = sellers_map[v_code]

        total_val = safe_float(row.get(k_total) if k_total else 0.0)

        email_val = (row.get(k_email) or "").strip()
        phone_val = (row.get(k_phone) or "").strip()
        mobile_val = (row.get(k_mobile) or "").strip()
        num_client_val = (row.get(k_num_client) or "").strip()
        
        if k_contact and not email_val and not phone_val:
            generic_contact = (row.get(k_contact) or "").strip()
            if "@" in generic_contact:
                email_val = generic_contact
            else:
                phone_val = generic_contact

        datos_contacto = {
            "email": email_val,
            "telefono": phone_val,
            "celular": mobile_val,
            "numero_cliente": num_client_val
        }

        fecha_reg = safe_date(row.get(k_date_reg)) if k_date_reg else None
        if not fecha_reg:
            fecha_reg = datetime.utcnow().date()
            
        canal_val = str(row.get(k_channel) or "").strip() if k_channel else "Drive CSV"
        num_fac = str(row.get(k_invoice_num) or "").strip() if k_invoice_num else None
        fecha_fac = safe_date(row.get(k_invoice_date)) if k_invoice_date else None
        venta_perdida_val = str(row.get(k_lost) or "").strip() if k_lost else "No"
        comentarios_val = str(row.get(k_comment) or "").strip() if k_comment else "Sincronizado desde CSV"

        new_quote = Cotizacion(
            vendedor_id=vendedor_id,
            cliente_nombre=client_name,
            datos_contacto=datos_contacto,
            items=[{
                "producto": "Sincronizado desde CSV",
                "cantidad": 1,
                "precio_unitario": total_val
            }],
            total=total_val,
            numero_cotizacion=num_cot,
            fecha_registro=fecha_reg,
            canal=canal_val,
            numero_factura=num_fac,
            fecha_factura=fecha_fac,
            venta_perdida=venta_perdida_val,
            comentarios=comentarios_val
        )
        
        db.add(new_quote)
        synced_count += 1
        if num_cot:
            existing_quote_numbers.add(num_cot)

    if synced_count > 0:
        await db.commit()
        
    return {
        "status": "success",
        "message": f"Sincronización finalizada exitosamente.",
        "details": {
            "imported": synced_count,
            "duplicates_skipped": duplicates_count
        }
    }

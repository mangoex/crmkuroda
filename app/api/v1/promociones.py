from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
import io
import openpyxl

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.promocion import Promocion
from app.models.usuario import Usuario
from app.models.cotizacion import Cotizacion
from app.models.cotizacion_detalle import CotizacionItem
from app.services.commercial_analytics import find_clients_for_promotion, safe_phone_href
from app.services.jerarquia import get_ids_vendedores_visibles

router = APIRouter()

require_admin = RoleChecker(["admin", "gerente"])

@router.get("/")
async def list_promociones(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Promocion))
    promociones = result.scalars().all()
    return {"status": "success", "data": [p.to_dict() for p in promociones]}

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_promociones(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")
    
    contents = await file.read()
    
    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
        ws = wb.active
        
        # Eliminar promociones anteriores
        await db.execute(delete(Promocion))
        
        rows_added = 0
        
        # Skip header
        iter_rows = ws.iter_rows(min_row=2, values_only=True)
        for row in iter_rows:
            if not row or not row[0]: # Skip empty rows
                continue
                
            promocion = Promocion(
                centro=str(row[0]) if row[0] is not None else None,
                descrip_gpo_materiales=str(row[1]) if row[1] is not None else None,
                indicador_abc=str(row[2]) if row[2] is not None else None,
                codigo_material=str(row[3]) if row[3] is not None else None,
                descripcion_material=str(row[4]) if row[4] is not None else None,
                unidad_medida=str(row[5]) if row[5] is not None else None,
                costo_promedio=float(row[6]) if row[6] is not None else None,
                costo_promedio_moneda=float(row[7]) if row[7] is not None else None,
                costo_estandar=float(row[8]) if row[8] is not None else None,
                precio_promocion=float(row[9]) if len(row) > 9 and row[9] is not None else None,
                moneda=str(row[10]) if len(row) > 10 and row[10] is not None else None,
                valido_hasta=row[11] if len(row) > 11 and row[11] is not None else None, 
                costo_estandar_promocion=float(row[12]) if len(row) > 12 and row[12] is not None else None,
                margen_promocion=float(row[13]) if len(row) > 13 and row[13] is not None else None,
                proveedor=str(row[14]) if len(row) > 14 and row[14] is not None else None,
                inventario_disponible=float(row[15]) if len(row) > 15 and row[15] is not None else None
            )
            db.add(promocion)
            rows_added += 1
            
        await db.commit()
        return {"status": "success", "message": f"Se han cargado {rows_added} promociones exitosamente."}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {str(e)}")


@router.get("/{promocion_id}/clientes-potenciales", status_code=status.HTTP_200_OK)
async def get_promotion_potential_clients(
    promocion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Find clients who previously purchased the material that is now on promotion.

    Returns a list of clients with their contact info and purchase history.
    Salespeople only see clients linked to their quotes.
    """
    if current_user.rol == "soporte":
        raise HTTPException(
            status_code=403,
            detail="El rol de soporte no tiene acceso a esta funcionalidad.",
        )

    # Fetch the promotion.
    promotion = (
        await db.execute(select(Promocion).where(Promocion.id == promocion_id))
    ).scalars().first()
    if not promotion:
        raise HTTPException(status_code=404, detail="La promoción no existe.")

    # Fetch items + their parent quotes via join.
    from sqlalchemy import and_
    query = (
        select(CotizacionItem, Cotizacion)
        .join(Cotizacion, CotizacionItem.cotizacion_id == Cotizacion.id)
    )

    # Apply seller visibility filter for vendedor role.
    if current_user.rol == "vendedor":
        from sqlalchemy import or_, func
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
    items_with_quotes = result.all()

    clients = find_clients_for_promotion(
        promotion,
        items_with_quotes,
        only_invoiced=False,  # Include both invoiced and quoted
    )

    # Build pre-filled message for WhatsApp/Email.
    promo_desc = promotion.descripcion_material or promotion.codigo_material or "Material"
    promo_price = f"${promotion.precio_promocion:,.2f}" if promotion.precio_promocion else "Precio especial"
    promo_valid = promotion.valido_hasta.strftime("%d/%m/%Y") if promotion.valido_hasta else "por tiempo limitado"

    wa_message = (
        f"¡Hola! Le informamos que tenemos una promoción especial en "
        f"{promo_desc} a {promo_price} (válido hasta {promo_valid}). "
        f"¿Le interesa? Quedo a sus órdenes."
    )
    email_subject = f"Promoción Especial: {promo_desc} a {promo_price}"
    email_body = (
        f"Estimado cliente,\n\n"
        f"Le informamos que tenemos una promoción especial:\n\n"
        f"  Material: {promo_desc}\n"
        f"  Precio de Promoción: {promo_price}\n"
        f"  Válido hasta: {promo_valid}\n\n"
        f"¡No deje pasar esta oportunidad!\n\nSaludos cordiales."
    )

    # Enrich each client with contact action URLs.
    for client in clients:
        contact = client.get("contacto", {})
        phone = safe_phone_href(contact.get("contacto_preferente"))
        email = contact.get("email")
        client["acciones"] = {
            "whatsapp_url": (
                f"https://wa.me/{phone}?text={__import__('urllib.parse', fromlist=['quote']).quote(wa_message)}"
                if phone
                else None
            ),
            "email_url": (
                f"mailto:{email}?subject={__import__('urllib.parse', fromlist=['quote']).quote(email_subject)}"
                f"&body={__import__('urllib.parse', fromlist=['quote']).quote(email_body)}"
                if email
                else None
            ),
            "telefono": phone,
        }

    return {
        "status": "success",
        "data": {
            "promocion": promotion.to_dict(),
            "mensaje_whatsapp": wa_message,
            "asunto_email": email_subject,
            "clientes": clients,
            "total_clientes": len(clients),
        },
    }

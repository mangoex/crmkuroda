from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from uuid import UUID
from typing import Optional

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user, get_password_hash
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate

router = APIRouter()

# Instantiate RBAC dependencies
require_admin_or_gerente = RoleChecker(["admin", "gerente"])

@router.get("/", status_code=status.HTTP_200_OK)
async def list_vendedores(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente)
):
    """Lists all registered salespersons with clean limit/offset pagination and metadata."""
    # Count total vendedor records
    count_query = select(func.count()).select_from(Usuario).filter(Usuario.rol == "vendedor")
    count_res = await db.execute(count_query)
    total = count_res.scalar_one()

    # Query paginated vendedor records
    query = select(Usuario).filter(Usuario.rol == "vendedor").offset(offset).limit(limit)
    res = await db.execute(query)
    vendedores = res.scalars().all()

    data = [
        {
            "id": str(v.id),
            "email": v.email,
            "rol": v.rol,
            "telefono_whatsapp": v.telefono_whatsapp,
            "codigo_vendedor": v.codigo_vendedor,
            "nombre_completo": v.nombre_completo,
            "avatar": v.avatar
        }
        for v in vendedores
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
async def create_vendedor(
    seller_in: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente)
):
    """Allows administrators or managers to register new salespersons."""
    if seller_in.rol != "vendedor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este endpoint está reservado exclusivamente para la creación de cuentas de Vendedor."
        )

    # Check for email duplicate
    result = await db.execute(select(Usuario).filter(Usuario.email == seller_in.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario registrado con este correo electrónico."
        )

    # Check for whatsapp phone duplicate
    if seller_in.telefono_whatsapp:
        result = await db.execute(select(Usuario).filter(Usuario.telefono_whatsapp == seller_in.telefono_whatsapp))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario registrado con este número de WhatsApp."
            )

    hashed_password = get_password_hash(seller_in.password)
    new_seller = Usuario(
        email=seller_in.email,
        hashed_password=hashed_password,
        rol="vendedor",
        telefono_whatsapp=seller_in.telefono_whatsapp
    )

    db.add(new_seller)
    await db.commit()
    await db.refresh(new_seller)

    return {
        "status": "success",
        "message": "Vendedor creado exitosamente.",
        "data": {
            "id": str(new_seller.id),
            "email": new_seller.email,
            "rol": new_seller.rol,
            "telefono_whatsapp": new_seller.telefono_whatsapp,
            "codigo_vendedor": new_seller.codigo_vendedor,
            "nombre_completo": new_seller.nombre_completo,
            "avatar": new_seller.avatar
        }
    }

@router.put("/{vendedor_id}", status_code=status.HTTP_200_OK)
async def update_vendedor(
    vendedor_id: UUID,
    seller_update: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Updates seller details. Allows admins/gerentes to update anyone, and salespeople to update themselves."""
    # RBAC & Ownership check
    if current_user.rol not in ["admin", "gerente"] and current_user.id != vendedor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar los datos de este vendedor."
        )

    result = await db.execute(select(Usuario).filter(Usuario.id == vendedor_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El vendedor especificado no existe."
        )

    # Prevent non-admin/gerente from escalating roles
    if current_user.rol not in ["admin", "gerente"] and seller_update.rol is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se permite auto-modificar el rol de usuario."
        )

    # Apply updates
    if seller_update.email is not None:
        user.email = seller_update.email
    if seller_update.rol is not None:
        user.rol = seller_update.rol
    if seller_update.telefono_whatsapp is not None:
        user.telefono_whatsapp = seller_update.telefono_whatsapp
    if seller_update.codigo_vendedor is not None:
        user.codigo_vendedor = seller_update.codigo_vendedor
    if seller_update.nombre_completo is not None:
        user.nombre_completo = seller_update.nombre_completo
    if seller_update.avatar is not None:
        user.avatar = seller_update.avatar
    if seller_update.password is not None:
        user.hashed_password = get_password_hash(seller_update.password)

    await db.commit()
    await db.refresh(user)

    return {
        "status": "success",
        "message": "Datos del vendedor actualizados correctamente.",
        "data": {
            "id": str(user.id),
            "email": user.email,
            "rol": user.rol,
            "telefono_whatsapp": user.telefono_whatsapp,
            "codigo_vendedor": user.codigo_vendedor,
            "nombre_completo": user.nombre_completo,
            "avatar": user.avatar
        }
    }

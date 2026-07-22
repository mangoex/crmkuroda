from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash, get_current_user
from app.models.usuario import Usuario
from app.models.registro_acceso import RegistroAcceso
from app.schemas.usuario import UsuarioCreate, Token
from app.core.config import settings

router = APIRouter()


def _calendar_month_bounds(month_value: Optional[str], local_tz: ZoneInfo):
    """Devuelve el periodo UTC de un mes calendario en la zona operativa."""
    if month_value:
        try:
            selected = datetime.strptime(month_value, "%Y-%m")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El mes debe tener el formato YYYY-MM.",
            ) from exc
        year, month = selected.year, selected.month
    else:
        today = datetime.now(local_tz).date()
        year, month = today.year, today.month

    month_start_local = datetime(year, month, 1, tzinfo=local_tz)
    if month == 12:
        next_month_local = datetime(year + 1, 1, 1, tzinfo=local_tz)
    else:
        next_month_local = datetime(year, month + 1, 1, tzinfo=local_tz)

    return (
        month_start_local.astimezone(timezone.utc),
        next_month_local.astimezone(timezone.utc),
        f"{year:04d}-{month:02d}",
    )

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_in: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new user (Admin, Gerente, Vendedor) with verified uniqueness."""
    # Force role to "vendedor" for public registrations to prevent privilege escalation
    user_in.rol = "vendedor"

    # Check email duplicate
    result = await db.execute(select(Usuario).filter(Usuario.email == user_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario registrado con este correo electrónico."
        )

    # Check whatsapp duplicate if provided
    if user_in.telefono_whatsapp:
        result = await db.execute(select(Usuario).filter(Usuario.telefono_whatsapp == user_in.telefono_whatsapp))
        existing_phone = result.scalars().first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario registrado con este número de WhatsApp."
            )

    hashed_password = get_password_hash(user_in.password)
    new_user = Usuario(
        email=user_in.email,
        hashed_password=hashed_password,
        rol=user_in.rol,
        telefono_whatsapp=user_in.telefono_whatsapp,
        codigo_vendedor=user_in.codigo_vendedor,
        nombre_completo=user_in.nombre_completo,
        avatar=user_in.avatar
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "status": "success",
        "message": "Usuario creado exitosamente.",
        "data": {
            "id": str(new_user.id),
            "email": new_user.email,
            "rol": new_user.rol,
            "telefono_whatsapp": new_user.telefono_whatsapp,
            "codigo_vendedor": new_user.codigo_vendedor,
            "nombre_completo": new_user.nombre_completo
        }
    }

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Logs in a user using OAuth2 form data and returns a JWT access token."""
    result = await db.execute(select(Usuario).filter(Usuario.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "rol": user.rol},
        expires_delta=access_token_expires
    )

    db.add(RegistroAcceso(usuario_id=user.id))
    await db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "rol": user.rol
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def close_session(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Cierra el ultimo acceso abierto del usuario actual."""
    result = await db.execute(
        select(RegistroAcceso)
        .where(RegistroAcceso.usuario_id == current_user.id, RegistroAcceso.salida.is_(None))
        .order_by(RegistroAcceso.entrada.desc())
        .limit(1)
    )
    registro = result.scalars().first()
    if registro:
        registro.salida = datetime.now(timezone.utc)
        await db.commit()
    return {"status": "success"}


@router.get("/access-log/today", status_code=status.HTTP_200_OK)
async def get_today_access_log(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Devuelve entradas y salidas de hoy para el tablero de coordinacion."""
    if current_user.rol not in {"admin", "gerente"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")

    local_tz = ZoneInfo("America/Mazatlan")
    today = datetime.now(local_tz).date()
    day_start = datetime.combine(today, time.min, tzinfo=local_tz).astimezone(timezone.utc)
    next_day = day_start + timedelta(days=1)
    result = await db.execute(
        select(RegistroAcceso, Usuario)
        .join(Usuario, Usuario.id == RegistroAcceso.usuario_id)
        .where(RegistroAcceso.entrada >= day_start, RegistroAcceso.entrada < next_day)
        .order_by(RegistroAcceso.entrada.desc())
        .limit(30)
    )
    return {
        "status": "success",
        "data": [
            {
                "id": str(registro.id),
                "usuario": usuario.nombre_completo or usuario.email,
                "rol": usuario.rol,
                "entrada": registro.entrada.isoformat() if registro.entrada else None,
                "salida": registro.salida.isoformat() if registro.salida else None,
            }
            for registro, usuario in result.all()
        ],
    }


@router.get("/access-log", status_code=status.HTTP_200_OK)
async def get_access_log_by_month(
    month: Optional[str] = Query(default=None, description="Mes calendario YYYY-MM"),
    vendedor_id: Optional[UUID] = Query(default=None, description="UUID del vendedor"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Devuelve la actividad de acceso del mes y vendedor seleccionados."""
    if current_user.rol not in {"admin", "gerente"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")

    local_tz = ZoneInfo("America/Mazatlan")
    month_start, next_month, calendar_month = _calendar_month_bounds(month, local_tz)

    if vendedor_id is not None:
        seller_result = await db.execute(select(Usuario).where(Usuario.id == vendedor_id))
        seller = seller_result.scalars().first()
        if not seller or seller.rol != "vendedor":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El vendedor seleccionado no es válido.")

    query = (
        select(RegistroAcceso, Usuario)
        .join(Usuario, Usuario.id == RegistroAcceso.usuario_id)
        .where(RegistroAcceso.entrada >= month_start, RegistroAcceso.entrada < next_month)
        .order_by(RegistroAcceso.entrada.desc())
        .limit(250)
    )
    if vendedor_id is not None:
        query = query.where(RegistroAcceso.usuario_id == vendedor_id)

    records = []
    for registro, usuario in (await db.execute(query)).all():
        entrada_local = registro.entrada.astimezone(local_tz) if registro.entrada else None
        records.append({
            "id": str(registro.id),
            "usuario_id": str(usuario.id),
            "usuario": usuario.nombre_completo or usuario.email,
            "rol": usuario.rol,
            "entrada": registro.entrada.isoformat() if registro.entrada else None,
            "salida": registro.salida.isoformat() if registro.salida else None,
            "fecha_actividad": entrada_local.date().isoformat() if entrada_local else None,
            "mes_calendario": entrada_local.strftime("%Y-%m") if entrada_local else calendar_month,
        })

    return {"status": "success", "month": calendar_month, "data": records}

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Retrieves the currently logged-in user's profile details."""
    # Resolver hijos directos para que el frontend arme el dropdown de filtro
    hijos = []
    if current_user.rol == "vendedor":
        res = await db.execute(
            select(Usuario).where(
                Usuario.vendedor_padre_id == current_user.id,
                Usuario.rol == "vendedor",
            )
        )
        for h in res.scalars().all():
            hijos.append({
                "id": str(h.id),
                "codigo_vendedor": h.codigo_vendedor,
                "nombre_completo": h.nombre_completo,
                "email": h.email,
            })

    return {
        "status": "success",
        "data": {
            "id": str(current_user.id),
            "email": current_user.email,
            "rol": current_user.rol,
            "telefono_whatsapp": current_user.telefono_whatsapp,
            "codigo_vendedor": current_user.codigo_vendedor,
            "nombre_completo": current_user.nombre_completo,
            "avatar": current_user.avatar,
            "vendedor_padre_id": str(current_user.vendedor_padre_id) if current_user.vendedor_padre_id else None,
            "vendedores_hijos": hijos,
        }
    }

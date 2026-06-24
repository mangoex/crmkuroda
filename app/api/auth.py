from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash, get_current_user
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, Token
from app.core.config import settings

router = APIRouter()

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
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "rol": user.rol
    }

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_me(current_user: Usuario = Depends(get_current_user)):
    """Retrieves the currently logged-in user's profile details."""
    return {
        "status": "success",
        "data": {
            "id": str(current_user.id),
            "email": current_user.email,
            "rol": current_user.rol,
            "telefono_whatsapp": current_user.telefono_whatsapp,
            "codigo_vendedor": current_user.codigo_vendedor,
            "nombre_completo": current_user.nombre_completo,
            "avatar": current_user.avatar
        }
    }

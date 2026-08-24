from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from uuid import UUID

class UsuarioBase(BaseModel):
    email: EmailStr
    rol: str = Field(description="Rol del usuario: admin, gerente, vendedor, soporte, compras, logistica, marketing")
    telefono_whatsapp: Optional[str] = Field(default=None, description="Número de teléfono de WhatsApp (ej. +521234567890)")
    codigo_vendedor: Optional[str] = Field(default=None, description="Código de vendedor (ej. C01)")
    nombre_completo: Optional[str] = Field(default=None, description="Nombre completo del vendedor")
    avatar: Optional[str] = Field(default=None, description="Avatar del usuario en formato Base64")

class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=6, description="Contraseña del usuario (mínimo 6 caracteres)")
    vendedor_padre_id: Optional[str] = Field(default=None, description="UUID del vendedor padre (jerarquia 1 nivel, solo vendedor->vendedor)")

class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    rol: Optional[str] = None
    telefono_whatsapp: Optional[str] = None
    codigo_vendedor: Optional[str] = None
    nombre_completo: Optional[str] = None
    avatar: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6)
    vendedor_padre_id: Optional[str] = Field(default=None, description="UUID del vendedor padre (string vacio = quitar padre)")

class UsuarioResponse(BaseModel):
    id: UUID
    email: EmailStr
    rol: str
    telefono_whatsapp: Optional[str] = None
    codigo_vendedor: Optional[str] = None
    nombre_completo: Optional[str] = None
    avatar: Optional[str] = None
    vendedor_padre_id: Optional[UUID] = None
    vendedores_hijos: List[UUID] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    rol: str

class TokenData(BaseModel):
    email: Optional[str] = None
    rol: Optional[str] = None

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class ClienteBase(BaseModel):
    sociedad: Optional[str] = "MKS"
    numero_cliente: Optional[str] = None
    nombre: str
    nombre_contacto: Optional[str] = None
    rfc: Optional[str] = None
    tipo_persona: Optional[str] = "Persona física"
    calle: Optional[str] = None
    numero_exterior: Optional[str] = None
    colonia: Optional[str] = None
    codigo_postal: Optional[str] = None
    poblacion: Optional[str] = None
    estado: Optional[str] = None
    telefono: Optional[str] = None
    celular: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    sociedad: Optional[str] = None
    numero_cliente: Optional[str] = None
    nombre: Optional[str] = None
    nombre_contacto: Optional[str] = None
    rfc: Optional[str] = None
    tipo_persona: Optional[str] = None
    calle: Optional[str] = None
    numero_exterior: Optional[str] = None
    colonia: Optional[str] = None
    codigo_postal: Optional[str] = None
    poblacion: Optional[str] = None
    estado: Optional[str] = None
    telefono: Optional[str] = None
    celular: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None

class ClienteOut(ClienteBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ClientePaginatedOut(BaseModel):
    status: str = "success"
    total: int
    page: int
    limit: int
    pages: int
    total_fisicas: int = 0
    total_morales: int = 0
    data: List[ClienteOut]

class ClienteFilterOptionsOut(BaseModel):
    status: str = "success"
    tipos_persona: List[str]
    colonias: List[str]
    poblaciones: List[str]

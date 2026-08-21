from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class AsignacionIniciar(BaseModel):
    cliente_ids: List[UUID]
    vendedor_ids: List[UUID]

class PujaCrear(BaseModel):
    cliente_id: UUID
    razon: str = Field(..., min_length=5, description="La razón por la cual se debe asignar este cliente")

class PujaResolver(BaseModel):
    cliente_id: UUID
    puja_ganadora_id: UUID

class UsuarioSimpleSchema(BaseModel):
    id: UUID
    email: str
    nombre_completo: Optional[str] = None
    rol: str

    model_config = ConfigDict(from_attributes=True)

class PujaResponse(BaseModel):
    id: UUID
    cliente_id: UUID
    vendedor_id: UUID
    razon: str
    estado: str
    creado_en: datetime
    vendedor: Optional[UsuarioSimpleSchema] = None

    model_config = ConfigDict(from_attributes=True)

class ClienteDisponibleResponse(BaseModel):
    id: UUID
    nombre: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    comentarios: Optional[str] = None
    estado: str
    asignado_a: Optional[UUID] = None
    vendedores_permitidos: Optional[List[str]] = None
    creado_en: datetime
    asignado_vendedor: Optional[UsuarioSimpleSchema] = None
    pujas: List[PujaResponse] = []

    model_config = ConfigDict(from_attributes=True)

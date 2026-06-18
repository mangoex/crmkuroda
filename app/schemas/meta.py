from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from decimal import Decimal
from uuid import UUID

class MetaBase(BaseModel):
    descripcion: str
    monto_objetivo: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    fecha_inicio: date
    fecha_limite: date
    estado: str = Field(default="pendiente", description="Estado de la meta: pendiente, en_progreso, completada")

class MetaCreate(BaseModel):
    vendedor_id: UUID
    descripcion: str
    monto_objetivo: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    fecha_inicio: date
    fecha_limite: date

class MetaUpdate(BaseModel):
    descripcion: Optional[str] = None
    monto_objetivo: Optional[Decimal] = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    fecha_inicio: Optional[date] = None
    fecha_limite: Optional[date] = None
    estado: Optional[str] = None

class MetaResponse(MetaBase):
    id: UUID
    vendedor_id: UUID

    class Config:
        from_attributes = True

class MetasAgentResponse(BaseModel):
    monto_objetivo: Decimal
    descripcion: str
    kpis_clave: list[str]

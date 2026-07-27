from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ComentarioCreate(BaseModel):
    comentario: str = Field(min_length=1, max_length=4000)


class ComentarioUpdate(BaseModel):
    comentario: str = Field(min_length=1, max_length=4000)


class CanalVentaUpsert(BaseModel):
    codigo_origen: str = Field(min_length=1, max_length=100)
    nombre_normalizado: str = Field(min_length=1, max_length=100)
    activo: bool = True


class ComentarioResponse(BaseModel):
    id: UUID
    cotizacion_id: UUID
    autor_id: Optional[UUID] = None
    autor_nombre: Optional[str] = None
    comentario: str
    creado_en: datetime
    editado_en: Optional[datetime] = None

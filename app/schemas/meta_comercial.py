from datetime import date
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


TipoMetaComercial = Literal["general", "vendedor", "sucursal"]


class MetaComercialBase(BaseModel):
    tipo: TipoMetaComercial
    vendedor_id: Optional[UUID] = None
    sucursal: Optional[str] = Field(default=None, max_length=160)
    mes: date
    monto_objetivo: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    descripcion: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validar_alcance(self):
        if self.mes.day != 1:
            raise ValueError("El mes debe indicar el primer día del mes calendario.")
        if self.tipo == "vendedor":
            if not self.vendedor_id or self.sucursal:
                raise ValueError("Una meta por vendedor requiere vendedor_id y no acepta sucursal.")
        elif self.tipo == "sucursal":
            if not self.sucursal or not self.sucursal.strip() or self.vendedor_id:
                raise ValueError("Una meta por sucursal requiere sucursal y no acepta vendedor_id.")
        elif self.vendedor_id or self.sucursal:
            raise ValueError("Una meta general no acepta vendedor_id ni sucursal.")
        return self


class MetaComercialCreate(MetaComercialBase):
    pass


class MetaComercialUpdate(BaseModel):
    monto_objetivo: Optional[Decimal] = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    descripcion: Optional[str] = Field(default=None, max_length=1000)


class MetaComercialResponse(MetaComercialBase):
    id: UUID
    creado_por_id: Optional[UUID] = None

    class Config:
        from_attributes = True

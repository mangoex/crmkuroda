from pydantic import BaseModel, Field
from typing import Optional, Any
from decimal import Decimal
from uuid import UUID
from datetime import date

class CotizacionBase(BaseModel):
    cliente_nombre: str
    datos_contacto: dict[str, Any] = Field(description="JSON con email, telefono, etc.")
    items: list[dict[str, Any]] = Field(description="Lista de items: [{'producto': str, 'cantidad': int, 'precio_unitario': float}]")
    total: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    texto_propuesta: Optional[str] = None
    
    # Excel imported fields
    numero_cotizacion: Optional[str] = None
    fecha_registro: Optional[date] = None
    canal: Optional[str] = None
    numero_factura: Optional[str] = None
    fecha_factura: Optional[date] = None
    venta_perdida: Optional[str] = None
    comentarios: Optional[str] = None

class CotizacionCreate(BaseModel):
    cliente_nombre: str
    datos_contacto: dict[str, Any]
    items: list[dict[str, Any]]
    requerimientos_adicionales: Optional[str] = Field(default=None, description="Requerimientos o notas adicionales para la propuesta")

class CotizacionCreateManual(BaseModel):
    cliente_nombre: str
    datos_contacto: dict[str, Any]
    items: list[dict[str, Any]]
    total: Decimal
    texto_propuesta: str
    
    # Optional Excel fields
    numero_cotizacion: Optional[str] = None
    fecha_registro: Optional[date] = None
    canal: Optional[str] = None
    numero_factura: Optional[str] = None
    fecha_factura: Optional[date] = None
    venta_perdida: Optional[str] = None
    comentarios: Optional[str] = None

class CotizacionUpdate(BaseModel):
    cliente_nombre: Optional[str] = None
    datos_contacto: Optional[dict[str, Any]] = None
    items: Optional[list[dict[str, Any]]] = None
    total: Optional[Decimal] = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    texto_propuesta: Optional[str] = None
    
    numero_cotizacion: Optional[str] = None
    fecha_registro: Optional[date] = None
    canal: Optional[str] = None
    numero_factura: Optional[str] = None
    fecha_factura: Optional[date] = None
    venta_perdida: Optional[str] = None
    comentarios: Optional[str] = None

class CotizacionResponse(CotizacionBase):
    id: UUID
    vendedor_id: UUID

    class Config:
        from_attributes = True

class CotizacionesAgentResponse(BaseModel):
    total: Decimal
    texto_propuesta: str

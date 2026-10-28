"""Esquemas Pydantic v2 y ejemplos OpenAPI para el módulo de solo lectura /api/v1/bot."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BotErrorResponse(BaseModel):
    detail: str = Field(..., description="Descripción del error.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"detail": "Clave de API ausente o inválida."}
        }
    )


class BotHealthResponse(BaseModel):
    status: str = Field(default="ok", description="Estado operativo del servicio.")
    version: str = Field(default="1.0.0", description="Versión actual de la API.")
    hora_servidor: str = Field(
        ...,
        description="Fecha y hora del servidor en ISO 8601 con zona horaria America/Mazatlan.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "version": "1.0.0",
                "hora_servidor": "2026-10-28T11:16:26-07:00",
            }
        }
    )


class BotVendedorItem(BaseModel):
    id: str = Field(..., description="UUID del vendedor.")
    nombre: str = Field(..., description="Nombre completo del vendedor.")
    email: str = Field(..., description="Correo electrónico del vendedor.")
    telefono: Optional[str] = Field(default=None, description="Teléfono o WhatsApp del vendedor.")
    equipo: Optional[str] = Field(default=None, description="Equipo o código comercial asignado.")
    activo: bool = Field(default=True, description="Indica si el vendedor se encuentra activo.")
    fecha_alta: str = Field(..., description="Fecha de alta en ISO 8601 (America/Mazatlan).")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "11111111-1111-1111-1111-111111111111",
                "nombre": "Lorena Peraza",
                "email": "lorena.peraza@kuroda.com",
                "telefono": "+526677112233",
                "equipo": "C01",
                "activo": True,
                "fecha_alta": "2026-01-15T08:00:00-07:00",
            }
        }
    )


class BotVendedorListResponse(BaseModel):
    total: int = Field(..., ge=0, description="Total de registros que cumplen el filtro.")
    limit: int = Field(..., ge=1, le=500, description="Límite de registros por página.")
    offset: int = Field(..., ge=0, description="Desplazamiento actual.")
    items: list[BotVendedorItem] = Field(default_factory=list)


class BotVendedorResumenMes(BaseModel):
    periodo: str = Field(..., description="Periodo mensual consultado (YYYY-MM).")
    ventas_total: float = Field(..., description="Monto total vendido en el mes actual (MXN).")
    num_ventas: int = Field(..., description="Número de ventas concretadas en el mes actual.")
    num_cotizaciones: int = Field(..., description="Número de cotizaciones registradas en el mes actual.")
    meta_mes: float = Field(..., description="Meta comercial asignada en el mes actual (MXN).")
    avance_pct: float = Field(..., description="Porcentaje de avance sobre la meta del mes.")
    moneda: str = Field(default="MXN", description="Moneda de los importes.")


class BotVendedorDetailResponse(BotVendedorItem):
    ventas_total: float = Field(..., description="Monto total vendido en el mes actual.")
    num_ventas: int = Field(..., description="Cantidad de ventas del mes actual.")
    num_cotizaciones: int = Field(..., description="Cantidad de cotizaciones del mes actual.")
    meta_mes: float = Field(..., description="Meta del mes actual.")
    avance_pct: float = Field(..., description="Porcentaje de avance del mes actual.")
    moneda: str = Field(default="MXN", description="Moneda oficial (MXN).")
    resumen_mes: BotVendedorResumenMes = Field(..., description="Objeto desglosado del resumen mensual.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "11111111-1111-1111-1111-111111111111",
                "nombre": "Lorena Peraza",
                "email": "lorena.peraza@kuroda.com",
                "telefono": "+526677112233",
                "equipo": "C01",
                "activo": True,
                "fecha_alta": "2026-01-15T08:00:00-07:00",
                "ventas_total": 125400.50,
                "num_ventas": 8,
                "num_cotizaciones": 14,
                "meta_mes": 200000.00,
                "avance_pct": 62.70,
                "moneda": "MXN",
                "resumen_mes": {
                    "periodo": "2026-10",
                    "ventas_total": 125400.50,
                    "num_ventas": 8,
                    "num_cotizaciones": 14,
                    "meta_mes": 200000.00,
                    "avance_pct": 62.70,
                    "moneda": "MXN",
                },
            }
        }
    )


class BotPartidaItem(BaseModel):
    producto: str = Field(..., description="Descripción o código del producto/material.")
    codigo_material: Optional[str] = Field(default=None, description="SKU o código de material SAP.")
    cantidad: float = Field(..., description="Cantidad de unidades.")
    precio_unitario: float = Field(..., description="Precio unitario en MXN.")
    importe: float = Field(..., description="Importe total de la partida en MXN.")
    moneda: str = Field(default="MXN", description="Moneda (MXN).")


class BotVentaItem(BaseModel):
    id: str = Field(..., description="Identificador único de la venta.")
    folio: str = Field(..., description="Folio de factura o documento de venta.")
    fecha: str = Field(..., description="Fecha de la venta en ISO 8601 (America/Mazatlan).")
    vendedor_id: Optional[str] = Field(default=None, description="UUID del vendedor.")
    vendedor_nombre: Optional[str] = Field(default=None, description="Nombre del vendedor.")
    cliente_id: Optional[str] = Field(default=None, description="Identificador o número de cliente.")
    cliente_nombre: str = Field(..., description="Nombre del cliente.")
    monto: float = Field(..., description="Monto decimal de la venta.")
    moneda: str = Field(default="MXN", description="Moneda (MXN).")
    estatus: str = Field(default="facturada", description="Estatus de la venta (ej. facturada, pagada).")
    forma_pago: Optional[str] = Field(default=None, description="Forma de pago o canal de entrega.")
    cotizacion_id: Optional[str] = Field(default=None, description="ID de la cotización origen.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "22222222-2222-2222-2222-222222222222",
                "folio": "FAC-1355407435",
                "fecha": "2026-10-12T00:00:00-07:00",
                "vendedor_id": "11111111-1111-1111-1111-111111111111",
                "vendedor_nombre": "Lorena Peraza",
                "cliente_id": "400191",
                "cliente_nombre": "Constructora del Pacífico S.A.",
                "monto": 18500.75,
                "moneda": "MXN",
                "estatus": "facturada",
                "forma_pago": "Pide y Recoge",
                "cotizacion_id": "22222222-2222-2222-2222-222222222222",
            }
        }
    )


class BotVentaListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[BotVentaItem]


class BotVentaDetailResponse(BotVentaItem):
    partidas: list[BotPartidaItem] = Field(default_factory=list, description="Partidas de la venta.")


class BotMetaItem(BaseModel):
    id: str = Field(..., description="UUID de la meta.")
    vendedor_id: Optional[str] = Field(default=None, description="UUID del vendedor.")
    vendedor_nombre: Optional[str] = Field(default=None, description="Nombre del vendedor.")
    periodo: str = Field(..., description="Periodo de la meta en formato YYYY-MM.")
    tipo: str = Field(..., description="Periodicidad: mensual, trimestral o anual.")
    meta_monto: float = Field(..., description="Monto objetivo de la meta.")
    moneda: str = Field(default="MXN", description="Moneda (MXN).")
    meta_unidades: Optional[int] = Field(default=None, description="Meta en unidades si existe.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "33333333-3333-3333-3333-333333333333",
                "vendedor_id": "11111111-1111-1111-1111-111111111111",
                "vendedor_nombre": "Lorena Peraza",
                "periodo": "2026-10",
                "tipo": "mensual",
                "meta_monto": 200000.00,
                "moneda": "MXN",
                "meta_unidades": None,
            }
        }
    )


class BotMetaListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[BotMetaItem]


class BotAvanceVendedorItem(BaseModel):
    vendedor_id: str
    vendedor_nombre: str
    meta_monto: float
    vendido_monto: float
    avance_pct: float
    faltante: float
    num_ventas: int
    num_cotizaciones_abiertas: int
    ultima_venta_fecha: Optional[str] = None
    dias_sin_venta: Optional[int] = None
    moneda: str = "MXN"


class BotAvanceEquipoSummary(BaseModel):
    meta_monto: float
    vendido_monto: float
    avance_pct: float
    faltante: float
    num_ventas: int
    num_cotizaciones_abiertas: int
    ultima_venta_fecha: Optional[str] = None
    dias_sin_venta: Optional[int] = None
    moneda: str = "MXN"


class BotAvanceResponse(BaseModel):
    periodo: str
    moneda: str = "MXN"
    total: int
    limit: int
    offset: int
    equipo: BotAvanceEquipoSummary
    items: list[BotAvanceVendedorItem]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "periodo": "2026-10",
                "moneda": "MXN",
                "total": 3,
                "limit": 100,
                "offset": 0,
                "equipo": {
                    "meta_monto": 600000.00,
                    "vendido_monto": 420000.00,
                    "avance_pct": 70.00,
                    "faltante": 180000.00,
                    "num_ventas": 20,
                    "num_cotizaciones_abiertas": 10,
                    "ultima_venta_fecha": "2026-10-27T00:00:00-07:00",
                    "dias_sin_venta": 1,
                    "moneda": "MXN",
                },
                "items": [
                    {
                        "vendedor_id": "11111111-1111-1111-1111-111111111111",
                        "vendedor_nombre": "Lorena Peraza",
                        "meta_monto": 200000.00,
                        "vendido_monto": 150000.00,
                        "avance_pct": 75.00,
                        "faltante": 50000.00,
                        "num_ventas": 7,
                        "num_cotizaciones_abiertas": 4,
                        "ultima_venta_fecha": "2026-10-27T00:00:00-07:00",
                        "dias_sin_venta": 1,
                        "moneda": "MXN",
                    }
                ],
            }
        }
    )


class BotCotizacionItem(BaseModel):
    id: str
    folio: str
    fecha_emision: Optional[str] = None
    fecha_vencimiento: Optional[str] = None
    vendedor_id: Optional[str] = None
    vendedor_nombre: Optional[str] = None
    cliente_id: Optional[str] = None
    cliente_nombre: str
    monto: float
    moneda: str = "MXN"
    estatus: str = Field(..., description="borrador | enviada | aceptada | rechazada | vencida")
    dias_desde_envio: int
    ultima_actualizacion: Optional[str] = None


class BotCotizacionListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[BotCotizacionItem]


class BotNotaItem(BaseModel):
    id: Optional[str] = None
    tipo: str
    contenido: str
    fecha: Optional[str] = None


class BotCotizacionDetailResponse(BotCotizacionItem):
    partidas: list[BotPartidaItem] = Field(default_factory=list)
    notas: list[BotNotaItem] = Field(default_factory=list)


class BotClienteItem(BaseModel):
    id: str
    nombre: str
    empresa: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    vendedor_id: Optional[str] = None
    fecha_alta: Optional[str] = None


class BotClienteListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[BotClienteItem]


class BotCitaItem(BaseModel):
    id: str
    fecha_hora: str
    vendedor_id: str
    cliente_id: Optional[str] = None
    tipo: str
    estatus: str
    notas: Optional[str] = None


class BotCitaListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[BotCitaItem]


class BotCompromisoItem(BaseModel):
    id: str
    descripcion: str
    vendedor_id: str
    cliente_id: Optional[str] = None
    fecha_compromiso: str
    estatus: str = Field(..., description="pendiente | cumplido | vencido")
    fecha_cumplimiento: Optional[str] = None


class BotCompromisoListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[BotCompromisoItem]

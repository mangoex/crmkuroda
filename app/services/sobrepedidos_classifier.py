from __future__ import annotations

import re
from dataclasses import dataclass


STATUS_GREEN = "Listo / Disponible (Verde)"
STATUS_YELLOW = "En Proceso (Amarillo)"
STATUS_RED = "Requiere Accion (Rojo)"


@dataclass(frozen=True)
class SobrepedidoStatus:
    estado_crm: str
    motivo_estado: str


def clean_text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def classify_sobrepedido(
    estatus_compras: object,
    cantidad_pendiente: float,
    cantidad_disponible_exacta: float = 0.0,
    tiene_coincidencia_factura: bool = False,
    tiene_coincidencia_exacta: bool = False,
) -> SobrepedidoStatus:
    """Classify a VA05 pending line with controlled CRM semaphore rules."""
    comentario = clean_text(estatus_compras)
    comentario_lower = comentario.lower()
    pendiente = float(cantidad_pendiente or 0)
    disponible = float(cantidad_disponible_exacta or 0)

    if tiene_coincidencia_exacta and disponible >= pendiente and pendiente > 0:
        return SobrepedidoStatus(
            STATUS_GREEN,
            "Coincidencia exacta Factura + Codigo en VL06O con cantidad suficiente.",
        )

    if tiene_coincidencia_exacta and disponible > 0:
        return SobrepedidoStatus(
            STATUS_YELLOW,
            "Coincidencia exacta Factura + Codigo en VL06O con disponibilidad parcial.",
        )

    if comentario_lower.startswith("fac") or " factura" in comentario_lower:
        return SobrepedidoStatus(
            STATUS_GREEN,
            "Compras reporta factura de proveedor; se considera listo para seguimiento de entrega.",
        )

    if "sin fecha" in comentario_lower:
        return SobrepedidoStatus(
            STATUS_RED,
            "Back order sin fecha comprometida.",
        )

    if "sin informacion" in comentario_lower or "sin información" in comentario_lower:
        if tiene_coincidencia_factura:
            return SobrepedidoStatus(
                STATUS_YELLOW,
                "La factura aparece en VL06O, pero no coincide el Codigo de esta linea.",
            )
        return SobrepedidoStatus(
            STATUS_RED,
            "Sin informacion de compras y sin evidencia logistica para la linea.",
        )

    if tiene_coincidencia_factura:
        return SobrepedidoStatus(
            STATUS_YELLOW,
            "La factura aparece en VL06O, pero no coincide el Codigo de esta linea.",
        )

    if "back order" in comentario_lower:
        return SobrepedidoStatus(
            STATUS_YELLOW,
            "Back order con seguimiento o fecha aproximada.",
        )

    if "confirmacion" in comentario_lower or "confirmación" in comentario_lower or "confirm" in comentario_lower:
        return SobrepedidoStatus(
            STATUS_YELLOW,
            "Compras reporta confirmacion, pendiente de validar disponibilidad en VL06O.",
        )

    return SobrepedidoStatus(
        STATUS_RED,
        "Sin regla de avance identificada y sin evidencia logistica para la linea.",
    )

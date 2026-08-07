"""Deterministic, pure-Python service that aggregates a client's purchase
history from the existing ``Cotizacion`` data.

All monetary arithmetic uses ``Decimal`` so the results are exact and
reproducible regardless of the caller.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Iterable

from app.services.commercial_analytics import decimal_value, normalize_contact, normalize_text


def build_client_history(
    numero_cliente: str,
    quotes: Iterable[Any],
    *,
    quote_valid_days: int = 30,
    today: date | None = None,
) -> dict[str, Any]:
    """Return a summary + ordered list of operations for *numero_cliente*.

    Parameters
    ----------
    numero_cliente:
        The SAP / ERP customer number to look up.
    quotes:
        An iterable of ``Cotizacion`` model instances (or any duck-typed
        objects that expose the same attributes).
    quote_valid_days:
        Number of days a quote without an invoice is considered *pending*
        before it becomes *expired*.
    today:
        Reference date for age calculations.  Defaults to ``date.today()``.

    Returns
    -------
    dict
        ``{"resumen": {…}, "operaciones": [{…}, …]}``
    """
    today = today or date.today()
    target = normalize_text(numero_cliente)

    matching: list[Any] = []
    for quote in quotes:
        if normalize_text(getattr(quote, "numero_cliente", None)) == target:
            matching.append(quote)

    # Sort chronologically (newest first).
    matching.sort(
        key=lambda q: getattr(q, "fecha_registro", None) or date.min,
        reverse=True,
    )

    total_cotizaciones = len(matching)
    total_facturadas = 0
    total_pendientes = 0
    total_perdidas = 0
    total_expiradas = 0
    importe_cotizado = Decimal("0")
    importe_facturado = Decimal("0")
    cliente_nombre: str | None = None

    operaciones: list[dict[str, Any]] = []

    for quote in matching:
        # Resolve client name from the first non-empty occurrence.
        if not cliente_nombre:
            cliente_nombre = getattr(quote, "cliente_nombre", None)

        cot_total = decimal_value(getattr(quote, "total", 0))
        fac_total = decimal_value(getattr(quote, "importe_facturado", 0))
        importe_cotizado += cot_total

        has_invoice = bool(getattr(quote, "numero_factura", None)) or fac_total > 0
        is_lost = normalize_text(getattr(quote, "venta_perdida", None)) == "SI"

        if has_invoice:
            estado = "Facturado"
            total_facturadas += 1
            importe_facturado += fac_total
        elif is_lost:
            estado = "Venta Perdida"
            total_perdidas += 1
        else:
            reg_date = getattr(quote, "fecha_registro", None)
            if reg_date and (today - reg_date).days > quote_valid_days:
                estado = "Expirada"
                total_expiradas += 1
            else:
                estado = "Pendiente"
                total_pendientes += 1

        contact = normalize_contact(getattr(quote, "datos_contacto", None))

        operaciones.append({
            "cotizacion_id": str(getattr(quote, "id", "")),
            "numero_cotizacion": getattr(quote, "numero_cotizacion", None),
            "fecha_registro": (
                getattr(quote, "fecha_registro").isoformat()
                if getattr(quote, "fecha_registro", None)
                else None
            ),
            "canal": getattr(quote, "canal", None),
            "total_cotizado": float(cot_total),
            "numero_factura": getattr(quote, "numero_factura", None),
            "fecha_factura": (
                getattr(quote, "fecha_factura").isoformat()
                if getattr(quote, "fecha_factura", None)
                else None
            ),
            "importe_facturado": float(fac_total),
            "venta_perdida": getattr(quote, "venta_perdida", None),
            "estado": estado,
            "vendedor_nombre": getattr(quote, "vendedor_nombre", None),
            "contacto": contact,
        })

    return {
        "numero_cliente": numero_cliente,
        "cliente_nombre": cliente_nombre,
        "resumen": {
            "total_cotizaciones": total_cotizaciones,
            "total_facturadas": total_facturadas,
            "total_pendientes": total_pendientes,
            "total_perdidas": total_perdidas,
            "total_expiradas": total_expiradas,
            "importe_cotizado": float(importe_cotizado),
            "importe_facturado": float(importe_facturado),
            "tasa_conversion": (
                round(total_facturadas / total_cotizaciones * 100, 2)
                if total_cotizaciones
                else 0
            ),
        },
        "operaciones": operaciones,
    }

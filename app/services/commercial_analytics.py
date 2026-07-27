from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable, Mapping


CANONICAL_CHANNELS = (
    "Apartados",
    "Kuroda Turbo",
    "Material D",
    "Promociones",
    "Marketplace",
)


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.strip().upper().split())


def normalize_contact(datos_contacto: Mapping[str, Any] | None) -> dict[str, Any]:
    original = dict(datos_contacto or {})
    telefono = str(original.get("telefono") or "").strip() or None
    celular = str(original.get("celular") or "").strip() or None
    email = str(original.get("email") or "").strip() or None
    preferente = celular or telefono
    return {
        **original,
        "email": email,
        "telefono": telefono,
        "celular": celular,
        "contacto_preferente": preferente,
        "tipo_contacto_preferente": "celular" if celular else ("telefono" if telefono else None),
    }


def normalize_channel(raw_value: Any, configured: Mapping[str, str] | None = None) -> str:
    normalized = normalize_text(raw_value)
    configured = configured or {}
    configured_lookup = {normalize_text(key): value for key, value in configured.items()}
    if normalized in configured_lookup:
        return configured_lookup[normalized]

    deterministic_aliases = {
        "APARTADO": "Apartados",
        "APARTADOS": "Apartados",
        "KURODA TURBO": "Kuroda Turbo",
        "TURBO": "Kuroda Turbo",
        "MATERIAL D": "Material D",
        "MATERIAL-D": "Material D",
        "PROMOCION": "Promociones",
        "PROMOCIONES": "Promociones",
        "MARKETPLACE": "Marketplace",
        "MARKET PLACE": "Marketplace",
    }
    return deterministic_aliases.get(normalized, "Sin clasificar")


def decimal_value(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def aggregate_channels(
    quotes: Iterable[Any],
    configured: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for quote in quotes:
        channel = normalize_channel(getattr(quote, "canal", None), configured)
        group = groups.setdefault(
            channel,
            {
                "canal": channel,
                "cotizaciones": 0,
                "operaciones_facturadas": 0,
                "importe_cotizado": Decimal("0"),
                "importe_facturado": Decimal("0"),
            },
        )
        group["cotizaciones"] += 1
        group["importe_cotizado"] += decimal_value(getattr(quote, "total", 0))
        invoice_amount = decimal_value(getattr(quote, "importe_facturado", 0))
        if getattr(quote, "numero_factura", None) or invoice_amount > 0:
            group["operaciones_facturadas"] += 1
            group["importe_facturado"] += invoice_amount

    total_invoiced = sum((g["importe_facturado"] for g in groups.values()), Decimal("0"))
    result = []
    for group in groups.values():
        operations = group["operaciones_facturadas"]
        group["conversion"] = (
            round(operations / group["cotizaciones"] * 100, 2)
            if group["cotizaciones"]
            else 0
        )
        group["ticket_promedio"] = (
            group["importe_facturado"] / operations if operations else Decimal("0")
        )
        group["participacion"] = (
            round(float(group["importe_facturado"] / total_invoiced * 100), 2)
            if total_invoiced
            else 0
        )
        result.append(
            {
                **group,
                "importe_cotizado": float(group["importe_cotizado"]),
                "importe_facturado": float(group["importe_facturado"]),
                "ticket_promedio": float(group["ticket_promedio"]),
            }
        )
    return sorted(result, key=lambda item: item["importe_facturado"], reverse=True)


def aggregate_material_items(
    rows: Iterable[tuple[Any, Any]],
    seller_names: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    seller_names = seller_names or {}
    groups: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for item, quote in rows:
        seller_id = str(getattr(quote, "vendedor_id", "") or "")
        seller_name = (
            getattr(quote, "vendedor_nombre", None)
            or seller_names.get(seller_id)
            or "Asesor sin vincular"
        )
        key = (
            seller_id,
            seller_name,
            getattr(item, "familia", None) or "Sin familia",
            getattr(item, "grupo_materiales", None) or "Sin grupo",
            getattr(item, "codigo_material", None) or "Sin SKU",
        )
        group = groups.setdefault(
            key,
            {
                "vendedor_id": seller_id or None,
                "vendedor": seller_name,
                "familia": key[2],
                "grupo_materiales": key[3],
                "codigo_material": key[4],
                "descripcion": getattr(item, "descripcion", None),
                "cantidad_cotizada": Decimal("0"),
                "importe_cotizado": Decimal("0"),
                "cantidad_facturada": Decimal("0"),
                "importe_facturado": Decimal("0"),
            },
        )
        for field in (
            "cantidad_cotizada",
            "importe_cotizado",
            "cantidad_facturada",
            "importe_facturado",
        ):
            group[field] += decimal_value(getattr(item, field, 0))

    result = []
    for group in groups.values():
        result.append(
            {
                **group,
                "cantidad_cotizada": float(group["cantidad_cotizada"]),
                "importe_cotizado": float(group["importe_cotizado"]),
                "cantidad_facturada": float(group["cantidad_facturada"]),
                "importe_facturado": float(group["importe_facturado"]),
            }
        )
    return sorted(
        result,
        key=lambda item: (
            item["vendedor"],
            item["familia"],
            item["grupo_materiales"],
            -item["importe_facturado"],
        ),
    )


def build_seller_performance(
    sellers: Iterable[Any],
    quotes: Iterable[Any],
    goals: Iterable[Any],
    logs: Iterable[Any],
    today: date,
    quote_valid_days: int = 30,
) -> list[dict[str, Any]]:
    sellers = list(sellers)
    seller_by_name = {
        normalize_text(seller.nombre_completo): seller.id
        for seller in sellers
        if seller.nombre_completo
    }
    quote_groups: dict[Any, list[Any]] = defaultdict(list)
    for quote in quotes:
        resolved_id = quote.vendedor_id or seller_by_name.get(
            normalize_text(quote.vendedor_nombre)
        )
        if resolved_id:
            quote_groups[resolved_id].append(quote)

    goals_by_seller: dict[Any, Decimal] = defaultdict(lambda: Decimal("0"))
    for goal in goals:
        goals_by_seller[goal.vendedor_id] += decimal_value(goal.monto_objetivo)
    logs_by_seller: dict[Any, list[Any]] = defaultdict(list)
    for log in logs:
        logs_by_seller[log.user_id].append(log)

    data = []
    for seller in sellers:
        seller_quotes = quote_groups[seller.id]
        invoiced = [
            quote
            for quote in seller_quotes
            if quote.numero_factura or decimal_value(quote.importe_facturado) > 0
        ]
        invoice_total = sum(
            (decimal_value(quote.importe_facturado) for quote in invoiced),
            Decimal("0"),
        )
        quote_total = sum(
            (decimal_value(quote.total) for quote in seller_quotes),
            Decimal("0"),
        )
        goal = goals_by_seller[seller.id]
        seller_logs = logs_by_seller[seller.id]
        consistency = (
            sum(log.total_points for log in seller_logs) / len(seller_logs)
            if seller_logs
            else 0
        )
        pending = sum(
            1
            for quote in seller_quotes
            if not quote.numero_factura
            and normalize_text(quote.venta_perdida) != "SI"
            and (
                not quote.fecha_registro
                or (today - quote.fecha_registro).days <= quote_valid_days
            )
        )
        data.append(
            {
                "vendedor_id": str(seller.id),
                "codigo_vendedor": seller.codigo_vendedor,
                "vendedor": seller.nombre_completo or seller.email,
                "meta": float(goal),
                "importe_cotizado": float(quote_total),
                "venta_facturada": float(invoice_total),
                "cumplimiento": round(float(invoice_total / goal * 100), 2) if goal else 0,
                "cotizaciones": len(seller_quotes),
                "operaciones_facturadas": len(invoiced),
                "conversion": round(len(invoiced) / len(seller_quotes) * 100, 2)
                if seller_quotes
                else 0,
                "ticket_promedio": float(invoice_total / len(invoiced)) if invoiced else 0,
                "pendientes": pending,
                "consistencia_promedio": round(consistency, 2),
                "ultima_actividad": max((log.date for log in seller_logs), default=None),
            }
        )
    return sorted(data, key=lambda row: row["venta_facturada"], reverse=True)


def promotion_priority(
    quote: Any,
    items: Iterable[Any],
    promotions: Iterable[Any],
    today: date,
    quote_valid_days: int = 30,
) -> dict[str, Any]:
    if getattr(quote, "numero_factura", None):
        return {"tiene_promocion": False, "nivel_prioridad": None, "promociones_coincidentes": []}
    if normalize_text(getattr(quote, "venta_perdida", None)) == "SI":
        return {"tiene_promocion": False, "nivel_prioridad": None, "promociones_coincidentes": []}
    registered = getattr(quote, "fecha_registro", None)
    if registered and (today - registered).days > quote_valid_days:
        return {"tiene_promocion": False, "nivel_prioridad": None, "promociones_coincidentes": []}

    item_codes = {
        normalize_text(getattr(item, "codigo_material", None))
        for item in items
        if normalize_text(getattr(item, "codigo_material", None))
    }
    matches = []
    minimum_days = None
    for promotion in promotions:
        code = normalize_text(getattr(promotion, "codigo_material", None))
        valid_until = getattr(promotion, "valido_hasta", None)
        valid_date = valid_until.date() if isinstance(valid_until, datetime) else valid_until
        if not code or code not in item_codes or not valid_date or valid_date < today:
            continue
        remaining = (valid_date - today).days
        minimum_days = remaining if minimum_days is None else min(minimum_days, remaining)
        matches.append(
            {
                "codigo_material": getattr(promotion, "codigo_material", None),
                "descripcion": getattr(promotion, "descripcion_material", None),
                "precio_promocion": getattr(promotion, "precio_promocion", None),
                "valido_hasta": valid_date.isoformat(),
                "dias_restantes": remaining,
            }
        )

    if not matches:
        return {"tiene_promocion": False, "nivel_prioridad": None, "promociones_coincidentes": []}
    level = "alta" if minimum_days <= 3 else ("media" if minimum_days <= 7 else "normal")
    return {
        "tiene_promocion": True,
        "nivel_prioridad": level,
        "promociones_coincidentes": matches,
    }


def safe_phone_href(value: Any) -> str | None:
    digits = re.sub(r"[^\d+]", "", str(value or ""))
    return digits or None

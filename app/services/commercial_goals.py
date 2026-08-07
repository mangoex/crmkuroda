"""Cálculos deterministas para metas comerciales mensuales."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Iterable

VALID_PERIODS = {"dia", "semana", "mes"}


def decimal_value(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().upper().split())


def month_start(value: date) -> date:
    return value.replace(day=1)


def month_end(value: date) -> date:
    return value.replace(day=monthrange(value.year, value.month)[1])


def period_bounds(reference: date, periodo: str) -> tuple[date, date]:
    if periodo not in VALID_PERIODS:
        raise ValueError("Periodo inválido. Usa dia, semana o mes.")
    if periodo == "dia":
        return reference, reference
    if periodo == "semana":
        start = reference - timedelta(days=reference.weekday())
        return start, start + timedelta(days=6)
    return month_start(reference), month_end(reference)


def month_starts_between(start: date, end: date) -> list[date]:
    current = month_start(start)
    result = []
    while current <= end:
        result.append(current)
        current = (month_end(current) + timedelta(days=1)).replace(day=1)
    return result


def overlap_days(start: date, end: date, range_start: date, range_end: date) -> int:
    overlap_start = max(start, range_start)
    overlap_end = min(end, range_end)
    return max(0, (overlap_end - overlap_start).days + 1)


def prorated_monthly_amount(amount: Any, month: date, start: date, end: date) -> Decimal:
    days = overlap_days(start, end, month_start(month), month_end(month))
    if not days:
        return Decimal("0")
    return decimal_value(amount) * Decimal(days) / Decimal(monthrange(month.year, month.month)[1])


def _goal_matches(goal: Any, tipo: str, vendedor_id: Any = None, sucursal: str | None = None) -> bool:
    if getattr(goal, "tipo", None) != tipo:
        return False
    if tipo == "vendedor":
        return getattr(goal, "vendedor_id", None) == vendedor_id
    if tipo == "sucursal":
        return normalize_text(getattr(goal, "sucursal", None)) == normalize_text(sucursal)
    return True


def commercial_goal_amount(
    goals: Iterable[Any],
    tipo: str,
    start: date,
    end: date,
    *,
    vendedor_id: Any = None,
    sucursal: str | None = None,
) -> tuple[Decimal, bool]:
    """Devuelve monto prorrateado y si existe una meta nueva para el alcance."""
    total = Decimal("0")
    found = False
    for goal in goals:
        if not _goal_matches(goal, tipo, vendedor_id, sucursal):
            continue
        goal_month = month_start(getattr(goal, "mes"))
        amount = prorated_monthly_amount(getattr(goal, "monto_objetivo"), goal_month, start, end)
        if amount or (month_start(start) <= goal_month <= month_start(end)):
            found = True
            total += amount
    return total, found


def legacy_goal_amount(goals: Iterable[Any], seller_id: Any, start: date, end: date) -> Decimal:
    total = Decimal("0")
    for goal in goals:
        if getattr(goal, "vendedor_id", None) != seller_id:
            continue
        goal_start = getattr(goal, "fecha_inicio", None)
        goal_end = getattr(goal, "fecha_limite", None)
        if not goal_start or not goal_end:
            continue
        days = overlap_days(start, end, goal_start, goal_end)
        span = max(1, (goal_end - goal_start).days + 1)
        total += decimal_value(getattr(goal, "monto_objetivo")) * Decimal(days) / Decimal(span)
    return total


def quote_sale_date(quote: Any) -> date | None:
    return getattr(quote, "fecha_registro", None) or getattr(quote, "fecha_factura", None)


def is_invoiced(quote: Any) -> bool:
    return bool(getattr(quote, "numero_factura", None)) or decimal_value(getattr(quote, "importe_facturado", 0)) > 0


def invoice_amount(quote: Any) -> Decimal:
    return decimal_value(getattr(quote, "importe_facturado", 0))


def sales_in_period(quotes: Iterable[Any], start: date, end: date) -> Decimal:
    return sum(
        (
            invoice_amount(quote)
            for quote in quotes
            if is_invoiced(quote)
            and quote_sale_date(quote)
            and start <= quote_sale_date(quote) <= end
        ),
        Decimal("0"),
    )


def build_goals_dashboard(
    sellers: Iterable[Any],
    quotes: Iterable[Any],
    commercial_goals: Iterable[Any],
    legacy_goals: Iterable[Any],
    reference: date,
    periodo: str,
) -> dict[str, Any]:
    start, end = period_bounds(reference, periodo)
    sellers = list(sellers)
    quotes = list(quotes)
    commercial_goals = list(commercial_goals)
    legacy_goals = list(legacy_goals)
    seller_by_name = {
        normalize_text(seller.nombre_completo): seller.id
        for seller in sellers
        if getattr(seller, "nombre_completo", None)
    }
    grouped_quotes: dict[Any, list[Any]] = {seller.id: [] for seller in sellers}
    branches: dict[str, list[Any]] = {}
    for quote in quotes:
        resolved_id = getattr(quote, "vendedor_id", None) or seller_by_name.get(
            normalize_text(getattr(quote, "vendedor_nombre", None))
        )
        if resolved_id in grouped_quotes:
            grouped_quotes[resolved_id].append(quote)
        branch = str(getattr(quote, "organizacion_ventas", None) or "").strip()
        if branch:
            branches.setdefault(branch, []).append(quote)

    general_target, general_configured = commercial_goal_amount(
        commercial_goals, "general", start, end
    )
    seller_rows = []
    for seller in sellers:
        target, configured = commercial_goal_amount(
            commercial_goals, "vendedor", start, end, vendedor_id=seller.id
        )
        if not configured:
            target = legacy_goal_amount(legacy_goals, seller.id, start, end)
        actual = sales_in_period(grouped_quotes.get(seller.id, []), start, end)
        seller_rows.append(
            {
                "vendedor_id": str(seller.id),
                "vendedor": getattr(seller, "nombre_completo", None) or getattr(seller, "email", "Vendedor"),
                "meta": float(target),
                "venta_facturada": float(actual),
                "cumplimiento": round(float(actual / target * 100), 2) if target else 0,
                "origen_meta": "comercial" if configured else ("legada" if target else "sin_meta"),
            }
        )

    goal_branches = {
        str(getattr(goal, "sucursal", None) or "").strip()
        for goal in commercial_goals
        if getattr(goal, "tipo", None) == "sucursal" and getattr(goal, "sucursal", None)
    }
    branch_rows = []
    for branch in sorted(set(branches) | goal_branches, key=normalize_text):
        target, configured = commercial_goal_amount(
            commercial_goals, "sucursal", start, end, sucursal=branch
        )
        actual = sales_in_period(branches.get(branch, []), start, end)
        branch_rows.append(
            {
                "sucursal": branch,
                "meta": float(target),
                "venta_facturada": float(actual),
                "cumplimiento": round(float(actual / target * 100), 2) if target else 0,
                "origen_meta": "comercial" if configured else "sin_meta",
            }
        )

    general_actual = sales_in_period(quotes, start, end)
    return {
        "periodo": {
            "tipo": periodo,
            "fecha_referencia": reference.isoformat(),
            "fecha_inicio": start.isoformat(),
            "fecha_fin": end.isoformat(),
        },
        "general": {
            "meta": float(general_target),
            "venta_facturada": float(general_actual),
            "cumplimiento": round(float(general_actual / general_target * 100), 2) if general_target else 0,
            "origen_meta": "comercial" if general_configured else "sin_meta",
        },
        "vendedores": sorted(seller_rows, key=lambda row: row["venta_facturada"], reverse=True),
        "sucursales": sorted(branch_rows, key=lambda row: row["venta_facturada"], reverse=True),
    }

"""
Menu Service Module - Deterministic calculation and RBAC filtering for CRM Kuroda.
"""

from typing import List, Dict, Any, Optional

# List of all menu sections in default order with allowed roles
ALL_MENU_SECTIONS: List[Dict[str, Any]] = [
    {"id": "summary", "label": "Mi Panel", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "vendedores", "label": "Vendedores", "roles": ["gerente", "admin", "administrador"]},
    {"id": "inventario-abcf", "label": "Inventario D", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "promociones", "label": "Promociones", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "sobrepedidos", "label": "Sobrepedidos", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "por-entregar", "label": "Por entregar", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "cotizaciones", "label": "Cotizaciones", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "seguimiento", "label": "Seguimiento", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "agentes", "label": "Centro de Agentes", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "slight-edge", "label": "La Ventaja", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "asignacion", "label": "Asignación", "roles": ["gerente", "admin", "administrador"]},
    {"id": "api", "label": "Conexión", "roles": ["gerente", "admin", "administrador"]},
]


def normalize_role(role: str) -> str:
    """Normalize user role string."""
    if not role:
        return "vendedor"
    r = str(role).lower().strip()
    if r in ["admin", "administrador"]:
        return "admin"
    if r == "gerente":
        return "gerente"
    return "vendedor"


def get_allowed_sections_for_role(role: str) -> List[str]:
    """
    Returns the list of section IDs allowed for a given user role in default order.
    """
    norm_role = normalize_role(role)
    allowed = []
    for section in ALL_MENU_SECTIONS:
        if norm_role in section["roles"] or ("administrador" in section["roles"] and norm_role == "admin"):
            allowed.append(section["id"])
    return allowed


def calculate_menu_order(role: str, custom_order: Optional[List[str]] = None) -> List[str]:
    """
    Deterministically calculates the final ordered list of section IDs for a given role and optional custom order.
    
    Rules:
    1. Filter out any section IDs not allowed for the user's role.
    2. Maintain user's requested order for allowed sections without duplicates.
    3. Append any allowed sections missing from custom_order at the end, in standard default order.
    """
    allowed_set = set(get_allowed_sections_for_role(role))
    default_order = get_allowed_sections_for_role(role)
    
    if not custom_order:
        return default_order

    result: List[str] = []
    seen = set()

    # Process custom order
    for sec_id in custom_order:
        if isinstance(sec_id, str):
            sec_clean = sec_id.strip()
            if sec_clean in allowed_set and sec_clean not in seen:
                result.append(sec_clean)
                seen.add(sec_clean)

    # Append any allowed sections that were omitted in custom order
    for sec_id in default_order:
        if sec_id not in seen:
            result.append(sec_id)
            seen.add(sec_id)

    return result

"""
Menu Service Module - Deterministic calculation and RBAC filtering for CRM Kuroda.
"""

from typing import List, Dict, Any, Optional

# List of all menu sections in default order with allowed roles
ALL_MENU_SECTIONS: List[Dict[str, Any]] = [
    {"id": "summary", "label": "Mi Panel", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "seguimiento", "label": "Seguimiento", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "cotizaciones", "label": "Cotizaciones", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "promociones", "label": "Promociones", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "inventario-abcf", "label": "Inventario D", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "sobrepedidos", "label": "Sobrepedidos", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "por-entregar", "label": "Por entregar", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "vendedores", "label": "Vendedores", "roles": ["gerente", "admin", "administrador"]},
    {"id": "agentes", "label": "Centro de Agentes", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "slight-edge", "label": "La Ventaja", "roles": ["vendedor", "gerente", "admin", "administrador"]},
    {"id": "asignacion", "label": "Asignación", "roles": ["gerente", "admin", "administrador"]},
    {"id": "api", "label": "API WhatsApp", "roles": ["gerente", "admin", "administrador"]},
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
    Deterministically calculates the final ordered list of section IDs for a given role.
    Menu order is strictly fixed according to the system specification.
    """
    return get_allowed_sections_for_role(role)


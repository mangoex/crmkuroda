"""Helper de jerarquía de vendedores (padre -> hijos, 1 nivel).

Centraliza la resolucion de qué vendedores puede ver un usuario, para que
cada modulo (cotizaciones, sobrepedidos, por_entregar, asignaciones) aplique
el filtro de forma consistente.

Convención:
  - admin/gerente/soporte ven a TODOS los vendedores (sin restricción).
  - Un vendedor sin padre ni hijos se ve solo a sí mismo.
  - Un vendedor-padre se ve a sí mismo + sus hijos directos.

Devuelve DOS listas porque los modulos usan identificadores distintos:
  - ids:        lista de UUID (para cotizaciones/metas/asignaciones).
  - codigos:    lista de strings (para sobrepedidos/por_entregar, que matchean
                por codigo_vendedor contra datos importados de SAP/Excel).
"""
from __future__ import annotations

from typing import List, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario


async def get_vendedores_visibles(
    db: AsyncSession,
    current_user: Usuario,
) -> Tuple[List[UUID], List[str]]:
    """Devuelve (ids, codigos) de los vendedores que current_user puede ver.

    - admin/gerente/soporte: None, None  (señal de "sin restricción": el caller no filtra).
    - vendedor: [propio_id, *hijos_ids], [propio_codigo, *hijos_codigos].
    """
    # Admin/gerente/soporte no tienen restricción por vendedor.
    # Soporte ve todos los registros de sobrepedidos/por-entregar (acceso de
    # solo lectura a esas secciones, sin codigo_vendedor propio).
    if current_user.rol in ("admin", "gerente", "soporte"):
        return None, None

    # Vendedor: propio + hijos directos
    ids: List[UUID] = [current_user.id]
    codigos: List[str] = []
    if current_user.codigo_vendedor:
        codigos.append(current_user.codigo_vendedor)

    res = await db.execute(
        select(Usuario).where(
            Usuario.vendedor_padre_id == current_user.id,
            Usuario.rol == "vendedor",
        )
    )
    for hijo in res.scalars().all():
        ids.append(hijo.id)
        if hijo.codigo_vendedor:
            codigos.append(hijo.codigo_vendedor)

    return ids, codigos


async def get_ids_vendedores_visibles(
    db: AsyncSession,
    current_user: Usuario,
) -> List[UUID] | None:
    """Atajo: solo los UUIDs visibles. None = sin restricción."""
    ids, _ = await get_vendedores_visibles(db, current_user)
    return ids


async def get_codigos_vendedores_visibles(
    db: AsyncSession,
    current_user: Usuario,
) -> List[str] | None:
    """Atajo: solo los códigos visibles. None = sin restricción."""
    _, codigos = await get_vendedores_visibles(db, current_user)
    return codigos


async def get_hijos_ids(db: AsyncSession, padre: Usuario) -> List[UUID]:
    """Lista de IDs de los hijos directos de un vendedor."""
    res = await db.execute(
        select(Usuario.id).where(
            Usuario.vendedor_padre_id == padre.id,
            Usuario.rol == "vendedor",
        )
    )
    return [row[0] for row in res.all()]

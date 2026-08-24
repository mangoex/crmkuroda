from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.por_entregar import PorEntregar
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.services.jerarquia import get_codigos_vendedores_visibles

router = APIRouter()


@router.get("/")
async def list_por_entregar(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = select(PorEntregar)
    if current_user.rol == "vendedor":
        codigos_visibles = await get_codigos_vendedores_visibles(db, current_user)
        if codigos_visibles:
            query = query.filter(PorEntregar.vendedor_codigo.in_(codigos_visibles))
        else:
            query = query.filter(PorEntregar.vendedor_codigo == "__NO_MATCH__")

    result = await db.execute(query)
    records = result.scalars().all()

    # Enriquecer con datos de contacto del catálogo de Clientes
    client_numbers = {r.numero_cliente.strip() for r in records if r.numero_cliente and r.numero_cliente.strip()}
    client_names = {r.cliente_nombre.strip() for r in records if r.cliente_nombre and r.cliente_nombre.strip()}
    clients_by_number = {}
    clients_by_name = {}
    if client_numbers or client_names:
        conditions = []
        if client_numbers:
            conditions.append(Cliente.numero_cliente.in_(client_numbers))
        if client_names:
            conditions.append(Cliente.nombre.in_(client_names))
        catalog_clients = (await db.execute(select(Cliente).where(or_(*conditions)))).scalars().all()
        for cl in catalog_clients:
            if cl.numero_cliente and cl.numero_cliente.strip():
                clients_by_number[cl.numero_cliente.strip()] = cl
            if cl.nombre and cl.nombre.strip():
                clients_by_name[cl.nombre.strip()] = cl

    data = []
    for r in records:
        d = r.to_dict()
        cl = clients_by_number.get(r.numero_cliente.strip() if r.numero_cliente else "") or clients_by_name.get(r.cliente_nombre.strip() if r.cliente_nombre else "")
        tel = (cl.telefono or "").strip() if cl and cl.telefono else None
        cel = (cl.celular or "").strip() if cl and cl.celular else None
        d["contacto"] = {
            "telefono": tel,
            "celular": cel,
            "contacto_preferente": cel or tel,
            "email": (cl.email or "").strip() if cl and cl.email else None,
            "nombre_contacto": (cl.nombre_contacto or "").strip() if cl and cl.nombre_contacto else None,
        }
        data.append(d)

    return {"status": "success", "data": data}

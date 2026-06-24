from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.models.cliente_asignacion import ClienteDisponible, PujaCliente
from app.schemas.asignacion import (
    AsignacionIniciar,
    PujaCrear,
    PujaResolver,
    ClienteDisponibleResponse,
    PujaResponse
)

router = APIRouter()

@router.get("/clientes", response_model=List[ClienteDisponibleResponse])
async def list_clientes(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lists available clients based on user role."""
    if current_user.rol in ["admin", "gerente"]:
        # Managers can see all clients with their related bids
        result = await db.execute(
            select(ClienteDisponible)
            .options(
                selectinload(ClienteDisponible.asignado_vendedor),
                selectinload(ClienteDisponible.pujas).selectinload(PujaCliente.vendedor)
            )
            .order_by(ClienteDisponible.creado_en.desc())
        )
        return result.scalars().all()
    else:
        # Vendedores can see:
        # 1. Clients currently in auction where they are allowed to bid
        # 2. Clients directly assigned to them
        result = await db.execute(
            select(ClienteDisponible)
            .options(
                selectinload(ClienteDisponible.asignado_vendedor),
                selectinload(ClienteDisponible.pujas).selectinload(PujaCliente.vendedor)
            )
            .filter(
                (ClienteDisponible.estado == "en_subasta") | 
                ((ClienteDisponible.estado == "asignado") & (ClienteDisponible.asignado_a == current_user.id))
            )
            .order_by(ClienteDisponible.creado_en.desc())
        )
        all_candidates = result.scalars().all()
        
        # Filter on code-level for JSON sellers_permitidos lists
        filtered = []
        for c in all_candidates:
            if c.estado == "asignado" and c.asignado_a == current_user.id:
                filtered.append(c)
            elif c.estado == "en_subasta" and c.vendedores_permitidos:
                # vendedores_permitidos is a list of stringified UUIDs
                if str(current_user.id) in c.vendedores_permitidos:
                    filtered.append(c)
        return filtered

@router.post("/crear-cliente", response_model=ClienteDisponibleResponse, status_code=status.HTTP_201_CREATED)
async def crear_cliente(
    nombre: str,
    email: str = None,
    telefono: str = None,
    comentarios: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Creates a new available client. Admin/gerente only."""
    if current_user.rol not in ["admin", "gerente"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para crear clientes disponibles."
        )
    
    nuevo_cliente = ClienteDisponible(
        nombre=nombre,
        email=email,
        telefono=telefono,
        comentarios=comentarios,
        estado="disponible"
    )
    db.add(nuevo_cliente)
    await db.commit()
    await db.refresh(nuevo_cliente)
    
    # Reload with relationships
    res = await db.execute(
        select(ClienteDisponible)
        .options(selectinload(ClienteDisponible.asignado_vendedor))
        .filter(ClienteDisponible.id == nuevo_cliente.id)
    )
    return res.scalars().first()

@router.post("/iniciar", status_code=status.HTTP_200_OK)
async def iniciar_asignacion(
    payload: AsignacionIniciar,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Assigns clients directly (if 1 vendor) or places them in auction (if >1 vendors)."""
    if current_user.rol not in ["admin", "gerente"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para iniciar la asignación de clientes."
        )
        
    if not payload.cliente_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes seleccionar al menos un cliente."
        )
        
    if not payload.vendedor_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes seleccionar al menos un vendedor."
        )

    # Verify clients exist and are not already assigned
    cli_res = await db.execute(
        select(ClienteDisponible).filter(ClienteDisponible.id.in_(payload.cliente_ids))
    )
    clientes = cli_res.scalars().all()
    if len(clientes) != len(payload.cliente_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno o más clientes seleccionados no existen."
        )

    # Verify vendors exist
    ven_res = await db.execute(
        select(Usuario).filter(Usuario.id.in_(payload.vendedor_ids))
    )
    vendedores = ven_res.scalars().all()
    if len(vendedores) != len(payload.vendedor_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno o más vendedores seleccionados no existen."
        )

    if len(payload.vendedor_ids) == 1:
        # Direct Assignment
        vendedor_id = payload.vendedor_ids[0]
        for c in clientes:
            c.estado = "asignado"
            c.asignado_a = vendedor_id
            c.vendedores_permitidos = None
        await db.commit()
        return {
            "status": "success",
            "message": f"Se asignaron directamente {len(clientes)} clientes al vendedor seleccionado."
        }
    else:
        # Auction Mode
        vendedores_str_list = [str(vid) for vid in payload.vendedor_ids]
        for c in clientes:
            c.estado = "en_subasta"
            c.asignado_a = None
            c.vendedores_permitidos = vendedores_str_list
            
            # Wipe any previous bids for these clients if re-auctioned
            await db.execute(
                delete(PujaCliente).where(PujaCliente.cliente_id == c.id)
            )
            # SQLAlchemy will cascade delete or we can let cascade option handle it
        await db.commit()
        return {
            "status": "success",
            "message": f"Se colocaron {len(clientes)} clientes en subasta para {len(vendedores)} vendedores."
        }

@router.post("/pujas", response_model=PujaResponse, status_code=status.HTTP_201_CREATED)
async def crear_puja(
    payload: PujaCrear,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Allows a seller to submit a bid reasoning why they should get the client."""
    if current_user.rol != "vendedor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los vendedores pueden pujar por clientes."
        )

    # Get client
    res = await db.execute(
        select(ClienteDisponible).filter(ClienteDisponible.id == payload.cliente_id)
    )
    cliente = res.scalars().first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente especificado no existe."
        )

    if cliente.estado != "en_subasta":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este cliente no se encuentra en subasta."
        )

    if not cliente.vendedores_permitidos or str(current_user.id) not in cliente.vendedores_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes autorización para participar en la subasta de este cliente."
        )

    # Check if vendedor already bid
    existing_res = await db.execute(
        select(PujaCliente).filter(
            PujaCliente.cliente_id == payload.cliente_id,
            PujaCliente.vendedor_id == current_user.id
        )
    )
    if existing_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya te has postulado para este cliente."
        )

    nueva_puja = PujaCliente(
        cliente_id=payload.cliente_id,
        vendedor_id=current_user.id,
        razon=payload.razon,
        estado="pendiente"
    )
    db.add(nueva_puja)
    await db.commit()
    await db.refresh(nueva_puja)

    # Reload with vendedor details
    res_reload = await db.execute(
        select(PujaCliente)
        .options(selectinload(PujaCliente.vendedor))
        .filter(PujaCliente.id == nueva_puja.id)
    )
    return res_reload.scalars().first()

@router.post("/resolver", status_code=status.HTTP_200_OK)
async def resolver_subasta(
    payload: PujaResolver,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Resolves the auction by approving the winning bid and assigning the client."""
    if current_user.rol not in ["admin", "gerente"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para resolver subastas."
        )

    # Get client
    cli_res = await db.execute(
        select(ClienteDisponible).filter(ClienteDisponible.id == payload.cliente_id)
    )
    cliente = cli_res.scalars().first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente especificado no existe."
        )

    if cliente.estado != "en_subasta":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este cliente no se encuentra en subasta activa."
        )

    # Get all bids for this client
    bids_res = await db.execute(
        select(PujaCliente).filter(PujaCliente.cliente_id == payload.cliente_id)
    )
    pujas = bids_res.scalars().all()
    
    winner_bid = None
    for p in pujas:
        if p.id == payload.puja_ganadora_id:
            winner_bid = p
            break

    if not winner_bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La puja ganadora especificada no existe para este cliente."
        )

    # Resolve bids and assign client
    for p in pujas:
        if p.id == winner_bid.id:
            p.estado = "aprobada"
        else:
            p.estado = "rechazada"

    cliente.estado = "asignado"
    cliente.asignado_a = winner_bid.vendedor_id
    cliente.vendedores_permitidos = None

    await db.commit()
    return {
        "status": "success",
        "message": "Subasta resuelta. El cliente ha sido asignado al vendedor ganador."
    }

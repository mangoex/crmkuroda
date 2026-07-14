from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.por_entregar import PorEntregar
from app.models.usuario import Usuario
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
    return {"status": "success", "data": [r.to_dict() for r in records]}

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.actualizacion_datos import ActualizacionDatos
from app.models.usuario import Usuario

router = APIRouter()


@router.get("/")
async def list_actualizaciones_datos(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Devuelve la última actualización compartida de cada fuente de datos."""
    records = (await db.execute(select(ActualizacionDatos))).scalars().all()
    return {
        "status": "success",
        "data": {
            record.tipo: {
                "actualizado_en": record.actualizado_en.isoformat() if record.actualizado_en else None,
                "actualizado_por_id": str(record.actualizado_por_id) if record.actualizado_por_id else None,
            }
            for record in records
        },
    }

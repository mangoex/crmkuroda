from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.actualizacion_datos import ActualizacionDatos


async def registrar_actualizacion_datos(
    db: AsyncSession,
    tipo: str,
    usuario_id: Optional[UUID],
) -> ActualizacionDatos:
    """Registra la actualización exitosa de una fuente de datos."""
    registro = await db.get(ActualizacionDatos, tipo)
    if registro is None:
        registro = ActualizacionDatos(tipo=tipo, actualizado_por_id=usuario_id)
        db.add(registro)
    else:
        registro.actualizado_en = datetime.now(timezone.utc)
        registro.actualizado_por_id = usuario_id
    return registro

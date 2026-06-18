from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.cotizacion import Cotizacion
from app.models.usuario import Usuario
from app.agents.analista_agent import analizar_rendimiento

router = APIRouter()

@router.get("/resumen")
async def obtener_resumen_ejecutivo(db: AsyncSession = Depends(get_db)):
    """
    Endpoint para obtener un resumen ejecutivo (Business Insights) de todas las cotizaciones del mes.
    """
    try:
        # Obtener cotizaciones con los datos de sus vendedores
        result = await db.execute(
            select(Cotizacion).options(selectinload(Cotizacion.vendedor))
        )
        cotizaciones = result.scalars().all()
        
        cotizaciones_dict = []
        for c in cotizaciones:
            cotizaciones_dict.append({
                "vendedor_nombre": c.vendedor.nombre_completo or c.vendedor.email,
                "cliente_nombre": c.cliente_nombre,
                "total": str(c.total),
                "venta_perdida": c.venta_perdida,
                "comentarios": c.comentarios
            })
            
        resumen = await analizar_rendimiento(cotizaciones=cotizaciones_dict, db=db)
        
        return {"status": "success", "resumen_ejecutivo": resumen}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

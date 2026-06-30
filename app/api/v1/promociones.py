from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
import io
import openpyxl

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.promocion import Promocion
from app.models.usuario import Usuario

router = APIRouter()

require_admin = RoleChecker(["admin", "gerente"])

@router.get("/")
async def list_promociones(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Promocion))
    promociones = result.scalars().all()
    return {"status": "success", "data": [p.to_dict() for p in promociones]}

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_promociones(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")
    
    contents = await file.read()
    
    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
        ws = wb.active
        
        # Eliminar promociones anteriores
        await db.execute(delete(Promocion))
        
        rows_added = 0
        
        # Skip header
        iter_rows = ws.iter_rows(min_row=2, values_only=True)
        for row in iter_rows:
            if not row or not row[0]: # Skip empty rows
                continue
                
            promocion = Promocion(
                centro=str(row[0]) if row[0] is not None else None,
                descrip_gpo_materiales=str(row[1]) if row[1] is not None else None,
                indicador_abc=str(row[2]) if row[2] is not None else None,
                codigo_material=str(row[3]) if row[3] is not None else None,
                descripcion_material=str(row[4]) if row[4] is not None else None,
                unidad_medida=str(row[5]) if row[5] is not None else None,
                costo_promedio=float(row[6]) if row[6] is not None else None,
                costo_promedio_moneda=float(row[7]) if row[7] is not None else None,
                costo_estandar=float(row[8]) if row[8] is not None else None,
                precio_promocion=float(row[9]) if row[9] is not None else None,
                moneda=str(row[10]) if row[10] is not None else None,
                valido_hasta=row[11] if row[11] is not None else None, # Assuming it's already a datetime object via openpyxl
                costo_estandar_promocion=float(row[12]) if row[12] is not None else None,
                margen_promocion=float(row[13]) if row[13] is not None else None
            )
            db.add(promocion)
            rows_added += 1
            
        await db.commit()
        return {"status": "success", "message": f"Se han cargado {rows_added} promociones exitosamente."}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {str(e)}")

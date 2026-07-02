from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
import io
import openpyxl

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.inventario_abcf import InventarioAbcf
from app.models.usuario import Usuario

router = APIRouter()

require_admin = RoleChecker(["admin", "gerente"])

@router.get("/")
async def list_inventario(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InventarioAbcf))
    inventarios = result.scalars().all()
    return {"status": "success", "data": [i.to_dict() for i in inventarios]}

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_inventario(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    if not file.filename.endswith(".xlsx") and not file.filename.endswith(".XLSX"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")
    
    contents = await file.read()
    
    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
        # Eliminar inventario anterior
        await db.execute(delete(InventarioAbcf))
        
        rows_added = 0
        
        for ws in wb.worksheets:
            if ws.sheet_state == 'hidden':
                continue
                
            # Skip header
            iter_rows = ws.iter_rows(min_row=2, values_only=True)
            for row in iter_rows:
                if not row or not row[0]: # Skip empty rows
                    continue
                
                # Map columns according to the extracted structure
                try:
                    inv = InventarioAbcf(
                        nombre_centro=str(row[0]) if len(row)>0 and row[0] is not None else None,
                        almacen=str(row[1]) if len(row)>1 and row[1] is not None else None,
                        numero_proveedor=str(row[2]) if len(row)>2 and row[2] is not None else None,
                        nombre_proveedor=str(row[3]) if len(row)>3 and row[3] is not None else None,
                        abc_f=str(row[4]) if len(row)>4 and row[4] is not None else None,
                        codigo_material=str(row[5]) if len(row)>5 and row[5] is not None else None,
                        descripcion_material=str(row[6]) if len(row)>6 and row[6] is not None else None,
                        cantidad_propia=float(row[7]) if len(row)>7 and row[7] is not None else None,
                        existencia_consignacion=float(row[8]) if len(row)>8 and row[8] is not None else None,
                        entregas_pendientes=float(row[9]) if len(row)>9 and row[9] is not None else None,
                        existencia_transito=float(row[10]) if len(row)>10 and row[10] is not None else None,
                        existencia_bloqueada=float(row[11]) if len(row)>11 and row[11] is not None else None,
                        existencia_control_calidad=float(row[12]) if len(row)>12 and row[12] is not None else None,
                        umb=str(row[13]) if len(row)>13 and row[13] is not None else None,
                        costo_promedio_unitario=float(row[14]) if len(row)>14 and row[14] is not None else None,
                        importe_inventario_propio=float(row[15]) if len(row)>15 and row[15] is not None else None,
                        valor_consignacion_proveedor=float(row[16]) if len(row)>16 and row[16] is not None else None,
                        ubicacion=str(row[17]) if len(row)>17 and row[17] is not None else None,
                        grupo_materiales=str(row[18]) if len(row)>18 and row[18] is not None else None,
                        descrip_gpo_materiales=str(row[19]) if len(row)>19 and row[19] is not None else None,
                        codigo_anterior_material=str(row[20]) if len(row)>20 and row[20] is not None else None,
                        abc=str(row[21]) if len(row)>21 and row[21] is not None else None,
                        fecha_ultimo_inventario=str(row[22]) if len(row)>22 and row[22] is not None else None
                    )
                    db.add(inv)
                    rows_added += 1
                except Exception as row_error:
                    print(f"Error parseando fila: {row_error}")
                    continue
            
        await db.commit()
        return {"status": "success", "message": f"Se han cargado {rows_added} registros de inventario exitosamente."}
        
    except Exception as e:
        await db.rollback()
        print(f"Error general procesando archivo de inventario: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {str(e)}")

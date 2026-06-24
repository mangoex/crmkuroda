with open("app/api/v1/cotizaciones.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add imports
imports = """import httpx
import csv
import io
from app.models.company import Company
from app.core.security import RoleChecker
from datetime import datetime

require_admin_or_gerente = RoleChecker(["admin", "gerente"])
"""

content = content.replace("router = APIRouter()", imports + "\nrouter = APIRouter()")

# Add endpoint
endpoint = """
@router.post("/sync-csv", status_code=status.HTTP_200_OK)
async def sync_cotizaciones_csv(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente)
):
    \"\"\"Syncs quotes from Google Drive CSV linked to the company.\"\"\"
    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()
    
    if not company or not company.csv_drive_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se ha configurado la URL del archivo CSV en la pestana de Conexion."
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(company.csv_drive_url, timeout=15.0)
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar el CSV: {str(e)}")

    csv_text = response.text
    reader = csv.DictReader(io.StringIO(csv_text))
    
    synced_count = 0
    for row in reader:
        # Assuming CSV has columns: cliente_nombre, datos_contacto, total, comentarios
        if "cliente_nombre" not in row or not row["cliente_nombre"].strip():
            continue
            
        new_quote = Cotizacion(
            vendedor_id=current_user.id,
            cliente_nombre=row.get("cliente_nombre", "Sin nombre"),
            datos_contacto=row.get("datos_contacto", ""),
            items=[{"nombre": "Sincronizado desde CSV", "cantidad": 1, "precio_unitario": float(row.get("total", 0))}],
            total=float(row.get("total", 0) or 0),
            comentarios=row.get("comentarios", "Importado desde CSV")
        )
        db.add(new_quote)
        synced_count += 1
        
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Sincronizacion exitosa. Se insertaron {synced_count} cotizaciones."
    }
"""

content += endpoint

with open("app/api/v1/cotizaciones.py", "w", encoding="utf-8") as f:
    f.write(content)

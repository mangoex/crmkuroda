from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
import io
import openpyxl
import re
from datetime import datetime

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.sobrepedido import Sobrepedido
from app.models.usuario import Usuario

router = APIRouter()

require_admin_or_gerente = RoleChecker(["admin", "gerente"])

def clean_comment(val):
    if val is None:
        return ""
    s = str(val).strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def parse_date(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    
    # Try DD.MM.YYYY -> YYYY-MM-DD
    match = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', s)
    if match:
        d, m, y = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
    
    # Try other formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s

def find_col_index(headers, patterns):
    for pattern in patterns:
        for idx, h in enumerate(headers):
            if h and re.search(pattern, str(h), re.IGNORECASE):
                return idx
    raise ValueError(f"No se encontró la columna para el patrón {patterns}")

@router.get("/")
async def list_sobrepedidos(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = select(Sobrepedido)
    if current_user.rol == "vendedor":
        query = query.filter(Sobrepedido.vendedor_codigo == current_user.codigo_vendedor)
    
    result = await db.execute(query)
    records = result.scalars().all()
    return {"status": "success", "data": [r.to_dict() for r in records]}

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_sobrepedidos(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente)
):
    if not file.filename.endswith(".xlsx") and not file.filename.endswith(".XLSX"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")
    
    contents = await file.read()
    
    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
        
        # 1. Parse VA05
        if "VA05" not in wb.sheetnames:
            raise HTTPException(status_code=400, detail="No se encontró la pestaña 'VA05' en el archivo Excel")
        va05_ws = wb["VA05"]
        va05_headers = [cell.value for cell in va05_ws[1]]
        
        idx_va05_pedido = find_col_index(va05_headers, [r"numero.*pedido", r"pedido"])
        idx_va05_cliente = find_col_index(va05_headers, [r"nombre.*cliente", r"cliente"])
        idx_va05_vendedor_codigo = find_col_index(va05_headers, [r"^vendedor$"])
        idx_va05_vendedor_nombre = find_col_index(va05_headers, [r"nombre.*vendedor"])
        idx_va05_pendiente = find_col_index(va05_headers, [r"cantidad.*pendiente", r"pendiente"])
        
        va05_data = {}
        for row in va05_ws.iter_rows(min_row=2, values_only=True):
            if not row or row[idx_va05_pedido] is None:
                continue
            try:
                pedido_id = int(row[idx_va05_pedido])
                cant_pendiente = float(row[idx_va05_pendiente]) if row[idx_va05_pendiente] is not None else 0.0
                
                # Filter: only process rows with Cantidad Pendiente > 0
                if cant_pendiente <= 0:
                    continue
                    
                cliente = str(row[idx_va05_cliente]).strip() if row[idx_va05_cliente] is not None else ""
                vendedor_cod = str(row[idx_va05_vendedor_codigo]).strip() if row[idx_va05_vendedor_codigo] is not None else ""
                vendedor_nom = str(row[idx_va05_vendedor_nombre]).strip() if row[idx_va05_vendedor_nombre] is not None else ""
                
                va05_data[pedido_id] = {
                    "cliente_nombre": cliente,
                    "vendedor_codigo": vendedor_cod,
                    "vendedor_nombre": vendedor_nom,
                    "cantidad_pendiente": cant_pendiente
                }
            except Exception as e:
                print(f"Error parsing VA05 row: {e}")
        
        # 2. Parse VL06O (Logistics)
        vl06_pedidos = set()
        if "VL06O" in wb.sheetnames:
            vl06_ws = wb["VL06O"]
            vl06_headers = [cell.value for cell in vl06_ws[1]]
            idx_vl06_pedido = find_col_index(vl06_headers, [r"documento.*modelo", r"modelo"])
            
            for row in vl06_ws.iter_rows(min_row=2, values_only=True):
                if not row or row[idx_vl06_pedido] is None:
                    continue
                try:
                    pedido_id = int(float(row[idx_vl06_pedido]))
                    vl06_pedidos.add(pedido_id)
                except Exception:
                    pass
        
        # 3. Parse SP
        if "SP" not in wb.sheetnames:
            raise HTTPException(status_code=400, detail="No se encontró la pestaña 'SP' en el archivo Excel")
        sp_ws = wb["SP"]
        sp_headers = [cell.value for cell in sp_ws[2]]
        
        idx_sp_pedido = find_col_index(sp_headers, [r"^pedido$"])
        idx_sp_codigo = find_col_index(sp_headers, [r"c.digo", r"^codigo$"])
        idx_sp_desc = find_col_index(sp_headers, [r"descripci.n", r"^descripcion$"])
        idx_sp_dia_pedido = find_col_index(sp_headers, [r"d.a.*pedido", r"dia.*pedido"])
        idx_sp_comentarios = find_col_index(sp_headers, [r"comentarios"])
        idx_sp_proveedor = find_col_index(sp_headers, [r"proveedor"])
        
        # Delete old records
        await db.execute(delete(Sobrepedido))
        
        rows_added = 0
        for row in sp_ws.iter_rows(min_row=3, values_only=True):
            if not row or row[idx_sp_pedido] is None:
                continue
            try:
                pedido_id = int(row[idx_sp_pedido])
                
                # Check if it exists in active VA05 orders
                va05_info = va05_data.get(pedido_id)
                if not va05_info:
                    continue
                
                comentarios = clean_comment(row[idx_sp_comentarios])
                
                # Semaphore Classification
                if pedido_id in vl06_pedidos:
                    estado_crm = "Listo en Almacén (Verde)"
                elif "sin fecha" in comentarios.lower():
                    estado_crm = "Alerta (Rojo)"
                elif any(x in comentarios.lower() for x in ["confirm", "conf", "nº", "no."]):
                    estado_crm = "En Proceso (Amarillo)"
                elif any(x in comentarios.lower() for x in ["fac ", "factura"]):
                    estado_crm = "Listo en Almacén (Verde)"
                else:
                    estado_crm = "Alerta (Rojo)"
                
                sp_rec = Sobrepedido(
                    id_pedido_erp=pedido_id,
                    cliente_nombre=va05_info["cliente_nombre"],
                    vendedor_codigo=va05_info["vendedor_codigo"],
                    vendedor_nombre=va05_info["vendedor_nombre"],
                    producto_sku=str(row[idx_sp_codigo]).strip() if row[idx_sp_codigo] is not None else "",
                    producto_desc=str(row[idx_sp_desc]).strip() if row[idx_sp_desc] is not None else "",
                    cantidad_pendiente=va05_info["cantidad_pendiente"],
                    fecha_pedido=parse_date(row[idx_sp_dia_pedido]),
                    estatus_compras=comentarios,
                    proveedor=str(row[idx_sp_proveedor]).strip() if row[idx_sp_proveedor] is not None else "",
                    estado_crm=estado_crm
                )
                db.add(sp_rec)
                rows_added += 1
            except Exception as e:
                print(f"Error parsing row in SP sheet: {e}")
                continue
        
        await db.commit()
        return {"status": "success", "message": f"Se han cargado {rows_added} registros de sobrepedidos exitosamente."}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {str(e)}")

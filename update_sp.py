import os
import re
import sqlite3
import pandas as pd
from datetime import datetime

db_path = 'crm.db'
excel_path = r"C:\Users\Miguel Gonzalez\Downloads\CRMK\ZVA05VTAS.VL06O.CRM 2.0.xlsx"
if not os.path.exists(excel_path):
    excel_path = "../ZVA05VTAS.VL06O.CRM 2.0.xlsx"
if not os.path.exists(excel_path):
    excel_path = "ZVA05VTAS.VL06O.CRM 2.0.xlsx"

if not os.path.exists(excel_path):
    print(f"Error: No se encontró el archivo de sobrepedidos en {excel_path}")
    exit(1)

print(f"Leyendo archivo Excel: {excel_path}")

# Load sheets
xl = pd.ExcelFile(excel_path)

# 1. Parse VA05
df_va05 = xl.parse("VA05")
df_va05.columns = [str(c).strip() for c in df_va05.columns]

col_va05_pedido = [c for c in df_va05.columns if re.search(r"numero.*pedido", c, re.I) or c.lower() == "pedido"][0]
col_va05_cliente = [c for c in df_va05.columns if re.search(r"nombre.*cliente", c, re.I) or c.lower() == "cliente"][0]
col_va05_vendedor_cod = [c for c in df_va05.columns if c.lower() == "vendedor"][0]
col_va05_vendedor_nom = [c for c in df_va05.columns if re.search(r"nombre.*vendedor", c, re.I)][0]
col_va05_pendiente = [c for c in df_va05.columns if re.search(r"cantidad.*pendiente", c, re.I)][0]

df_va05 = df_va05.dropna(subset=[col_va05_pedido])
df_va05[col_va05_pedido] = df_va05[col_va05_pedido].astype(int)
df_va05[col_va05_pendiente] = pd.to_numeric(df_va05[col_va05_pendiente], errors='coerce').fillna(0.0)

# Filter: Cantidad Pendiente > 0
df_va05 = df_va05[df_va05[col_va05_pendiente] > 0]

va05_clean = df_va05[[col_va05_pedido, col_va05_cliente, col_va05_vendedor_cod, col_va05_vendedor_nom, col_va05_pendiente]].copy()
va05_clean.columns = ['id_pedido_erp', 'cliente_nombre', 'vendedor_codigo', 'vendedor_nombre', 'cantidad_pendiente']
va05_clean = va05_clean.drop_duplicates(subset=['id_pedido_erp'])

# 2. Parse VL06O
vl06_pedidos = set()
if "VL06O" in xl.sheet_names:
    df_vl06 = xl.parse("VL06O")
    df_vl06.columns = [str(c).strip() for c in df_vl06.columns]
    col_vl06_pedido = [c for c in df_vl06.columns if re.search(r"documento.*modelo", c, re.I) or c.lower() == "modelo"][0]
    vl06_pedidos = set(df_vl06[col_vl06_pedido].dropna().astype(float).astype(int))

# 3. Parse SP
df_sp = xl.parse("SP", header=1)
df_sp.columns = [str(c).strip() for c in df_sp.columns]

col_sp_pedido = [c for c in df_sp.columns if c.lower() == "pedido"][0]
col_sp_codigo = [c for c in df_sp.columns if re.search(r"c.digo", c, re.I) or c.lower() == "codigo"][0]
col_sp_desc = [c for c in df_sp.columns if re.search(r"descripci.n", c, re.I) or c.lower() == "descripcion"][0]
col_sp_dia_pedido = [c for c in df_sp.columns if re.search(r"d.a.*pedido", c, re.I) or re.search(r"dia.*pedido", c, re.I)][0]
col_sp_comentarios = [c for c in df_sp.columns if c.lower() == "comentarios"][0]
col_sp_proveedor = [c for c in df_sp.columns if c.lower() == "proveedor"][0]

df_sp = df_sp.dropna(subset=[col_sp_pedido])
df_sp[col_sp_pedido] = df_sp[col_sp_pedido].astype(int)

# Inner Join with VA05
df_merged = pd.merge(df_sp, va05_clean, left_on=col_sp_pedido, right_on='id_pedido_erp', how='inner')

# Clean Comments
def clean_comment(val):
    if pd.isna(val):
        return ""
    s = str(val).strip()
    s = re.sub(r'\s+', ' ', s)
    return s

df_merged['estatus_compras'] = df_merged[col_sp_comentarios].apply(clean_comment)

# Semaphore Classification
def get_estado_crm(row):
    pedido = row['id_pedido_erp']
    comms = row['estatus_compras'].lower()
    
    if pedido in vl06_pedidos:
        return "Listo en Almacén (Verde)"
    elif "sin fecha" in comms:
        return "Alerta (Rojo)"
    elif any(x in comms for x in ["confirm", "conf", "nº", "no."]):
        return "En Proceso (Amarillo)"
    elif any(x in comms for x in ["fac ", "factura"]):
        return "Listo en Almacén (Verde)"
    else:
        return "Alerta (Rojo)"

df_merged['estado_crm'] = df_merged.apply(get_estado_crm, axis=1)

# Format Dates
def parse_date(val):
    if pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    match = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', s)
    if match:
        d, m, y = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return pd.to_datetime(s, format=fmt).strftime("%Y-%m-%d")
        except:
            continue
    return s

df_merged['fecha_pedido'] = df_merged[col_sp_dia_pedido].apply(parse_date)

# Define and clean remaining fields before copying
df_merged['producto_sku'] = df_merged[col_sp_codigo].astype(str).str.strip()
df_merged['producto_desc'] = df_merged[col_sp_desc].astype(str).str.strip()
df_merged['proveedor'] = df_merged[col_sp_proveedor].astype(str).str.strip()
df_merged['fecha_carga'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Select final columns
df_final = df_merged[[
    'id_pedido_erp', 'cliente_nombre', 'vendedor_codigo', 'vendedor_nombre',
    'producto_sku', 'producto_desc', 'cantidad_pendiente', 'fecha_pedido',
    'estatus_compras', 'proveedor', 'estado_crm', 'fecha_carga'
]].copy()

print("Conectando a SQLite...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ensure table exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS sobrepedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pedido_erp INTEGER,
    cliente_nombre TEXT,
    vendedor_codigo TEXT,
    vendedor_nombre TEXT,
    producto_sku TEXT,
    producto_desc TEXT,
    cantidad_pendiente REAL,
    fecha_pedido TEXT,
    estatus_compras TEXT,
    proveedor TEXT,
    estado_crm TEXT,
    fecha_carga DATETIME
)
""")

print("Borrando datos viejos...")
cursor.execute("DELETE FROM sobrepedidos")

print("Insertando nuevos datos...")
df_final.to_sql('sobrepedidos', conn, if_exists='append', index=False)

conn.commit()
conn.close()

print(f"¡Base de datos actualizada con {len(df_final)} registros con éxito!")

import sqlite3
import pandas as pd
from datetime import datetime

db_path = 'crm.db'
excel_path = 'c:/Users/Miguel Gonzalez/Downloads/CRMK/Promociones.xlsx'

print(f"Leyendo archivo Excel: {excel_path}")
df = pd.read_excel(excel_path)
print(f"Se encontraron {len(df)} filas.")

# Mapeo de columnas
col_mapping = {
    'Centro': 'centro',
    'Descrip Gpo Materiales': 'descrip_gpo_materiales',
    'Indicador ABC+Frecuencia de Venta': 'indicador_abc',
    'Codigo Material': 'codigo_material',
    'Descripcion del Material': 'descripcion_material',
    'Unidad de Medida Base': 'unidad_medida',
    'Costo Promedio Unitario': 'costo_promedio',
    'Costo Promedio Unitario Moneda de Venta': 'costo_promedio_moneda',
    'Costo Estandar': 'costo_estandar',
    'Precio Efectivo Promocion': 'precio_promocion',
    'Moneda': 'moneda',
    'Valido hasta Promocion': 'valido_hasta',
    'Costo Estandar Promocion': 'costo_estandar_promocion',
    'Margen Promocion': 'margen_promocion',
    'Proveedor': 'proveedor',
    'Inventario disponible': 'inventario_disponible'
}

df = df.rename(columns=col_mapping)
# Filtrar solo las columnas que importan para la base de datos
db_cols = list(col_mapping.values())
for col in db_cols:
    if col not in df.columns:
        df[col] = None

df = df[db_cols]

# Asegurar tipos
for col in ['costo_promedio', 'costo_promedio_moneda', 'costo_estandar', 'precio_promocion', 'costo_estandar_promocion', 'margen_promocion', 'inventario_disponible']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Manejo de fechas
if 'valido_hasta' in df.columns:
    df['valido_hasta'] = pd.to_datetime(df['valido_hasta'], errors='coerce')

print("Conectando a SQLite...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Actualizar esquema si es necesario
try:
    cursor.execute("ALTER TABLE promociones ADD COLUMN proveedor TEXT")
    print("Columna 'proveedor' añadida.")
except sqlite3.OperationalError:
    pass # Ya existe

try:
    cursor.execute("ALTER TABLE promociones ADD COLUMN inventario_disponible REAL")
    print("Columna 'inventario_disponible' añadida.")
except sqlite3.OperationalError:
    pass # Ya existe

print("Borrando datos viejos...")
cursor.execute("DELETE FROM promociones")

print("Insertando nuevos datos...")
# Usar to_sql para insertar eficientemente. Como la tabla ya existe y tiene 'id' auto incremental,
# es mejor insertar especificando append.
df.to_sql('promociones', conn, if_exists='append', index=False)

conn.commit()
conn.close()

print("¡Base de datos actualizada con éxito!")

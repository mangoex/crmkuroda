import sqlite3
import pandas as pd
from datetime import datetime

import os
import sys

db_path = 'crm.db'
candidate_paths = [
    'c:/Users/Miguel Gonzalez/Downloads/CRMK/Promocion 08.10.2026.xlsx',
    'Promocion 08.10.2026.xlsx',
    'c:/Users/Miguel Gonzalez/Downloads/CRMK/Promociones.xlsx',
    'Promociones.xlsx',
]

excel_path = next((p for p in candidate_paths if os.path.exists(p)), candidate_paths[0])

print(f"Leyendo archivo Excel: {excel_path}")
df = pd.read_excel(excel_path)
print(f"Se encontraron {len(df)} filas.")

# Mapeo de columnas tolerante a ambos formatos (antiguo y nuevo)
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
    'Precio Efectivo de Promocion con IVA': 'precio_promocion',
    'Precio Efectivo Promocion': 'precio_promocion',
    'Moneda': 'moneda',
    'Valido desde Promocion': 'valido_desde',
    'Valido hasta Promocion': 'valido_hasta',
    'Costo Estandar Promocion': 'costo_estandar_promocion',
    'Margen Promocion': 'margen_promocion',
    'Proveedor': 'proveedor',
    'Inventario disponible': 'inventario_disponible'
}

df = df.rename(columns=col_mapping)

# Columnas de destino en la base de datos
db_cols = [
    'centro', 'descrip_gpo_materiales', 'indicador_abc', 'codigo_material',
    'descripcion_material', 'unidad_medida', 'costo_promedio', 'costo_promedio_moneda',
    'costo_estandar', 'precio_promocion', 'moneda', 'valido_desde', 'valido_hasta',
    'costo_estandar_promocion', 'margen_promocion', 'proveedor', 'inventario_disponible'
]

for col in db_cols:
    if col not in df.columns:
        df[col] = None

df = df[db_cols]

# Asegurar tipos
for col in ['costo_promedio', 'costo_promedio_moneda', 'costo_estandar', 'precio_promocion', 'costo_estandar_promocion', 'margen_promocion', 'inventario_disponible']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Manejo de fechas
if 'valido_desde' in df.columns:
    df['valido_desde'] = pd.to_datetime(df['valido_desde'], errors='coerce')
if 'valido_hasta' in df.columns:
    df['valido_hasta'] = pd.to_datetime(df['valido_hasta'], errors='coerce')

# Sanitización comercial: omitir registros corruptos o con precio <= 0
filas_previas = len(df)
df = df[df['precio_promocion'].notnull() & (df['precio_promocion'] > 0)]
descartadas = filas_previas - len(df)
if descartadas > 0:
    print(f"Sanitización: Se descartaron {descartadas} filas con precio nulo o <= 0.")

print(f"Total filas válidas a insertar: {len(df)}")

print("Conectando a SQLite...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Actualizar esquema si es necesario
for col_def in [
    ("proveedor", "TEXT"),
    ("inventario_disponible", "REAL"),
    ("valido_desde", "TIMESTAMP"),
    ("es_relevante", "INTEGER DEFAULT 0")
]:
    try:
        cursor.execute(f"ALTER TABLE promociones ADD COLUMN {col_def[0]} {col_def[1]}")
        print(f"Columna '{col_def[0]}' añadida.")
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

import os
import csv
import asyncio
import logging
from sqlalchemy.future import select
from sqlalchemy import func
from app.core.database import SessionLocal, engine, Base
from app.models.cliente import Cliente

logger = logging.getLogger(__name__)

CSV_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "LISTADO CLIENTES.csv"),
    os.path.join(os.path.dirname(__file__), "LISTADO CLIENTES.csv"),
    "LISTADO CLIENTES.csv",
    "../LISTADO CLIENTES.csv",
]

def find_csv_file():
    for p in CSV_PATHS:
        abs_p = os.path.abspath(p)
        if os.path.exists(abs_p):
            return abs_p
    return None

def clean_val(val):
    if val is None:
        return ""
    val_str = str(val).strip()
    if val_str.lower() in ("nan", "null", "none"):
        return ""
    return val_str

async def seed_clientes_from_csv(force=False):
    csv_file = find_csv_file()
    if not csv_file:
        logger.warning("No se encontró el archivo LISTADO CLIENTES.csv")
        print("No se encontró el archivo LISTADO CLIENTES.csv")
        return 0

    async with SessionLocal() as session:
        if not force:
            count_res = await session.execute(select(func.count(Cliente.id)))
            existing_count = count_res.scalar() or 0
            if existing_count > 0:
                print(f"La base de datos ya contiene {existing_count} clientes. Se omite siembra.")
                return existing_count

        print(f"Cargando clientes desde: {csv_file}")
        
        # Open CSV with cp1252 or latin1 encoding
        records = []
        with open(csv_file, mode="r", encoding="cp1252", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            for row in reader:
                if not row or len(row) < 3:
                    continue
                
                # Column mapping matching CSV order
                # 0: Sociedad, 1: Numero de Cliente, 2: Nombre, 3: RFC, 4: Persona Fisica?, 5: Calle,
                # 6: Numero de, 7: Colonia, 8: Codigo Postal, 9: Poblacion, 10: Estado,
                # 11: Telefono, 12: Celular, 13: Fax, 14: Email
                
                sociedad = clean_val(row[0]) if len(row) > 0 else "MKS"
                numero_cliente = clean_val(row[1]) if len(row) > 1 else ""
                nombre = clean_val(row[2]) if len(row) > 2 else ""
                rfc = clean_val(row[3]) if len(row) > 3 else ""
                tipo_persona_raw = clean_val(row[4]) if len(row) > 4 else ""
                calle = clean_val(row[5]) if len(row) > 5 else ""
                numero_exterior = clean_val(row[6]) if len(row) > 6 else ""
                colonia = clean_val(row[7]) if len(row) > 7 else ""
                codigo_postal = clean_val(row[8]) if len(row) > 8 else ""
                poblacion = clean_val(row[9]) if len(row) > 9 else ""
                estado = clean_val(row[10]) if len(row) > 10 else ""
                telefono = clean_val(row[11]) if len(row) > 11 else ""
                celular = clean_val(row[12]) if len(row) > 12 else ""
                fax = clean_val(row[13]) if len(row) > 13 else ""
                email = clean_val(row[14]) if len(row) > 14 else ""

                if not nombre:
                    continue

                # Format zip code if float representation like 80200.0 or 0.0
                if codigo_postal.endswith(".0"):
                    codigo_postal = codigo_postal[:-2]
                if codigo_postal == "0":
                    codigo_postal = ""

                records.append({
                    "sociedad": sociedad,
                    "numero_cliente": numero_cliente,
                    "nombre": nombre,
                    "rfc": rfc,
                    "tipo_persona": tipo_persona_raw,
                    "calle": calle,
                    "numero_exterior": numero_exterior,
                    "colonia": colonia,
                    "codigo_postal": codigo_postal,
                    "poblacion": poblacion,
                    "estado": estado,
                    "telefono": telefono,
                    "celular": celular,
                    "fax": fax,
                    "email": email,
                })

        print(f"Total registros leídos del CSV: {len(records)}")

        # Bulk insert in batches
        batch_size = 2000
        total_inserted = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            db_objs = [Cliente(**item) for item in batch]
            session.add_all(db_objs)
            await session.commit()
            total_inserted += len(batch)
            print(f"  Insertados {total_inserted} / {len(records)} clientes...")

        print(f"¡Siembra de clientes completada exitosamente! ({total_inserted} registros)")
        return total_inserted

if __name__ == "__main__":
    async def main():
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=[Cliente.__table__]))
        await seed_clientes_from_csv(force=True)

    asyncio.run(main())

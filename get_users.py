import asyncio
from sqlalchemy.future import select
from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.core.security import get_password_hash

async def main():
    async with SessionLocal() as db:
        # Check if admin exists
        res = await db.execute(select(Usuario).filter(Usuario.email == "admin@kuroda.com"))
        admin = res.scalars().first()
        if not admin:
            print("Creando usuario administrador...")
            admin = Usuario(
                email="admin@kuroda.com",
                hashed_password=get_password_hash("admin123"),
                rol="admin",
                nombre_completo="Administrador General"
            )
            db.add(admin)
            await db.commit()
            print("Usuario administrador creado (admin@kuroda.com / admin123)")

        print("\n--- Lista de Usuarios Registrados ---")
        res_users = await db.execute(select(Usuario))
        users = res_users.scalars().all()
        for u in users:
            print(f"- {u.nombre_completo or 'Sin Nombre'} | Rol: {u.rol} | Email: {u.email}")
            
if __name__ == "__main__":
    asyncio.run(main())

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, delete, case
from typing import Optional, List
import csv
import io

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.schemas.cliente import (
    ClienteCreate,
    ClienteUpdate,
    ClienteOut,
    ClientePaginatedOut,
    ClienteFilterOptionsOut,
)

router = APIRouter()

# Allow access to admin, gerente, and vendedor
require_clientes_user = RoleChecker(["admin", "gerente", "vendedor"])
require_admin_or_gerente = RoleChecker(["admin", "gerente"])


@router.get("", response_model=ClientePaginatedOut)
@router.get("/", response_model=ClientePaginatedOut)
async def list_clientes(
    search: Optional[str] = Query(None, description="Búsqueda dinámica por nombre, RFC o número de cliente"),
    tipo_persona: Optional[str] = Query(None, description="Filtro por tipo de persona"),
    colonia: Optional[str] = Query(None, description="Filtro por colonia"),
    poblacion: Optional[str] = Query(None, description="Filtro por población"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(25, ge=1, le=500, description="Registros por página (por defecto 25)"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_clientes_user),
):
    """Obtiene el listado de clientes paginado con búsqueda dinámica y filtros."""
    query = select(Cliente)

    # Base filters
    filters = []

    if search and search.strip():
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Cliente.nombre.ilike(term),
                Cliente.rfc.ilike(term),
                Cliente.numero_cliente.ilike(term),
                Cliente.email.ilike(term),
            )
        )

    if tipo_persona and tipo_persona.strip():
        filters.append(Cliente.tipo_persona.ilike(f"%{tipo_persona.strip()}%"))

    if colonia and colonia.strip():
        filters.append(Cliente.colonia.ilike(f"%{colonia.strip()}%"))

    if poblacion and poblacion.strip():
        filters.append(Cliente.poblacion.ilike(f"%{poblacion.strip()}%"))

    if filters:
        query = query.filter(*filters)

    # Single query to calculate total, total_fisicas, and total_morales matching criteria
    stats_query = select(
        func.count(Cliente.id).label("total"),
        func.coalesce(
            func.sum(
                case(
                    (or_(Cliente.tipo_persona.ilike("%física%"), Cliente.tipo_persona.ilike("%fisica%")), 1),
                    else_=0
                )
            ), 0
        ).label("total_fisicas"),
        func.coalesce(
            func.sum(
                case(
                    (or_(Cliente.tipo_persona.ilike("%jurídica%"), Cliente.tipo_persona.ilike("%juridica%"), Cliente.tipo_persona.ilike("%moral%")), 1),
                    else_=0
                )
            ), 0
        ).label("total_morales"),
    )
    if filters:
        stats_query = stats_query.filter(*filters)

    stats_res = await db.execute(stats_query)
    row_stats = stats_res.first()
    total = row_stats.total if row_stats else 0
    total_fisicas = int(row_stats.total_fisicas) if row_stats else 0
    total_morales = int(row_stats.total_morales) if row_stats else 0

    # Pagination calculation
    offset = (page - 1) * limit
    pages = (total + limit - 1) // limit if total > 0 else 1

    query = query.order_by(Cliente.id.asc()).offset(offset).limit(limit)
    result = await db.execute(query)
    clientes = result.scalars().all()

    return {
        "status": "success",
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "total_fisicas": total_fisicas,
        "total_morales": total_morales,
        "data": [c.to_dict() for c in clientes],
    }


@router.get("/filters", response_model=ClienteFilterOptionsOut)
async def get_filter_options(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_clientes_user),
):
    """Obtiene opciones únicas de tipos de persona, colonias y poblaciones para los filtros."""
    # Unique tipos persona
    q_persona = select(Cliente.tipo_persona).distinct().filter(Cliente.tipo_persona.isnot(None), Cliente.tipo_persona != "").order_by(Cliente.tipo_persona.asc())
    res_persona = await db.execute(q_persona)
    tipos_persona = [p for p in res_persona.scalars().all() if p]

    # Unique colonias (top 200 most common or alphabetical)
    q_colonia = (
        select(Cliente.colonia)
        .filter(Cliente.colonia.isnot(None), Cliente.colonia != "", Cliente.colonia != "1")
        .group_by(Cliente.colonia)
        .order_by(func.count(Cliente.id).desc())
        .limit(200)
    )
    res_colonia = await db.execute(q_colonia)
    colonias = sorted([c for c in res_colonia.scalars().all() if c])

    # Unique poblaciones
    q_poblacion = (
        select(Cliente.poblacion)
        .filter(Cliente.poblacion.isnot(None), Cliente.poblacion != "")
        .group_by(Cliente.poblacion)
        .order_by(func.count(Cliente.id).desc())
        .limit(200)
    )
    res_poblacion = await db.execute(q_poblacion)
    poblaciones = sorted([p for p in res_poblacion.scalars().all() if p])

    return {
        "status": "success",
        "tipos_persona": tipos_persona,
        "colonias": colonias,
        "poblaciones": poblaciones,
    }


@router.get("/{cliente_id}", response_model=ClienteOut)
async def get_cliente(
    cliente_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_clientes_user),
):
    """Obtiene el detalle de un cliente por ID."""
    result = await db.execute(select(Cliente).filter(Cliente.id == cliente_id))
    cliente = result.scalars().first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no fue encontrado.",
        )
    return cliente.to_dict()


@router.post("/", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    payload: ClienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_clientes_user),
):
    """Crea (da de alta) un nuevo cliente en el catálogo."""
    if not payload.nombre or not payload.nombre.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del cliente es obligatorio.",
        )

    nuevo_cliente = Cliente(
        sociedad=payload.sociedad or "MKS",
        numero_cliente=payload.numero_cliente or "",
        nombre=payload.nombre.strip(),
        nombre_contacto=payload.nombre_contacto.strip() if payload.nombre_contacto else "",
        rfc=payload.rfc.strip() if payload.rfc else "",
        tipo_persona=payload.tipo_persona or "Persona física",
        calle=payload.calle or "",
        numero_exterior=payload.numero_exterior or "",
        colonia=payload.colonia or "",
        codigo_postal=payload.codigo_postal or "",
        poblacion=payload.poblacion or "",
        estado=payload.estado or "",
        telefono=payload.telefono or "",
        celular=payload.celular or "",
        fax=payload.fax or "",
        email=payload.email or "",
    )
    db.add(nuevo_cliente)
    await db.commit()
    await db.refresh(nuevo_cliente)
    return nuevo_cliente.to_dict()


@router.put("/{cliente_id}", response_model=ClienteOut)
async def update_cliente(
    cliente_id: int,
    payload: ClienteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_clientes_user),
):
    """Actualiza la información de un cliente existente."""
    result = await db.execute(select(Cliente).filter(Cliente.id == cliente_id))
    cliente = result.scalars().first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no existe.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        if val is not None:
            setattr(cliente, key, val)

    await db.commit()
    await db.refresh(cliente)
    return cliente.to_dict()


@router.delete("/{cliente_id}")
async def delete_cliente(
    cliente_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_clientes_user),
):
    """Elimina un cliente del catálogo."""
    result = await db.execute(select(Cliente).filter(Cliente.id == cliente_id))
    cliente = result.scalars().first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no existe.",
        )

    await db.delete(cliente)
    await db.commit()
    return {"status": "success", "message": f"Cliente '{cliente.nombre}' eliminado con éxito."}


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_clientes_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente),
):
    """Permite importar/actualizar clientes desde un archivo CSV."""
    if not file.filename.endswith(".csv") and not file.filename.endswith(".CSV"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un CSV (.csv)")

    contents = await file.read()
    try:
        decoded = contents.decode("cp1252", errors="replace")
    except Exception:
        decoded = contents.decode("utf-8", errors="replace")

    reader = csv.reader(io.StringIO(decoded))
    header = next(reader, None)

    records = []
    for row in reader:
        if not row or len(row) < 3:
            continue

        nombre = row[2].strip() if len(row) > 2 else ""
        if not nombre:
            continue

        records.append({
            "sociedad": row[0].strip() if len(row) > 0 else "MKS",
            "numero_cliente": row[1].strip() if len(row) > 1 else "",
            "nombre": nombre,
            "rfc": row[3].strip() if len(row) > 3 else "",
            "tipo_persona": row[4].strip() if len(row) > 4 else "Persona física",
            "calle": row[5].strip() if len(row) > 5 else "",
            "numero_exterior": row[6].strip() if len(row) > 6 else "",
            "colonia": row[7].strip() if len(row) > 7 else "",
            "codigo_postal": row[8].strip() if len(row) > 8 else "",
            "poblacion": row[9].strip() if len(row) > 9 else "",
            "estado": row[10].strip() if len(row) > 10 else "",
            "telefono": row[11].strip() if len(row) > 11 else "",
            "celular": row[12].strip() if len(row) > 12 else "",
            "fax": row[13].strip() if len(row) > 13 else "",
            "email": row[14].strip() if len(row) > 14 else "",
        })

    if not records:
        raise HTTPException(status_code=400, detail="El archivo CSV no contiene registros válidos.")

    # Bulk insert
    batch_size = 1000
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        db_objs = [Cliente(**item) for item in batch]
        db.add_all(db_objs)
        await db.commit()

    return {"status": "success", "message": f"Se importaron {len(records)} clientes correctamente."}

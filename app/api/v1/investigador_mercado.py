import logging
from typing import Any, Dict, List, Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.core.config import settings
from app.core.database import get_db
from app.models.inventario_abcf import InventarioAbcf
from app.models.promocion import Promocion
from app.agents.investigador_mercado_agent import (
    investigar_mercado_producto,
    InvestigacionMercadoResult
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ProductoCatalogoDto(BaseModel):
    id: Optional[int] = None
    codigo_material: str
    descripcion_material: str
    precio_venta: float
    costo_promedio: float
    stock_disponible: float
    abc_f: str
    almacen: Optional[str] = None
    origen: str = "inventario"  # "inventario" o "promocion"


class InvestigarRequest(BaseModel):
    codigo_material: str = Field(..., description="Código del material Kuroda")
    descripcion_material: str = Field(..., description="Descripción del producto")
    precio_kuroda: float = Field(..., description="Precio actual de lista Kuroda")
    costo_kuroda: float = Field(..., description="Costo unitario promedio")
    stock_kuroda: float = Field(0.0, description="Existencia actual en inventario")
    abc_f: Optional[str] = Field("B", description="Clasificación ABC+F o D")
    ciudad: str = Field("Culiacán", description="Ciudad objetivo para la investigación")
    estado: str = Field("Sinaloa", description="Estado objetivo para la investigación")
    pais: str = Field("México", description="País objetivo")
    competidores: Optional[List[str]] = Field(None, description="Competidores a priorizar")
    api_key_override: Optional[str] = Field(None, description="API Key opcional de OpenRouter")
    modelo_override: Optional[str] = Field(None, description="Modelo opcional de OpenRouter")


class TestConnectionRequest(BaseModel):
    api_key: Optional[str] = None


@router.get("/productos", response_model=List[ProductoCatalogoDto])
async def buscar_productos_catalogo(
    q: str = Query("", description="Búsqueda por código o descripción"),
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Busca productos en el inventario Kuroda (Inventario D / ABC+F y Promociones)
    para autocompletar en el Agente Investigador de Mercado, incluyendo precio actual, costo y stock.
    """
    query_term = (q or "").strip()
    productos: List[ProductoCatalogoDto] = []
    
    try:
        stmt_inv = select(InventarioAbcf)
        if query_term:
            stmt_inv = stmt_inv.where(
                or_(
                    InventarioAbcf.codigo_material.ilike(f"%{query_term}%"),
                    InventarioAbcf.descripcion_material.ilike(f"%{query_term}%")
                )
            )
        stmt_inv = stmt_inv.limit(limit)
        res_inv = await db.execute(stmt_inv)
        items_inv = res_inv.scalars().all()
        
        for item in items_inv:
            stock = float((item.cantidad_propia or 0.0) + (item.existencia_consignacion or 0.0))
            costo = float(item.costo_promedio_unitario or 0.0)
            # En Kuroda, si no hay un precio de venta fijo en esta tabla, calculamos el precio de lista base con margen estimado
            precio_base = round(costo * 1.38, 2) if costo > 0 else 0.0
            
            productos.append(
                ProductoCatalogoDto(
                    id=item.id,
                    codigo_material=item.codigo_material or "",
                    descripcion_material=item.descripcion_material or "",
                    precio_venta=precio_base,
                    costo_promedio=costo,
                    stock_disponible=stock,
                    abc_f=item.abc_f or item.abc or "B",
                    almacen=item.almacen or item.nombre_centro,
                    origen="inventario"
                )
            )
            
        # Complementar con promociones si aún hay espacio en el límite
        if len(productos) < limit:
            stmt_promo = select(Promocion)
            if query_term:
                stmt_promo = stmt_promo.where(
                    or_(
                        Promocion.codigo_material.ilike(f"%{query_term}%"),
                        Promocion.descripcion_material.ilike(f"%{query_term}%")
                    )
                )
            stmt_promo = stmt_promo.limit(limit - len(productos))
            res_promo = await db.execute(stmt_promo)
            items_promo = res_promo.scalars().all()
            
            codigos_existentes = {p.codigo_material for p in productos}
            for promo in items_promo:
                if promo.codigo_material in codigos_existentes:
                    continue
                costo_p = float(promo.costo_promedio or promo.costo_estandar or 0.0)
                precio_p = float(promo.precio_promocion or (costo_p * 1.30))
                stock_p = float(promo.inventario_disponible or 0.0)
                
                productos.append(
                    ProductoCatalogoDto(
                        id=promo.id,
                        codigo_material=promo.codigo_material or "",
                        descripcion_material=promo.descripcion_material or "",
                        precio_venta=precio_p,
                        costo_promedio=costo_p,
                        stock_disponible=stock_p,
                        abc_f=promo.indicador_abc or "PROMO",
                        almacen=promo.centro,
                        origen="promocion"
                    )
                )
    except Exception as exc:
        logger.error(f"Error al consultar catálogo para investigador de mercado: {exc}")
        # Retornar lista vacía de forma resiliente
        return []
        
    return productos


@router.post("/investigar", response_model=InvestigacionMercadoResult)
async def ejecutar_investigacion_mercado(
    req: InvestigarRequest
):
    """
    Ejecuta el Agente Investigador de Mercado:
    1. Delimita la prospección web a la plaza geográfica (ej. Culiacán, Sinaloa).
    2. Consulta en internet publicaciones, promociones y precios competidores con OpenRouter.
    3. Calcula sugerencia determinista de precio combinando mercado e inventario.
    """
    try:
        resultado = await investigar_mercado_producto(
            codigo_material=req.codigo_material,
            descripcion_material=req.descripcion_material,
            precio_kuroda=req.precio_kuroda,
            costo_kuroda=req.costo_kuroda,
            stock_kuroda=req.stock_kuroda,
            abc_f=req.abc_f,
            ciudad=req.ciudad,
            estado=req.estado,
            pais=req.pais,
            competidores=req.competidores,
            api_key_override=req.api_key_override,
            modelo_override=req.modelo_override
        )
        return resultado
    except Exception as exc:
        logger.error(f"Fallo en investigación de mercado: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante la investigación de mercado: {str(exc)}"
        )


@router.post("/test-connection")
async def test_openrouter_connection(req: TestConnectionRequest):
    """
    Valida la conectividad con la API de OpenRouter usando la API Key provista o la global.
    """
    key_to_test = (req.api_key or "").strip() or settings.OPENROUTER_API_KEY
    if not key_to_test:
        return {
            "status": "error",
            "connected": False,
            "message": "No hay API Key configurada. Por favor introduce una clave de OpenRouter."
        }
    
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {"Authorization": f"Bearer {key_to_test}"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                return {
                    "status": "success",
                    "connected": True,
                    "label": data.get("label", "Clave válida"),
                    "limit": data.get("limit"),
                    "usage": data.get("usage"),
                    "message": "Conexión exitosa con OpenRouter API."
                }
            else:
                return {
                    "status": "error",
                    "connected": False,
                    "message": f"OpenRouter respondió con error (HTTP {resp.status_code}): {resp.text}"
                }
    except Exception as exc:
        return {
            "status": "error",
            "connected": False,
            "message": f"No se pudo contactar a OpenRouter: {str(exc)}"
        }

import os
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
from app.core.security import RoleChecker, get_current_user
from app.models.usuario import Usuario
from app.models.inventario_abcf import InventarioAbcf
from app.models.promocion import Promocion
from app.agents.investigador_mercado_agent import (
    investigar_mercado_producto,
    InvestigacionMercadoResult
)

logger = logging.getLogger(__name__)

require_admin_or_gerente = RoleChecker(["admin", "gerente"])

router = APIRouter(dependencies=[Depends(require_admin_or_gerente)])



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


class SaveGlobalKeyRequest(BaseModel):
    api_key: str = Field(..., description="API Key de OpenRouter a guardar globalmente")


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


@router.get("/status")
async def get_openrouter_status():
    """
    Retorna el estado de disponibilidad de la API Key en el servidor (settings).
    """
    has_system_key = bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.strip())
    return {
        "has_system_key": has_system_key,
        "default_model": settings.OPENROUTER_MODEL,
        "provider": settings.LLM_PROVIDER
    }


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
    user_key = (req.api_key_override or "").strip()
    system_key = (settings.OPENROUTER_API_KEY or "").strip()
    
    if not user_key and not system_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere una API Key de OpenRouter para buscar precios en internet. Por favor introdúcela en la barra superior de conexión."
        )
    
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
            api_key_override=user_key or None,
            modelo_override=req.modelo_override
        )
        return resultado
    except PermissionError as p_err:
        logger.error(f"Error de autenticación OpenRouter: {p_err}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(p_err)
        )
    except ValueError as v_err:
        logger.error(f"Error de validación en OpenRouter: {v_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(v_err)
        )
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
    key_to_test = (req.api_key or "").strip() or (settings.OPENROUTER_API_KEY or "").strip()
    if not key_to_test:
        return {
            "status": "error",
            "connected": False,
            "message": "No hay API Key configurada. Por favor introduce tu clave de OpenRouter."
        }
    
    # Normalizar si el usuario pegó el token incluyendo 'Bearer '
    if key_to_test.lower().startswith("bearer "):
        key_to_test = key_to_test[7:].strip()
    
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
            elif resp.status_code == 401:
                return {
                    "status": "error",
                    "connected": False,
                    "message": "Error 401: La clave de API de OpenRouter no es válida o está revocada."
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


@router.post("/save-global-key")
async def save_global_openrouter_key(req: SaveGlobalKeyRequest):
    """
    Guarda la API Key de OpenRouter de forma global en el servidor para que cualquier
    gerente o usuario pueda utilizar el Investigador de Mercado sin tener que reconfigurarla.
    """
    clean_key = (req.api_key or "").strip()
    if clean_key.lower().startswith("bearer "):
        clean_key = clean_key[7:].strip()
        
    if not clean_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clave de API no puede estar vacía."
        )
        
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {"Authorization": f"Bearer {clean_key}"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"OpenRouter no autorizó la clave (HTTP {resp.status_code}): {resp.text}"
                )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo validar la clave con OpenRouter: {str(exc)}"
        )
        
    # Establecer la clave en la configuración activa en memoria del backend
    settings.OPENROUTER_API_KEY = clean_key
    
    # Intentar guardar en archivo .env para persistencia
    try:
        env_path = os.path.join(os.getcwd(), ".env")
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        found = False
        new_lines = []
        for line in lines:
            if line.startswith("OPENROUTER_API_KEY="):
                new_lines.append(f"OPENROUTER_API_KEY={clean_key}\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"\nOPENROUTER_API_KEY={clean_key}\n")
            
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as exc:
        logger.warning(f"No se pudo actualizar .env localmente: {exc}")
        
    return {
        "status": "success",
        "message": "Clave de OpenRouter configurada exitosamente de forma global en el servidor. Todos los gerentes ya pueden usarla desde cualquier equipo."
    }

import os
import logging
from typing import Any, Dict, List, Optional, Union
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
from app.models.cotizacion_detalle import CotizacionItem
from app.agents.investigador_mercado_agent import (
    investigar_mercado_producto,
    InvestigacionMercadoResult
)

logger = logging.getLogger(__name__)

require_admin_or_gerente = RoleChecker(["admin", "gerente"])

router = APIRouter(dependencies=[Depends(require_admin_or_gerente)])



class ProductoCatalogoDto(BaseModel):
    id: Optional[Union[int, str]] = None
    codigo_material: str
    descripcion_material: str
    precio_venta: float
    costo_promedio: float
    stock_disponible: float
    abc_f: str
    almacen: Optional[str] = None
    origen: str = "inventario"  # "inventario", "promocion", o "cotizacion"
    es_promocion: bool = False
    precio_promocion: Optional[float] = None
    precio_lista: Optional[float] = None
    margen_promocion: Optional[float] = None
    centros_disponibles: List[str] = []


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
    Busca productos en el catálogo de Kuroda fusionando de forma inteligente:
    1. Promociones Activas (con máxima prioridad de precio_promocion y margen real).
    2. Inventario D / ABC+F (reparando costos desde importes y consolidando existencias).
    3. Cotizaciones recientes (para precios reales cotizados si no hay promoción).
    """
    query_term = (q or "").strip()
    productos: List[ProductoCatalogoDto] = []
    
    try:
        # 1. Consultar Inventario ABC+F
        stmt_inv = select(InventarioAbcf)
        if query_term:
            stmt_inv = stmt_inv.where(
                or_(
                    InventarioAbcf.codigo_material.ilike(f"%{query_term}%"),
                    InventarioAbcf.descripcion_material.ilike(f"%{query_term}%")
                )
            )
        stmt_inv = stmt_inv.limit(limit * 3)
        res_inv = await db.execute(stmt_inv)
        items_inv = res_inv.scalars().all()
        
        # 2. Consultar Promociones Activas
        stmt_promo = select(Promocion)
        if query_term:
            stmt_promo = stmt_promo.where(
                or_(
                    Promocion.codigo_material.ilike(f"%{query_term}%"),
                    Promocion.descripcion_material.ilike(f"%{query_term}%")
                )
            )
        stmt_promo = stmt_promo.limit(limit * 3)
        res_promo = await db.execute(stmt_promo)
        items_promo = res_promo.scalars().all()
        
        # Indexar y consolidar Promociones por código de material
        promos_by_code: Dict[str, Dict[str, Any]] = {}
        for promo in items_promo:
            code = (promo.codigo_material or "").strip().upper()
            if not code:
                continue
            cost_p = float(promo.costo_promedio or promo.costo_estandar or 0.0)
            price_p = float(promo.precio_promocion or 0.0)
            stock_p = float(promo.inventario_disponible or 0.0)
            margin_p = float(promo.margen_promocion) if promo.margen_promocion is not None else None
            centro = (promo.centro or "").strip()
            
            if code not in promos_by_code:
                promos_by_code[code] = {
                    "id": promo.id,
                    "codigo_material": promo.codigo_material,
                    "descripcion_material": promo.descripcion_material or "",
                    "precio_promocion": price_p,
                    "costo_promedio": cost_p,
                    "stock_total": stock_p,
                    "margen_promocion": margin_p,
                    "centros": [centro] if centro else [],
                    "indicador_abc": promo.indicador_abc or "PROMO"
                }
            else:
                agg = promos_by_code[code]
                agg["stock_total"] += stock_p
                if centro and centro not in agg["centros"]:
                    agg["centros"].append(centro)
                if price_p > 0 and (agg["precio_promocion"] == 0 or price_p < agg["precio_promocion"]):
                    agg["precio_promocion"] = price_p
                if cost_p > 0 and agg["costo_promedio"] == 0:
                    agg["costo_promedio"] = cost_p
                if margin_p is not None and agg["margen_promocion"] is None:
                    agg["margen_promocion"] = margin_p

        # Indexar y consolidar Inventario ABC+F por código de material
        inv_by_code: Dict[str, Dict[str, Any]] = {}
        for item in items_inv:
            code = (item.codigo_material or "").strip().upper()
            if not code:
                continue
            
            cant = float(item.cantidad_propia or 0.0)
            consig = float(item.existencia_consignacion or 0.0)
            stock_row = cant + consig
            
            c_unit = float(item.costo_promedio_unitario or 0.0)
            imp_propio = float(item.importe_inventario_propio or 0.0)
            val_consig = float(item.valor_consignacion_proveedor or 0.0)
            
            # Recuperación determinista del costo unitario si viene en 0
            if c_unit <= 0.0:
                if imp_propio > 0.0 and cant > 0.0:
                    c_unit = round(imp_propio / cant, 2)
                elif val_consig > 0.0 and consig > 0.0:
                    c_unit = round(val_consig / consig, 2)
                    
            almacen_centro = (item.nombre_centro or item.almacen or "").strip()
            
            if code not in inv_by_code:
                inv_by_code[code] = {
                    "id": item.id,
                    "codigo_material": item.codigo_material,
                    "descripcion_material": item.descripcion_material or "",
                    "costo_promedio": c_unit,
                    "stock_total": stock_row,
                    "abc_f": item.abc_f or item.abc or "B",
                    "almacenes": [almacen_centro] if almacen_centro else []
                }
            else:
                agg = inv_by_code[code]
                agg["stock_total"] += stock_row
                if almacen_centro and almacen_centro not in agg["almacenes"]:
                    agg["almacenes"].append(almacen_centro)
                if c_unit > 0 and agg["costo_promedio"] == 0:
                    agg["costo_promedio"] = c_unit

        # 3. Consultar cotizaciones recientes como fallback de precio real para productos sin promo
        codes_needing_quote = [c for c in inv_by_code.keys() if c not in promos_by_code]
        quote_prices: Dict[str, float] = {}
        if codes_needing_quote:
            try:
                stmt_quotes = select(CotizacionItem).where(
                    CotizacionItem.codigo_material.in_(codes_needing_quote),
                    CotizacionItem.precio_venta > 0
                )
                res_quotes = await db.execute(stmt_quotes)
                for q_item in res_quotes.scalars().all():
                    q_code = (q_item.codigo_material or "").strip().upper()
                    pv = float(q_item.precio_venta or 0.0)
                    if pv > 0 and q_code not in quote_prices:
                        quote_prices[q_code] = pv
            except Exception as q_exc:
                logger.debug(f"Consulta de cotizaciones previas omitida o vacía: {q_exc}")

        # 4. Fusión inteligente priorizando Promociones Activas
        procesados = set()

        # Prioridad 1: Productos con Promoción Activa (existan o no en inventario)
        for code, promo in promos_by_code.items():
            procesados.add(code)
            inv = inv_by_code.get(code)
            
            precio_p = promo["precio_promocion"]
            costo_p = promo["costo_promedio"]
            
            # Enriquecer costo desde inventario si promo no lo tenía
            if costo_p <= 0 and inv and inv["costo_promedio"] > 0:
                costo_p = inv["costo_promedio"]
                
            # Si promo no tenía precio pero se calculó o existe costo
            if precio_p <= 0 and costo_p > 0:
                precio_p = round(costo_p * 1.30, 2)
                
            # Consolidar stock real disponible
            if inv and inv["stock_total"] > 0:
                stock_final = inv["stock_total"]
            else:
                stock_final = promo["stock_total"]
                
            centros = list(dict.fromkeys(promo["centros"] + (inv["almacenes"] if inv else [])))
            abc_clasif = (inv["abc_f"] if inv and inv["abc_f"] else promo["indicador_abc"]) or "D5"
            desc = (promo["descripcion_material"] or (inv["descripcion_material"] if inv else "")).strip()

            productos.append(
                ProductoCatalogoDto(
                    id=promo["id"] or (inv["id"] if inv else None),
                    codigo_material=promo["codigo_material"],
                    descripcion_material=desc,
                    precio_venta=precio_p,
                    costo_promedio=costo_p,
                    stock_disponible=stock_final,
                    abc_f=abc_clasif,
                    almacen=", ".join(centros[:3]) if centros else None,
                    origen="promocion",
                    es_promocion=True,
                    precio_promocion=precio_p,
                    precio_lista=round(costo_p * 1.38, 2) if costo_p > 0 else None,
                    margen_promocion=promo["margen_promocion"],
                    centros_disponibles=centros
                )
            )

        # Prioridad 2: Productos de Inventario sin promoción
        for code, inv in inv_by_code.items():
            if code in procesados:
                continue
            procesados.add(code)
            
            costo_inv = inv["costo_promedio"]
            stock_inv = inv["stock_total"]
            centros = inv["almacenes"]
            
            if code in quote_prices:
                precio_inv = quote_prices[code]
                origen_inv = "cotizacion"
            elif costo_inv > 0:
                precio_inv = round(costo_inv * 1.38, 2)
                origen_inv = "inventario"
            else:
                precio_inv = 0.0
                origen_inv = "inventario"
                
            productos.append(
                ProductoCatalogoDto(
                    id=inv["id"],
                    codigo_material=inv["codigo_material"],
                    descripcion_material=inv["descripcion_material"],
                    precio_venta=precio_inv,
                    costo_promedio=costo_inv,
                    stock_disponible=stock_inv,
                    abc_f=inv["abc_f"] or "B",
                    almacen=", ".join(centros[:3]) if centros else None,
                    origen=origen_inv,
                    es_promocion=False,
                    precio_promocion=None,
                    precio_lista=precio_inv,
                    margen_promocion=None,
                    centros_disponibles=centros
                )
            )

        return productos[:limit]

    except Exception as exc:
        logger.error(f"Error al consultar catálogo para investigador de mercado: {exc}")
        # Retornar lista vacía de forma resiliente
        return []



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
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo de autenticación con el proveedor de IA (OpenRouter): {str(p_err)}"
        )
    except ValueError as v_err:
        logger.error(f"Error de validación en OpenRouter: {v_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(v_err)
        )
    except RuntimeError as r_err:
        logger.error(f"Error de servicio OpenRouter: {r_err}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(r_err)
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

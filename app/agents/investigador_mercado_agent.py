import json
import logging
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


def normalizar_texto(texto: str) -> str:
    """Normaliza un texto quitando acentos, mayúsculas y caracteres especiales."""
    if not texto:
        return ""
    norm = unicodedata.normalize("NFD", str(texto))
    sin_tildes = "".join(ch for ch in norm if unicodedata.category(ch) != "Mn")
    limpio = re.sub(r'[^a-z0-9\s]', ' ', sin_tildes.lower())
    return re.sub(r'\s+', ' ', limpio).strip()



def coincide_nombre_comercial(nombre_tienda: str, competidores_permitidos: List[str]) -> bool:
    """
    Valida de forma estricta y determinista si la tienda encontrada coincide
    con el nombre comercial de alguno de los competidores solicitados.
    
    Criterios Humanio CEO:
    1. Si no hay competidores permitidos o se incluye '__ALL__', retorna True.
    2. Coincidencia directa de subcadena (ej. 'The Home Depot' coincide con 'Home Depot Culiacán').
    3. Coincidencia de tokens clave de la marca (ej. 'Construrama' con 'Materiales Construrama Sinaloa').
    4. Descarta marcas/fabricantes de producto (ej. 'Rotoplas', 'Helvex') o tiendas no solicitadas (ej. 'Bricomark').
    """
    if not competidores_permitidos or "__ALL__" in competidores_permitidos:
        return True
        
    t_norm = normalizar_texto(nombre_tienda)
    if not t_norm:
        return False
        
    # Palabras comunes o genéricas del comercio que no aportan distinción de marca comercial
    stop_words = {
        "de", "del", "la", "el", "los", "las", "en", "y", "sa", "cv", "mx",
        "mexico", "tienda", "tiendas", "ferreteria", "ferreterias", "materiales",
        "distribuidor", "distribuidora", "sucursal", "online", "com", "oficial"
    }
    
    t_tokens = set(tok for tok in t_norm.split() if tok not in stop_words and len(tok) >= 3)
    
    for comp in competidores_permitidos:
        if comp == "__ALL__":
            return True
        c_norm = normalizar_texto(comp)
        if not c_norm:
            continue
            
        # 1. Coincidencia directa de subcadena completa
        if c_norm in t_norm or t_norm in c_norm:
            return True
            
        # 2. Análisis por tokens clave distintivos de la marca comercial
        c_tokens = [tok for tok in c_norm.split() if tok not in stop_words and len(tok) >= 3]
        if not c_tokens:
            continue
            
        # Si todos los tokens clave del competidor están presentes en la tienda encontrada
        # (ej. comp="The Home Depot" -> ["home", "depot"]; tienda="Home Depot México" -> True)
        if all(tok in t_tokens for tok in c_tokens):
            return True
            
        # Para marcas de una sola palabra principal (ej. "Construrama", "Surtidor", "Boxito", "Sodimac")
        if len(c_tokens) == 1 and c_tokens[0] in t_tokens:
            return True
            
        # Si coincide la mayoría de los tokens y hay al menos uno distintivo largo (>= 5 letras)
        coincidentes = [tok for tok in c_tokens if tok in t_tokens]
        if len(coincidentes) >= max(1, len(c_tokens) - 1) and any(len(tok) >= 5 for tok in coincidentes):
            return True
            
    return False


class ItemCompetidor(BaseModel):
    tienda: str = Field(..., description="Nombre del competidor o tienda")
    producto_encontrado: str = Field(..., description="Título o descripción del producto detectado")
    precio: float = Field(..., description="Precio publicado detectado")
    moneda: str = Field("MXN", description="Moneda de la publicación")
    en_promocion: bool = Field(False, description="Indica si cuenta con descuento o promoción activa")
    detalle_promocion: Optional[str] = Field(None, description="Detalle del descuento o promoción")
    url: Optional[str] = Field(None, description="Enlace a la publicación o ficha del competidor")
    disponibilidad_local: Optional[str] = Field(None, description="Disponibilidad o cobertura en la plaza")
    diferencia_vs_kuroda: Optional[float] = Field(None, description="Diferencia monetaria vs Kuroda")
    diferencia_pct_vs_kuroda: Optional[float] = Field(None, description="Diferencia porcentual vs Kuroda")


class InvestigacionMercadoResult(BaseModel):
    codigo_material: str
    descripcion_material: str
    precio_kuroda: float
    costo_kuroda: float
    stock_kuroda: float
    abc_f: Optional[str] = "B"
    plaza: Dict[str, str]
    competidores_consultados: List[str]
    publicaciones: List[ItemCompetidor]
    analisis_precios: Dict[str, Any]
    resumen_plaza: str
    timestamp: str


def calcular_precio_sugerido(
    costo: float,
    precio_kuroda: float,
    stock_actual: float,

    abc_f: Optional[str] = "B",
    precios_competencia: Optional[List[float]] = None,
    margen_minimo_pct: float = 0.12
) -> Dict[str, Any]:
    """
    Algoritmo determinista en Python para cálculo de precio sugerido y métricas de mercado.
    Cumple con el marco Humanio CEO: las matemáticas comerciales y protección de margen son 100% deterministas.
    
    Reglas:
    1. Piso inquebrantable: Costo * (1 + margen_minimo_pct).
    2. Sobrestock / Material D: Estrategia agresiva para acelerar rotación sin violar el costo.
    3. Stock escaso (< 5 pzas) y mercado alto: Maximizar margen o preservar inventario.
    4. Stock equilibrado: Ajuste competitivo al promedio de la plaza.
    """
    costo = float(costo or 0.0)
    precio_kuroda = float(precio_kuroda or 0.0)
    stock_actual = float(stock_actual or 0.0)
    clasificacion = (abc_f or "B").strip().upper()
    precios_validos = [float(p) for p in (precios_competencia or []) if float(p) > 0]
    
    piso_costo = round(costo * (1.0 + margen_minimo_pct), 2)
    
    if not precios_validos:
        precio_sug = max(precio_kuroda, piso_costo)
        margen_sug = round((precio_sug - costo) / costo, 4) if costo > 0 else 0.0
        return {
            "precio_sugerido": round(precio_sug, 2),
            "margen_sugerido_pct": margen_sug,
            "precio_minimo_mercado": precio_kuroda,
            "precio_promedio_mercado": precio_kuroda,
            "precio_maximo_mercado": precio_kuroda,
            "brecha_vs_minimo_pct": 0.0,
            "brecha_vs_promedio_pct": 0.0,
            "estrategia": "PRESERVAR_PRECIO_ACTUAL",
            "justificacion": f"Sin referencias de competencia verificadas en la plaza. Se mantiene precio de lista de ${precio_kuroda:.2f} protegiendo un margen del {margen_sug * 100:.1f}% sobre costo."
        }
    
    precio_min = min(precios_validos)
    precio_max = max(precios_validos)
    precio_prom = round(sum(precios_validos) / len(precios_validos), 2)
    
    brecha_vs_min = round(((precio_kuroda - precio_min) / precio_min) * 100, 2) if precio_min > 0 else 0.0
    brecha_vs_prom = round(((precio_kuroda - precio_prom) / precio_prom) * 100, 2) if precio_prom > 0 else 0.0
    
    # 1. Caso: Material D / Sobrestock (alta acumulación de inventario)
    es_sobrestock = (clasificacion == "D") or (stock_actual >= 100 and clasificacion in ("C", "D", "F"))
    
    if es_sobrestock:
        estrategia = "LIQUIDACION_VOLUMEN"
        # Tratar de ganar o igualar el mejor precio de la plaza sin romper el piso de costo
        objetivo_mercado = round(precio_min * 0.99, 2)
        precio_sug = max(piso_costo, objetivo_mercado)
        
        if precio_sug == piso_costo and objetivo_mercado < piso_costo:
            justificacion = (
                f"Al ser Material {clasificacion} con sobrestock ({int(stock_actual)} pzas), se requiere rotación rápida. "
                f"La competencia más baja está en ${precio_min:.2f}, pero por protección de margen mínimo ({margen_minimo_pct*100:.0f}%), "
                f"el piso recomendado es ${precio_sug:.2f} sobre un costo de ${costo:.2f}."
            )
        else:
            justificacion = (
                f"Inventario en sobrestock/Material {clasificacion} ({int(stock_actual)} pzas). "
                f"Se sugiere precio competitivo de ${precio_sug:.2f} (1% por debajo de la mejor opción del mercado de ${precio_min:.2f}) "
                f"para acelerar la liquidación protegiendo la rentabilidad neta."
            )
    
    # 2. Caso: Stock Crítico / Escaso (< 5 pzas)
    elif stock_actual <= 5 and clasificacion in ("A", "B"):
        if precio_prom > precio_kuroda:
            estrategia = "MAXIMIZAR_MARGEN"
            precio_sug = round(min(precio_prom, precio_kuroda * 1.12), 2)
            justificacion = (
                f"Stock crítico ({int(stock_actual)} pzas) y el mercado local promedia ${precio_prom:.2f} (por encima de Kuroda). "
                f"Se sugiere capturar mayor margen ajustando a ${precio_sug:.2f} mientras se reabastece el centro de distribución."
            )
        else:
            estrategia = "PRESERVAR_STOCK"
            precio_sug = max(precio_kuroda, piso_costo)
            justificacion = (
                f"Stock limitado ({int(stock_actual)} pzas). Se recomienda mantener precio de lista actual de ${precio_sug:.2f} "
                f"para preservar inventario para clientes recurrentes."
            )
            
    # 3. Caso Estándar: Nivel de inventario regular
    else:
        if precio_kuroda > precio_prom:
            estrategia = "ALINEACION_COMPETITIVA"
            objetivo = round(precio_prom * 0.985, 2)
            if objetivo < piso_costo:
                precio_sug = piso_costo
                justificacion = (
                    f"El mercado local promedia ${precio_prom:.2f}, pero por regla estricta de protección de margen mínimo ({margen_minimo_pct*100:.0f}%), "
                    f"el precio sugerido se fija en el piso de costo de ${piso_costo:.2f} (costo base: ${costo:.2f})."
                )
            else:
                precio_sug = objetivo
                justificacion = (
                    f"Kuroda está {brecha_vs_prom:+.1f}% arriba del promedio de la plaza (${precio_prom:.2f}). "
                    f"Se sugiere alinear el precio a ${precio_sug:.2f} para incrementar la tasa de conversión, manteniendo un margen del {((precio_sug-costo)/costo)*100:.1f}% sobre costo."
                )
        else:
            estrategia = "LIDER_EN_PRECIO"
            precio_sug = max(precio_kuroda, piso_costo)
            justificacion = (
                f"Kuroda mantiene una posición competitiva ventajosa ({brecha_vs_prom:+.1f}% vs promedio de plaza). "
                f"Se recomienda mantener el precio de ${precio_sug:.2f} y destacar disponibilidad y entrega inmediata."
            )
            
    # Blindaje final de margen
    if precio_sug < piso_costo:
        precio_sug = piso_costo
        justificacion += f" (Ajustado por protección de margen mínimo al piso de costo de ${piso_costo:.2f})."
        
    margen_sug = round((precio_sug - costo) / costo, 4) if costo > 0 else 0.0
    
    return {
        "precio_sugerido": round(precio_sug, 2),
        "margen_sugerido_pct": margen_sug,
        "precio_minimo_mercado": round(precio_min, 2),
        "precio_promedio_mercado": round(precio_prom, 2),
        "precio_maximo_mercado": round(precio_max, 2),
        "brecha_vs_minimo_pct": brecha_vs_min,
        "brecha_vs_promedio_pct": brecha_vs_prom,
        "estrategia": estrategia,
        "justificacion": justificacion
    }


async def call_llm_openrouter_web(
    prompt: str,
    system_instruction: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout: float = 60.0
) -> str:
    """
    Realiza una petición a OpenRouter activando la capacidad de navegación y búsqueda web.
    Permite el uso de API key del usuario o la configurada globalmente en settings.
    """
    resolved_key = (api_key or "").strip() or (settings.OPENROUTER_API_KEY or "").strip()
    if not resolved_key or resolved_key.lower() in ("null", "undefined", "none", '""', "''"):
        raise ValueError("No se ha configurado la API Key de OpenRouter. Por favor introduce tu clave de OpenRouter en la barra superior.")
    
    # Normalizar si el usuario pegó el token incluyendo 'Bearer '
    if resolved_key.lower().startswith("bearer "):
        resolved_key = resolved_key[7:].strip()

    # Modelo predeterminado para búsqueda web
    # Perplexity sonar o GPT-4o-mini con capacidad web
    resolved_model = (model or "").strip() or settings.OPENROUTER_MODEL
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {resolved_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://kuroda.com",
        "X-Title": "CRM Kuroda Inteligente"
    }
    
    # Herramienta server-side moderna de OpenRouter para navegación web en tiempo real
    payload: Dict[str, Any] = {
        "model": resolved_model,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "tools": [
            {
                "type": "openrouter:web_search",
                "parameters": {
                    "max_results": 10
                }
            }
        ]
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload, headers=headers)
        
        # Fallback a plugins legacy si el modelo específico no acepta tools
        if response.status_code == 400 and "tool" in response.text.lower():
            logger.info("Reintentando petición a OpenRouter con plugin web legacy...")
            fallback_payload = {
                "model": resolved_model,
                "messages": payload["messages"],
                "plugins": [{"id": "web"}]
            }
            response = await client.post(url, json=fallback_payload, headers=headers)
            
        if response.status_code == 401:
            logger.error(f"Error OpenRouter Web API 401: {response.text}")
            raise PermissionError("Error de autenticación con OpenRouter (401): La clave de API es inválida o no está autorizada.")
        elif response.status_code == 402:
            logger.error(f"Error OpenRouter Web API 402: {response.text}")
            raise RuntimeError("Error de créditos en OpenRouter (402): Saldo insuficiente de créditos en tu cuenta de OpenRouter.")
        elif response.status_code == 429:
            logger.error(f"Error OpenRouter Web API 429: {response.text}")
            raise RuntimeError("Límite de solicitudes alcanzado en OpenRouter (429). Por favor espera un momento.")
        elif response.status_code != 200:
            logger.error(f"Error OpenRouter Web API: status={response.status_code} body={response.text}")
            raise RuntimeError(f"Error de OpenRouter ({response.status_code}): {response.text}")
        
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("OpenRouter no devolvió opciones de respuesta.")
        return choices[0].get("message", {}).get("content", "")


async def investigar_mercado_producto(
    codigo_material: str,
    descripcion_material: str,
    precio_kuroda: float,
    costo_kuroda: float,
    stock_kuroda: float,
    abc_f: Optional[str] = "B",
    ciudad: str = "Culiacán",
    estado: str = "Sinaloa",
    pais: str = "México",
    competidores: Optional[List[str]] = None,
    api_key_override: Optional[str] = None,
    modelo_override: Optional[str] = None
) -> InvestigacionMercadoResult:
    """
    Orquesta la investigación de mercado para un producto en una plaza geográfica determinada.
    1. Delimita la consulta con la plaza geográfica (Ciudad, Estado, País) y competidores.
    2. Consulta en internet a través de OpenRouter con web search.
    3. Extrae las publicaciones y precios estructurados.
    4. Ejecuta el algoritmo determinista en Python para precios sugeridos e inventario.
    """
    # Separar competidores específicos y flag de búsqueda abierta
    raw_competidores = [c.strip() for c in (competidores or []) if c.strip()]
    buscar_en_toda_la_web = ("__ALL__" in raw_competidores) or (not raw_competidores)
    competidores_prioritarios = [c for c in raw_competidores if c != "__ALL__"]
    
    if not competidores_prioritarios and not buscar_en_toda_la_web:
        competidores_prioritarios = ["The Home Depot", "Construrama", "Plomería Universal", "El Surtidor"]
        
    if competidores_prioritarios and not buscar_en_toda_la_web:
        comp_directriz = (
            f"CONDICIÓN ESTRICTA DE COMPETIDORES: "
            f"Debes auditar y reportar EXCLUSIVAMENTE los precios de las siguientes tiendas y competidores por su NOMBRE COMERCIAL: "
            f"{', '.join(competidores_prioritarios)}. "
            f"ESTÁ ESTRICTAMENTE PROHIBIDO incluir proveedores no solicitados, tiendas ajenas a esta lista o marcas/fabricantes del producto "
            f"(ej. marcas como Rotoplas, Helvex, Urrea NO son tiendas distribuidoras a menos que se listen explícitamente). "
            f"Solo reporta publicaciones donde la tienda vendedora coincida con los nombres comerciales indicados con cobertura en {ciudad}, {estado}."
        )
    elif competidores_prioritarios and buscar_en_toda_la_web:
        comp_directriz = (
            f"Prioriza auditar las tiendas sugeridas: {', '.join(competidores_prioritarios)}. "
            f"Sin embargo, también puedes incluir otros distribuidores o ferreterías con cobertura o envío a {ciudad}, {estado}."
        )
    else:
        comp_directriz = (
            f"Rastrea en toda la web en cualquier tienda, proveedor, ferretería o distribuidor con cobertura "
            f"en {ciudad}, {estado} (ej. The Home Depot, Construrama, Plomería Universal, El Surtidor, etc.)."
        )
        
    system_instruction = (
        "Eres un Agente Investigador de Mercado experto en el sector de plomería, materiales de construcción, "
        "tuberías, grifería y acabados en México. Tu labor es buscar activamente en internet precios, publicaciones "
        "y promociones vigentes de productos específicos en una zona geográfica delimitada.\n\n"
        "REGLAS OBLIGATORIAS:\n"
        f"1. PLAZA GEOGRÁFICA ESTRICTA: Debes enfocar la investigación exclusivamente en la plaza geográfica indicada: {ciudad}, {estado}, {pais}. "
        f"Descarta cualquier tienda o precio de otras regiones sin cobertura física o envío verificado a {ciudad}.\n"
        "2. CONDICIÓN ESTRICTA DE COMPETIDORES: Si se especifican competidores, debes buscar el nombre comercial "
        "de esos competidores específicos y considerar ÚNICAMENTE sus coincidencias comerciales. NO reportes tiendas no solicitadas ni utilices la marca del producto como tienda vendedora.\n"
        "3. EXCLUSIÓN DE PRODUCTOS SIN PRECIO O SIN INVENTARIO: Si un proveedor o tienda no tiene el producto disponible, "
        "está agotado o no publica un precio de venta numérico mayor a cero, NO LO INCLUYAS en la lista de publicaciones. "
        "Bajo ninguna circunstancia devuelvas precios en 0.00 o null. Solo reporta ofertas reales con precio > 0.\n"
        "4. Debes responder EXCLUSIVAMENTE en formato JSON válido, sin bloques de texto explicativo fuera del JSON.\n"
        "5. Estructura JSON esperada:\n"
        "{\n"
        '  "publicaciones": [\n'
        "    {\n"
        '      "tienda": "Nombre comercial del competidor o tienda",\n'
        '      "producto_encontrado": "Nombre exacto del producto encontrado",\n'
        '      "precio": 123.45,\n'
        '      "moneda": "MXN",\n'
        '      "en_promocion": true,\n'
        '      "detalle_promocion": "Ej. 10% de descuento o Ninguno",\n'
        '      "url": "https://...",\n'
        '      "disponibilidad_local": "En tienda local / Envío a domicilio en 24h"\n'
        "    }\n"
        "  ],\n"
        '  "resumen_plaza": "Breve resumen de la dinámica de precios encontrada en esta plaza geográfica."\n'
        "}"
    )
    
    prompt = (
        f"INVESTIGACIÓN DE MERCADO Y PROVEEDORES EN LA PLAZA:\n"
        f"- Producto de referencia Kuroda: {descripcion_material} (Código: {codigo_material})\n"
        f"- Precio actual de lista en Kuroda: ${precio_kuroda:.2f} MXN\n"
        f"- Plaza geográfica objetivo: {ciudad}, {estado}, {pais}\n"
        f"- Directriz de proveedores: {comp_directriz}\n\n"
        f"Realiza la búsqueda web para encontrar precios actuales de este producto o equivalentes directos de la misma marca/especificación "
        f"en {ciudad}, {estado}. Devuelve los resultados encontrados en el formato JSON solicitado sin incluir proveedores que no tengan precio o tengan precio 0."
    )
    
    publicaciones_items: List[ItemCompetidor] = []
    resumen_plaza = ""
    
    try:
        raw_text = await call_llm_openrouter_web(
            prompt=prompt,
            system_instruction=system_instruction,
            api_key=api_key_override,
            model=modelo_override
        )
        
        # Extracción robusta de JSON (tolerante a preámbulo o bloques de código markdown)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
        if json_match:
            clean_json = json_match.group(1).strip()
        else:
            json_match = re.search(r'(\{[\s\S]*\})', raw_text)
            clean_json = json_match.group(1).strip() if json_match else raw_text.strip()
            
        parsed = json.loads(clean_json)
        resumen_plaza = parsed.get("resumen_plaza", f"Investigación realizada en plaza {ciudad}, {estado}.")
        
        for pub in parsed.get("publicaciones", []):
            try:
                p_val = float(pub.get("precio", 0.0) or 0.0)
            except (ValueError, TypeError):
                p_val = 0.0
                
            # Omitir cualquier proveedor que no tenga precio o esté en 0 (sin inventario / no encontrado)
            if p_val <= 0:
                continue
                
            tienda_nombre = str(pub.get("tienda", "Competidor local")).strip()
            
            # FILTRADO DETERMINISTA ESTRICTO DE COMPETIDORES:
            # Si no es búsqueda abierta y hay competidores prioritarios, validar coincidencia comercial estricta
            if competidores_prioritarios and not buscar_en_toda_la_web:
                if not coincide_nombre_comercial(tienda_nombre, competidores_prioritarios):
                    logger.info(
                        f"Descartando tienda '{tienda_nombre}' por no coincidir estrictamente con competidores permitidos: {competidores_prioritarios}"
                    )
                    continue
                
            dif_abs = round(precio_kuroda - p_val, 2)
            dif_pct = round(((precio_kuroda - p_val) / p_val) * 100, 2) if p_val > 0 else 0.0
            
            publicaciones_items.append(
                ItemCompetidor(
                    tienda=tienda_nombre,
                    producto_encontrado=pub.get("producto_encontrado", descripcion_material),
                    precio=p_val,
                    moneda=pub.get("moneda", "MXN"),
                    en_promocion=bool(pub.get("en_promocion", False)),
                    detalle_promocion=pub.get("detalle_promocion"),
                    url=pub.get("url"),
                    disponibilidad_local=pub.get("disponibilidad_local", f"Cobertura en {ciudad}"),
                    diferencia_vs_kuroda=dif_abs,
                    diferencia_pct_vs_kuroda=dif_pct
                )
            )
            
    except (ValueError, PermissionError) as auth_err:
        logger.error(f"Fallo de credenciales o autenticación OpenRouter: {auth_err}")
        raise auth_err
    except Exception as exc:
        logger.warning(f"No se pudo completar búsqueda online en tiempo real: {exc}. Generando análisis de referencia.")
        resumen_plaza = f"Investigación en plaza {ciudad}, {estado} (Modo referencia: la búsqueda online reportó '{str(exc)[:120]}')."
        # Fallback de seguridad si no hay respuesta de OpenRouter
        publicaciones_items = []

        
    precios_encontrados = [item.precio for item in publicaciones_items if item.precio > 0]
    analisis = calcular_precio_sugerido(
        costo=costo_kuroda,
        precio_kuroda=precio_kuroda,
        stock_actual=stock_kuroda,
        abc_f=abc_f,
        precios_competencia=precios_encontrados
    )
    
    competidores_reportados = competidores_prioritarios if competidores_prioritarios else ["Cualquier proveedor en internet / Plaza local"]
    
    return InvestigacionMercadoResult(
        codigo_material=codigo_material,
        descripcion_material=descripcion_material,
        precio_kuroda=precio_kuroda,
        costo_kuroda=costo_kuroda,
        stock_kuroda=stock_kuroda,
        abc_f=abc_f,
        plaza={"ciudad": ciudad, "estado": estado, "pais": pais},
        competidores_consultados=competidores_reportados,
        publicaciones=publicaciones_items,
        analisis_precios=analisis,
        resumen_plaza=resumen_plaza,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

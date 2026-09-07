import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


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
    resolved_key = (api_key or "").strip() or settings.OPENROUTER_API_KEY
    if not resolved_key:
        raise ValueError("OPENROUTER_API_KEY no está configurada en variables de entorno ni fue provista en la sesión.")
    
    # Modelo predeterminado para búsqueda web
    # Perplexity sonar o GPT-4o-mini con plugins web en OpenRouter
    resolved_model = (model or "").strip() or settings.OPENROUTER_MODEL
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {resolved_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://kuroda.com",
        "X-Title": "CRM Kuroda Inteligente"
    }
    
    payload: Dict[str, Any] = {
        "model": resolved_model,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        # Habilitar plugin de búsqueda web nativo de OpenRouter
        "plugins": [{"id": "web"}]
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
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
    competidores_list = [c.strip() for c in (competidores or []) if c.strip()]
    if not competidores_list:
        competidores_list = ["The Home Depot", "Construrama", "Plomería Universal", "El Surtidor", "Ferreterías locales"]
        
    system_instruction = (
        "Eres un Agente Investigador de Mercado experto en el sector de plomería, materiales de construcción, "
        "tuberías, grifería y acabados en México. Tu labor es buscar activamente en internet precios, publicaciones "
        "y promociones vigentes de productos específicos en una zona geográfica delimitada.\n\n"
        "REGLAS OBLIGATORIAS:\n"
        "1. Debes enfocar la investigación exclusivamente en la plaza geográfica indicada (ciudad y estado). "
        "No mezcles precios de tiendas en otras ciudades lejanas a menos que ofrezcan envío directo con flete a dicha plaza.\n"
        "2. Identifica publicaciones reales de competidores (ej. The Home Depot, Construrama, distribuidores locales o tiendas online en México).\n"
        "3. Debes responder EXCLUSIVAMENTE en formato JSON válido, sin bloques de texto explicativo fuera del JSON.\n"
        "4. Estructura JSON esperada:\n"
        "{\n"
        '  "publicaciones": [\n'
        "    {\n"
        '      "tienda": "Nombre del competidor o tienda",\n'
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
        f"INVESTIGACIÓN DE MERCADO:\n"
        f"- Producto de referencia Kuroda: {descripcion_material} (Código: {codigo_material})\n"
        f"- Precio actual de lista en Kuroda: ${precio_kuroda:.2f} MXN\n"
        f"- Plaza geográfica objetivo: {ciudad}, {estado}, {pais}\n"
        f"- Competidores priorizados a auditar en la zona: {', '.join(competidores_list)}\n\n"
        f"Realiza la búsqueda web para encontrar precios actuales de este producto o equivalentes directos de la misma marca/especificación "
        f"en {ciudad}, {estado}. Devuelve los resultados encontrados en el formato JSON solicitado."
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
        
        # Limpieza de bloque de código markdown si existe
        clean_json = raw_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        elif clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()
        
        parsed = json.loads(clean_json)
        resumen_plaza = parsed.get("resumen_plaza", f"Investigación realizada en plaza {ciudad}, {estado}.")
        
        for pub in parsed.get("publicaciones", []):
            p_val = float(pub.get("precio", 0.0))
            dif_abs = round(precio_kuroda - p_val, 2)
            dif_pct = round(((precio_kuroda - p_val) / p_val) * 100, 2) if p_val > 0 else 0.0
            
            publicaciones_items.append(
                ItemCompetidor(
                    tienda=pub.get("tienda", "Competidor local"),
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
            
    except Exception as exc:
        logger.warning(f"No se pudo completar búsqueda online en tiempo real: {exc}. Generando análisis de referencia.")
        resumen_plaza = f"Investigación en plaza {ciudad}, {estado} (Modo referencia ante disponibilidad web)."
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
    
    return InvestigacionMercadoResult(
        codigo_material=codigo_material,
        descripcion_material=descripcion_material,
        precio_kuroda=precio_kuroda,
        costo_kuroda=costo_kuroda,
        stock_kuroda=stock_kuroda,
        abc_f=abc_f,
        plaza={"ciudad": ciudad, "estado": estado, "pais": pais},
        competidores_consultados=competidores_list,
        publicaciones=publicaciones_items,
        analisis_precios=analisis,
        resumen_plaza=resumen_plaza,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

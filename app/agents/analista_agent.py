import logging
from typing import List, Dict, Any
from app.agents.llm import call_llm
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.log_agente import LogAgente

logger = logging.getLogger(__name__)

async def analizar_rendimiento(cotizaciones: List[Dict[str, Any]], db: AsyncSession) -> str:
    """
    Agente 4: Analista (Business Insights).
    Toma las cotizaciones y redacta un resumen ejecutivo sobre el estado de ventas.
    """
    system_instruction = (
        "Eres un Agente Analista de Inteligencia de Negocios para CRM Kuroda. "
        "Tu objetivo es leer un resumen de las cotizaciones (ganadas, perdidas, pendientes) "
        "y redactar un breve y conciso Resumen Ejecutivo Mensual. Destaca qué se está haciendo bien, "
        "dónde se pierden ventas y sugiere recomendaciones tácticas."
    )
    
    # Procesar cotizaciones a texto simple para el LLM
    ganadas = [c for c in cotizaciones if c.get("venta_perdida") == "No"]
    perdidas = [c for c in cotizaciones if c.get("venta_perdida") == "Si"]
    pendientes = [c for c in cotizaciones if not c.get("venta_perdida")]
    
    total_ganadas = sum(float(c.get("total", 0)) for c in ganadas)
    total_perdidas = sum(float(c.get("total", 0)) for c in perdidas)
    
    prompt = (
        f"Por favor analiza el siguiente corte de caja y danos un Resumen Ejecutivo:\n\n"
        f"- Cotizaciones Exitosas (Ganadas): {len(ganadas)} (Total: ${total_ganadas:,.2f})\n"
        f"- Cotizaciones Perdidas: {len(perdidas)} (Total: ${total_perdidas:,.2f})\n"
        f"- Cotizaciones Pendientes de cierre: {len(pendientes)}\n\n"
        "Detalle de Cotizaciones Perdidas (Para análisis de causa raíz):\n"
    )
    
    for c in perdidas[:10]: # Solo las 10 últimas para no exceder tokens
        prompt += f"- Vendedor: {c.get('vendedor_nombre')}, Cliente: {c.get('cliente_nombre')}, Total: ${c.get('total')}, Comentarios: {c.get('comentarios', 'Sin comentarios')}\n"
        
    try:
        # Llamar al modelo de lenguaje (OpenRouter)
        respuesta = await call_llm(prompt=prompt, system_instruction=system_instruction)
        
        # Registrar auditoría
        log = LogAgente(
            agente_nombre="Analista_BusinessInsights",
            prompt_enviado=prompt,
            respuesta_recibida=respuesta
        )
        db.add(log)
        await db.commit()
        
        return respuesta
    except Exception as e:
        logger.error(f"Error en Agente Analista: {str(e)}")
        raise e

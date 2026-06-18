import json
from decimal import Decimal
from typing import Any, Dict, List
from app.agents.llm import call_gemini

async def generate_seller_goals(
    vendedor_email: str,
    historial_cotizaciones: List[Dict[str, Any]],
    objetivos_globales: str
) -> Dict[str, Any]:
    """
    Generates structured sales goals for a seller based on their recent performance
    and global company targets. Returns a dict containing:
    - monto_objetivo: float
    - descripcion: str
    - kpis_clave: list[str]
    """
    system_instruction = (
        "Eres un analista de ventas inteligente especializado en CRM. "
        "Tu tarea es establecer cuotas y metas realistas, alcanzables pero retadoras para los vendedores. "
        "Debes responder estrictamente con el esquema JSON solicitado, sin explicaciones ni markdown."
    )
    
    # Format the history data nicely for the prompt
    history_summary = []
    for c in historial_cotizaciones:
        history_summary.append(
            f"- Cliente: {c.get('cliente_nombre')}, Total Cotizado: {c.get('total')}, Propuesta: {c.get('texto_propuesta')[:100]}..."
        )
    history_str = "\n".join(history_summary) if history_summary else "Sin historial de cotizaciones previas."
    
    prompt = (
        f"Analiza el siguiente historial de cotizaciones del vendedor: {vendedor_email}\n\n"
        f"Historial de Cotizaciones:\n{history_str}\n\n"
        f"Objetivos y Directrices Globales del Negocio:\n{objetivos_globales}\n\n"
        f"Por favor, calcula un monto de venta objetivo óptimo para el siguiente periodo, "
        f"redacta una descripción clara del enfoque estratégico, y define una lista de 3 a 5 KPIs clave específicos."
    )
    
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "monto_objetivo": {"type": "NUMBER", "description": "Monto de venta objetivo numérico."},
            "descripcion": {"type": "STRING", "description": "Descripción de la meta y enfoque estratégico."},
            "kpis_clave": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Lista de KPIs de desempeño medibles."
            }
        },
        "required": ["monto_objetivo", "descripcion", "kpis_clave"]
    }
    
    raw_response = await call_gemini(
        prompt=prompt,
        system_instruction=system_instruction,
        response_schema=response_schema
    )
    
    try:
        # Load the structured JSON response
        result = json.loads(raw_response)
        return result
    except json.JSONDecodeError as e:
        # Fallback structure in case of parsing errors
        return {
            "monto_objetivo": 100000.0,
            "descripcion": f"Meta base automática debido a error de procesamiento de IA. Detalle: {str(e)}",
            "kpis_clave": ["Contactar clientes recurrentes", "Aumentar cierres de ventas"]
        }

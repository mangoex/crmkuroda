import json
import httpx
from fastapi import HTTPException
from app.core.config import settings

def categorize_activity(name: str) -> str:
    """
    Clasifica las disciplinas editables de los usuarios en 4 categorías estándar.
    """
    n = name.lower().strip()
    # 1. Llamadas / Prospección
    if any(x in n for x in ["llam", "call", "prospect", "contac"]):
        return "llamada"
    # 2. Citas / Reuniones
    if any(x in n for x in ["cit", "reun", "meet", "visita"]):
        return "cita"
    # 3. Cotizaciones / Propuestas
    if any(x in n for x in ["cotiz", "propuest", "presupuest", "quot", "enviar"]):
        return "cotizacion"
    # 4. Ventas / Cierres / Cobro
    if any(x in n for x in ["cierr", "vent", "cobro", "clos", "firm"]):
        return "venta"
    return "otra"

async def run_coaching_chat(messages_history: list) -> dict:
    """
    Runs the Slight Edge coaching chat logic. Accepts messages_history in OpenAI format.
    Returns a dict containing:
    - response: str (the text assistant message)
    - tool_call: dict or None (if tool was invoked, with parameters)
    """
    if not settings.OPENROUTER_API_KEY:
         raise HTTPException(
             status_code=500,
             detail="OPENROUTER_API_KEY no está configurado en las variables de entorno."
         )
         
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_instruction = (
        "Eres un coach de ventas experto y empático. Estás iniciando una sesión estructurada para diseñar el plan de "
        "\"La Ligera Ventaja\" (Slight Edge) del vendedor.\n\n"
        "Tu objetivo es guiarlo paso a paso:\n"
        "1. Pregunta amigablemente por sus objetivos financieros mensuales (ingresos deseados).\n"
        "2. Pregunta por su ticket promedio de venta.\n"
        "3. Pregunta o estima su tasa de conversión actual de citas a cierres.\n"
        "4. Con base en estos números, calcula el embudo inverso de ventas necesario para lograr el objetivo:\n"
        "   - Ventas necesarias = Meta de ingresos / Ticket promedio.\n"
        "   - Citas necesarias = Ventas necesarias / (Tasa de conversión / 100).\n"
        "   - Si el usuario te da una proporción directa de llamadas por venta (ej: 'para vender 1 necesito 10 llamadas'), "
        "calcula las llamadas mensuales totales multiplicando las ventas necesarias por esa cantidad de llamadas (ventas * llamadas_por_venta). "
        "Por ejemplo, si necesita 25 ventas y requiere 10 llamadas por venta, las llamadas necesarias son 250 (no 1000).\n"
        "5. Diseña una propuesta diaria de disciplinas constantes (acciones cotidianas y sencillas como llamadas, seguimiento, prospección).\n"
        "6. Asigna a cada acción un peso en puntos en función de su importancia de tal modo que al día sumen aproximadamente 10 puntos.\n\n"
        "FORMATO DE RESPUESTA OBLIGATORIO:\n"
        "- Escribe de manera conversacional, amigable, clara y estructurada en texto plano.\n"
        "- NO uses fórmulas matemáticas en formato LaTeX (como \\[ ... \\] o $$ ... $$) ni bloques de código.\n"
        "- NO uses encabezados de markdown pesados (como ## o ###).\n"
        "- Puedes usar saltos de línea sencillos y listas con guiones simples (-) para separar ideas.\n\n"
        "Una vez que el vendedor esté conforme con las actividades y los puntos, debes llamar obligatoriamente a la "
        "función 'save_slight_edge_plan' enviándole los parámetros estructurados correspondientes para guardar su configuración de forma permanente."
    )
    
    # Construct complete message payload
    messages = [{"role": "system", "content": system_instruction}] + messages_history
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "save_slight_edge_plan",
                "description": "Guarda la configuración final estructurada del plan de consistencia diaria de La Ligera Ventaja.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "monthly_income_goal": {"type": "number", "description": "Meta de ingresos mensuales del vendedor en número."},
                        "ticket_average": {"type": "number", "description": "Ticket de venta promedio del vendedor en número."},
                        "conversion_rate": {"type": "number", "description": "Tasa de conversión en porcentaje (ej: 25 para 25%)."},
                        "activities_config": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "activity": {"type": "string", "description": "Nombre de la disciplina diaria."},
                                    "points": {"type": "integer", "description": "Valor en puntos (ej: 2)."}
                                },
                                "required": ["activity", "points"]
                            },
                            "description": "Lista de actividades propuestas."
                        },
                        "daily_points_goal": {"type": "integer", "description": "Meta de puntos totales del día (sugerida: 10)."}
                    },
                    "required": ["monthly_income_goal", "ticket_average", "conversion_rate", "activities_config", "daily_points_goal"]
                }
            }
        }
    ]
    
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto"
    }
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Error al llamar a OpenRouter API en Coaching Chat (Status: {response.status_code}): {response.text}"
                )
            
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise HTTPException(
                    status_code=502,
                    detail="La API de OpenRouter no devolvió opciones en el chat de coaching."
                )
            
            msg = choices[0].get("message", {})
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])
            
            tool_call_data = None
            if tool_calls:
                # Get the first tool call
                tc = tool_calls[0]
                if tc.get("function", {}).get("name") == "save_slight_edge_plan":
                    try:
                        args = json.loads(tc.get("function", {}).get("arguments", "{}"))
                        tool_call_data = args
                    except Exception as parse_err:
                        print("Error parsing tool call arguments:", parse_err)
            
            return {
                "response": content or "¡Entendido! Vamos a registrar tu plan de La Ventaja.",
                "tool_call": tool_call_data
            }
            
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Fallo de comunicación con OpenRouter API en Coaching Chat: {str(e)}"
            )

async def generate_coordination_ai_goals(
    company_name: str,
    global_sales_target: float,
    global_goals: str,
    seller_name: str,
    seller_target_income: float,
    seller_ticket: float,
    seller_conversion_rate: float,
    seller_daily_points: int,
    seller_disciplines: str,
    actual_calls: int,
    actual_meetings: int,
    actual_quotes: int,
    actual_sales: int,
    actual_sales_amount: float,
    actual_avg_points: float,
    logged_days: int
) -> str:
    """
    Generates coaching suggestions for the coordinator using Gemini.
    """
    prompt = (
        f"Eres un coach de ventas experto especializado en la metodología \"La Ligera Ventaja\" (The Slight Edge) de Jeff Olson.\n"
        f"La empresa '{company_name}' tiene las siguientes directrices y metas:\n"
        f"- Meta de Facturación Mensual Global de la Empresa: ${global_sales_target}\n"
        f"- Estrategia Global: {global_goals}\n\n"
        f"Analiza al vendedor '{seller_name}' con base en su plan de La Ventaja y su desempeño de los últimos 30 días:\n\n"
        f"PLAN ACTUAL DE LA VENTAJA:\n"
        f"- Meta de ingresos mensuales del vendedor: ${seller_target_income}\n"
        f"- Ticket promedio: ${seller_ticket}\n"
        f"- Tasa de conversión planificada: {seller_conversion_rate}%\n"
        f"- Meta diaria de puntos: {seller_daily_points} pts\n"
        f"- Disciplinas diarias configuradas en su plan: {seller_disciplines}\n\n"
        f"RENDIMIENTO REAL EN LOS ÚLTIMOS 30 DÍAS:\n"
        f"- Llamadas completadas: {actual_calls}\n"
        f"- Citas completadas: {actual_meetings}\n"
        f"- Cotizaciones completadas: {actual_quotes}\n"
        f"- Ventas reales logradas (cierres): {actual_sales} (Monto estimado: ${actual_sales_amount})\n"
        f"- Consistencia promedio diaria: {actual_avg_points} pts (Meta diaria: {seller_daily_points} pts)\n"
        f"- Días con registro de actividades: {logged_days} días\n\n"
        f"Genera una sugerencia de coaching concisa y accionable para este vendedor (máximo 3 párrafos cortos, en español).\n"
        f"Compara su desempeño real contra sus metas planificadas y sugiere si debe ajustar sus disciplinas, mejorar su consistencia diaria, o si sus metas están correctamente alineadas para lograr el éxito global de la empresa.\n"
        f"No uses saludos ni introducciones, responde directamente con la recomendación."
    )
    
    system_instruction = "Eres un consultor estratégico de ventas y experto en la metodología de Jeff Olson."
    
    from app.agents.llm import call_gemini
    response = await call_gemini(prompt=prompt, system_instruction=system_instruction)
    return response

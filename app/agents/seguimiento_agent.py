import json
import logging
from typing import Any, Dict, List
import httpx
from app.core.config import settings
from app.agents.llm import call_gemini

logger = logging.getLogger(__name__)

async def generate_followup_message(
    vendedor_nombre: str,
    metas_vigentes: List[Dict[str, Any]],
    cotizaciones_recientes: List[Dict[str, Any]]
) -> str:
    """Generates a motivational, professional check-in message for a salesperson."""
    system_instruction = (
        "Eres un supervisor de ventas virtual y coach de negocios habilitador. "
        "Tu tono es profesional, motivacional, enfocado a resultados y de soporte constante. "
        "Genera un mensaje directo y breve (máximo 3-4 párrafos) dirigido al vendedor, "
        "haciendo referencia a sus metas vigentes y cotizaciones pendientes para impulsar su avance diario."
    )
    
    metas_str = "\n".join([
        f"- Meta: {m.get('descripcion')}, Objetivo: ${m.get('monto_objetivo')}, Estado: {m.get('estado')}"
        for m in metas_vigentes
    ]) if metas_vigentes else "No hay metas asignadas activas."
    
    cotizaciones_str = "\n".join([
        f"- Cotización para {c.get('cliente_nombre')}, Total: ${c.get('total')}"
        for c in cotizaciones_recientes
    ]) if cotizaciones_recientes else "No hay cotizaciones registradas recientemente."
    
    prompt = (
        f"Genera el seguimiento matutino para el vendedor: {vendedor_nombre}\n\n"
        f"Metas Vigentes:\n{metas_str}\n\n"
        f"Cotizaciones del Periodo:\n{cotizaciones_str}\n\n"
        f"Escribe un mensaje en español que lo salude cordialmente, "
        f"resuma cómo va con sus metas y le pregunte de forma alentadora el estatus de sus cotizaciones pendientes."
    )
    
    message = await call_gemini(
        prompt=prompt,
        system_instruction=system_instruction
    )
    return message.strip()

import urllib.parse

def generate_whatsapp_link(to_number: str, message: str) -> str:
    """
    Generates a wa.me link with a pre-filled message so the administrator
    can send the message manually.
    """
    # Standardize recipient phone format (remove symbols if present)
    clean_number = "".join(char for char in to_number if char.isdigit())
    
    encoded_message = urllib.parse.quote(message)
    wa_link = f"https://wa.me/{clean_number}?text={encoded_message}"
    
    logger.info(f"Enlace de WhatsApp generado para {clean_number}")
    return wa_link

async def send_whatsapp_message(to_number: str, message: str) -> str:
    """
    Alias to generate a wa.me link. The frontend or caller should use this URL to redirect the user.
    """
    return generate_whatsapp_link(to_number, message)

async def process_incoming_whatsapp_message(
    vendedor_nombre: str,
    message_text: str
) -> str:
    """
    Analyzes an incoming WhatsApp message from a salesperson and generates
    an appropriate virtual supervisor response.
    """
    system_instruction = (
        "Eres un supervisor de ventas virtual y coach para el CRM. "
        "Tu tarea es leer el mensaje que te envía el vendedor, responderle de forma alentadora y profesional, "
        "ofreciendo ayuda si tiene problemas o felicitándole si reporta avances. Mantén la respuesta amigable, corta y concisa."
    )
    
    prompt = (
        f"El vendedor {vendedor_nombre} te envía el siguiente mensaje:\n"
        f"\"{message_text}\"\n\n"
        f"Por favor, responde directamente a este mensaje en español."
    )
    
    reply = await call_gemini(
        prompt=prompt,
        system_instruction=system_instruction
    )
    return reply.strip()

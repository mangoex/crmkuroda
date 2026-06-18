import json
from decimal import Decimal
from typing import Any, Dict, List
from app.agents.llm import call_gemini

async def generate_proposal(
    cliente_nombre: str,
    items: List[Dict[str, Any]],
    requerimientos_adicionales: str = ""
) -> Dict[str, Any]:
    """
    Generates a formal, mathematically accurate proposal.
    Calculates the total price programmatically first to avoid LLM math errors,
    then uses Gemini to draft a professional sales pitch and formal text.
    """
    # 1. Programmatic total calculation (guarantees mathematical accuracy)
    calculated_total = Decimal("0.00")
    formatted_items = []
    
    for item in items:
        producto = item.get("producto", "Servicio/Producto")
        cantidad = int(item.get("cantidad", 1))
        precio_unitario = Decimal(str(item.get("precio_unitario", 0.00)))
        subtotal = cantidad * precio_unitario
        calculated_total += subtotal
        
        formatted_items.append({
            "producto": producto,
            "cantidad": cantidad,
            "precio_unitario": float(precio_unitario),
            "subtotal": float(subtotal)
        })

    # 2. Call Gemini for a persuasive formal business proposal structure
    system_instruction = (
        "Eres un ejecutivo comercial y redactor persuasivo experto en propuestas corporativas. "
        "Tu objetivo es redactar una cotización y propuesta comercial atractiva, formal y detallada. "
        "Debes mantener el total matemático proporcionado de forma exacta en tu respuesta. "
        "Usa viñetas, secciones limpias y un tono profesional de negocios."
    )
    
    items_summary_str = "\n".join([
        f"- {x['producto']} | Cantidad: {x['cantidad']} | P. Unitario: ${x['precio_unitario']:.2f} | Subtotal: ${x['subtotal']:.2f}"
        for x in formatted_items
    ])
    
    prompt = (
        f"Por favor redacta la propuesta comercial para: {cliente_nombre}.\n\n"
        f"Detalle de Cotización:\n{items_summary_str}\n\n"
        f"Total a pagar: ${calculated_total:.2f}\n"
        f"Notas adicionales del requerimiento: {requerimientos_adicionales if requerimientos_adicionales else 'Ninguna.'}\n\n"
        f"Escribe la propuesta en español. Debe incluir:\n"
        f"1. Un saludo y breve presentación de agradecimiento por su interés.\n"
        f"2. La tabla/detalle formal de conceptos cotizados con el total de ${calculated_total:.2f} destacado.\n"
        f"3. Condiciones de venta (tiempo de entrega de 3-5 días hábiles, vigencia del presupuesto por 15 días corridos).\n"
        f"4. Datos de contacto generales y despedida formal.\n\n"
        f"Mantén los montos y el total de la cotización exactamente como se indican: ${calculated_total:.2f}."
    )
    
    proposal_text = await call_gemini(
        prompt=prompt,
        system_instruction=system_instruction
    )
    
    return {
        "total": calculated_total,
        "texto_propuesta": proposal_text.strip(),
        "items_procesados": formatted_items
    }

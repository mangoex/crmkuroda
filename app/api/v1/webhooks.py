import logging
from typing import Optional
from fastapi import APIRouter, Request, Response, status, Query, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.config import settings
from app.models.usuario import Usuario
from app.agents.seguimiento_agent import process_incoming_whatsapp_message, send_whatsapp_message

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
):
    """
    Handles Meta's Webhook verification challenge (GET).
    Returns the challenge token if the verification token matches our configuration.
    """
    if hub_mode == "subscribe" and hub_challenge:
        if hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            logger.info("WhatsApp webhook verificado de manera exitosa.")
            return PlainTextResponse(content=hub_challenge, status_code=status.HTTP_200_OK)
        else:
            logger.warning("Intento de verificación de webhook fallido: token inválido.")
            return Response(content="Verificación fallida: Token incorrecto", status_code=status.HTTP_403_FORBIDDEN)
    return Response(content="Parámetros de webhook inválidos", status_code=status.HTTP_400_BAD_REQUEST)

@router.post("/whatsapp")
async def receive_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receives WhatsApp notification events from Meta (POST).
    Identifies the seller by phone number and triggers the virtual supervisor's response.
    """
    try:
        body = await request.json()
        logger.info(f"Webhook de WhatsApp recibido: {body}")

        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])

                for message in messages:
                    msg_type = message.get("type")
                    if msg_type != "text":
                        # We only process text interactions for now
                        continue

                    wa_id = message.get("from")  # e.g., "521234567890"
                    message_text = message.get("text", {}).get("body", "").strip()

                    if not wa_id or not message_text:
                        continue

                    # Search salesperson by phone number with flexible prefix matching
                    result = await db.execute(
                        select(Usuario).filter(
                            Usuario.telefono_whatsapp.like(f"%{wa_id}%") |
                            (wa_id.endswith(Usuario.telefono_whatsapp) & (Usuario.telefono_whatsapp != ""))
                        )
                    )
                    vendedor = result.scalars().first()

                    if vendedor:
                        vendedor_name = vendedor.email.split("@")[0].capitalize()
                        logger.info(f"Mensaje de WhatsApp recibido de {vendedor.email} ({wa_id}): {message_text}")
                        
                        # Generate response through supervisor agent
                        reply = await process_incoming_whatsapp_message(vendedor_name, message_text)
                        
                        # Send WhatsApp message back
                        await send_whatsapp_message(wa_id, reply)
                    else:
                        logger.warning(f"Mensaje de WhatsApp recibido de número no registrado: {wa_id}")
                        # Auto-reply notifying that they are not registered yet
                        generic_reply = (
                            "Hola, no reconozco este número de teléfono en el CRM Kuroda. "
                            "Por favor, solicita a tu administrador que registre tu número de WhatsApp."
                        )
                        await send_whatsapp_message(wa_id, generic_reply)

        return {"status": "success", "message": "Evento de WhatsApp procesado"}

    except Exception as e:
        logger.error(f"Error al procesar el webhook de WhatsApp: {str(e)}")
        # Always return 200 to prevent Meta from retrying indefinitely
        return {"status": "error", "message": f"Error de procesamiento: {str(e)}"}

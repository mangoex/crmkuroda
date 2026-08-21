import asyncio
import logging
from typing import Any, Dict, List, Optional
import httpx
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # segundos

async def _post_with_retry(
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: float = 45.0
) -> Dict[str, Any]:
    """Realiza una petición POST con reintentos exponenciales para fallos transitorios."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                # Reintentar si el servidor devuelve rate limit (429) o error de servidor (502, 503, 504)
                if response.status_code in (429, 502, 503, 504) and attempt < MAX_RETRIES:
                    backoff = INITIAL_BACKOFF * (2 ** (attempt - 1))
                    logger.warning(f"LLM API devolvió status {response.status_code}. Reintentando en {backoff:.1f}s (intento {attempt}/{MAX_RETRIES})...")
                    await asyncio.sleep(backoff)
                    continue
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Error al llamar a LLM API (Status: {response.status_code}): {response.text}"
                    )
                
                return response.json()
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                backoff = INITIAL_BACKOFF * (2 ** (attempt - 1))
                logger.warning(f"Fallo de conexión LLM ({type(exc).__name__}). Reintentando en {backoff:.1f}s (intento {attempt}/{MAX_RETRIES})...")
                await asyncio.sleep(backoff)
            else:
                break
        except HTTPException:
            raise
        except Exception as exc:
            last_error = exc
            break

    raise HTTPException(
        status_code=502,
        detail=f"Fallo de comunicación con LLM API tras {MAX_RETRIES} intentos: {str(last_error)}"
    )

async def _call_gemini_direct(
    prompt: str,
    system_instruction: Optional[str] = None,
    response_schema: Optional[dict] = None
) -> str:
    """Llama directamente a la API oficial de Google Gemini."""
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY no está configurada en las variables de entorno."
        )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    contents = []
    if system_instruction:
        contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_instruction}"}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    
    payload: Dict[str, Any] = {"contents": contents}
    
    if response_schema:
        payload["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
        
    data = await _post_with_retry(url, headers, payload)
    candidates = data.get("candidates", [])
    if not candidates:
        raise HTTPException(status_code=502, detail="Gemini API no devolvió candidatos de respuesta.")
        
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise HTTPException(status_code=502, detail="Gemini API no devolvió texto en el contenido.")
        
    return parts[0].get("text", "")

async def _call_openrouter(
    prompt: str,
    system_instruction: Optional[str] = None,
    response_schema: Optional[dict] = None
) -> str:
    """Llama a la API de OpenRouter."""
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
    
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})
    
    payload: Dict[str, Any] = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages
    }
    
    if response_schema:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "response_schema",
                "schema": response_schema,
                "strict": True
            }
        }
        
    data = await _post_with_retry(url, headers, payload)
    choices = data.get("choices", [])
    if not choices:
        raise HTTPException(status_code=502, detail="La API de OpenRouter no devolvió opciones.")
        
    return choices[0].get("message", {}).get("content", "")

async def call_llm(
    prompt: str,
    system_instruction: Optional[str] = None,
    response_schema: Optional[dict] = None
) -> str:
    """
    Función de entrada agéntica universal.
    Enruta hacia Gemini o OpenRouter según la configuración y claves disponibles.
    """
    provider = (settings.LLM_PROVIDER or "openrouter").lower()
    
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return await _call_gemini_direct(prompt, system_instruction, response_schema)
    elif settings.OPENROUTER_API_KEY:
        return await _call_openrouter(prompt, system_instruction, response_schema)
    elif settings.GEMINI_API_KEY:
        return await _call_gemini_direct(prompt, system_instruction, response_schema)
    else:
        raise HTTPException(
            status_code=500,
            detail="No hay credenciales de LLM configuradas (OPENROUTER_API_KEY o GEMINI_API_KEY)."
        )

async def call_llm_chat(
    messages_history: List[Dict[str, Any]],
    system_instruction: Optional[str] = None,
    tools: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Maneja conversaciones interactivas multi-turno y llamadas a funciones/herramientas (tools).
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
    
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.extend(messages_history)
    
    payload: Dict[str, Any] = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages
    }
    
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
        
    data = await _post_with_retry(url, headers, payload)
    choices = data.get("choices", [])
    if not choices:
        raise HTTPException(status_code=502, detail="La API de OpenRouter no devolvió opciones en el chat.")
        
    msg = choices[0].get("message", {})
    return msg

# Alias retrocompatible
call_gemini = call_llm

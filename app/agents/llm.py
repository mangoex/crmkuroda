import httpx
from fastapi import HTTPException
from app.core.config import settings

async def call_llm(prompt: str, system_instruction: str = None, response_schema: dict = None) -> str:
    """Asynchronously calls the OpenRouter API via direct HTTP POST requests."""
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
    
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages
    }
    
    if response_schema:
        # Formato de respuesta JSON estructurada para OpenAI / OpenRouter
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "response_schema",
                "schema": response_schema,
                "strict": True
            }
        }
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Error al llamar a OpenRouter API (Status: {response.status_code}): {response.text}"
                )
            
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise HTTPException(
                    status_code=502,
                    detail="La API de OpenRouter no devolvió opciones."
                )
            
            content = choices[0].get("message", {}).get("content", "")
            return content
            
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Fallo de comunicación con OpenRouter API: {str(e)}"
            )

# Alias para compatibilidad hacia atrás
call_gemini = call_llm

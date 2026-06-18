import httpx
from fastapi import HTTPException
from app.core.config import settings

async def call_gemini(prompt: str, system_instruction: str = None, response_schema: dict = None) -> str:
    """Asynchronously calls the Gemini API via direct HTTP POST requests."""
    if not settings.LLM_API_KEY:
         raise HTTPException(
             status_code=500,
             detail="LLM_API_KEY no está configurado en las variables de entorno."
         )
         
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.LLM_MODEL}:generateContent?key={settings.LLM_API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    contents = [{
        "parts": [{"text": prompt}]
    }]
    
    payload = {
        "contents": contents
    }
    
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }
        
    if response_schema:
        payload["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Error al llamar a Gemini API (Status: {response.status_code}): {response.text}"
                )
            
            data = response.json()
            # Ensure the structure exists
            candidates = data.get("candidates", [])
            if not candidates:
                raise HTTPException(
                    status_code=502,
                    detail="La API de Gemini no devolvió candidatos para el prompt suministrado."
                )
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                raise HTTPException(
                    status_code=502,
                    detail="La API de Gemini devolvió una respuesta vacía."
                )
                
            return parts[0].get("text", "")
            
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Fallo de comunicación con Gemini API: {str(e)}"
            )

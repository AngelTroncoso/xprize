import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
DEFAULT_TEMPERATURE = 0.4
FALLBACK_MESSAGE = (
    "Ocurrió un problema al generar la respuesta pedagógica con Gemini. "
    "Intenta nuevamente en unos segundos."
)


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("GEMINI_API_KEY no está configurada en el entorno.")

        self.model = model or DEFAULT_MODEL
        self.client = genai.Client(api_key=self.api_key)

    async def generate_pedagogic_response(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        model: Optional[str] = None,
    ) -> str:
        chosen_model = model or self.model
        contents: List[str] = [f"SYSTEM: {system_prompt}"]

        if history:
            for turn in history:
                role = turn.get("role", "user").upper()
                text = turn.get("text", "")
                contents.append(f"{role}: {text}")

        contents.append(f"USER: {user_message}")
        prompt = "\n".join(contents)

        try:
            def call_api() -> Any:
                return self.client.models.generate_content(
                    model=chosen_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        response_mime_type="text",
                    ),
                )

            response = await asyncio.to_thread(call_api)

            if hasattr(response, "content") and response.content:
                return str(response.content)

            if hasattr(response, "text") and response.text:
                return str(response.text)

            output = getattr(response, "output", None)
            if isinstance(output, list) and output:
                first = output[0]
                if isinstance(first, dict):
                    content = first.get("content")
                    if isinstance(content, list) and content:
                        candidate = content[0]
                        if isinstance(candidate, dict) and candidate.get("text"):
                            return str(candidate.get("text"))
                        return str(candidate)
                    return str(first)

            candidates = getattr(response, "candidates", None)
            if isinstance(candidates, list) and candidates:
                first = candidates[0]
                if isinstance(first, dict) and first.get("content"):
                    return str(first.get("content"))
                return str(first)

            return str(response)

        except Exception as error:
            logger.exception("Error generando respuesta con Gemini: %s", error)
            return FALLBACK_MESSAGE


default_gemini_client = GeminiClient()


import asyncio
import base64
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

    async def analyze_canvas_image(
        self,
        canvas_b64_data: str,
        system_prompt: str,
        user_message: str,
        temperature: float = DEFAULT_TEMPERATURE,
        model: Optional[str] = None,
    ) -> str:
        """
        Analiza una imagen de canvas usando la API multimodal de Gemini.

        Args:
            canvas_b64_data: Datos de imagen en Base64 (con o sin DataURL)
            system_prompt: Prompt del sistema para el contexto pedagógico
            user_message: Pregunta o contexto del usuario
            temperature: Control de creatividad
            model: Modelo a usar (por defecto el del cliente)

        Returns:
            Análisis visual en texto
        """
        chosen_model = model or self.model

        try:
            # Limpiar Base64 si incluye DataURL
            if "," in canvas_b64_data:
                canvas_b64_data = canvas_b64_data.split(",", 1)[1]

            # Decodificar para validar que es imagen válida
            image_bytes = base64.b64decode(canvas_b64_data)

            # Crear contenido multimodal para Google GenAI SDK
            def call_api() -> Any:
                return self.client.models.generate_content(
                    model=chosen_model,
                    contents=[
                        f"SYSTEM: {system_prompt}",
                        f"USER: {user_message}",
                        types.Part.from_data(data=image_bytes, mime_type="image/png"),
                        "Analiza esta imagen y proporciona tu feedback pedagógico.",
                    ],
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        response_mime_type="text",
                    ),
                )

            response = await asyncio.to_thread(call_api)

            if hasattr(response, "text") and response.text:
                return str(response.text)

            if hasattr(response, "content") and response.content:
                return str(response.content)

            candidates = getattr(response, "candidates", None)
            if isinstance(candidates, list) and candidates:
                first = candidates[0]
                if hasattr(first, "content"):
                    return str(first.content)

            return str(response)

        except Exception as error:
            logger.exception("Error analizando imagen con Gemini: %s", error)
            return FALLBACK_MESSAGE


default_gemini_client = GeminiClient()


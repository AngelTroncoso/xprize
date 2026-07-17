import asyncio
import base64
import binascii
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
DEFAULT_TEMPERATURE = 0.4
FALLBACK_MESSAGE = (
    "Ocurrio un problema al generar la respuesta pedagogica con Gemini. "
    "Intenta nuevamente en unos segundos."
)


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or DEFAULT_MODEL
        self.client = None
        
        if self._has_api_key():
            self.client = genai.Client(api_key=self.api_key)
        else:
            # Fallback a Vertex AI usando las credenciales de Google Cloud Run
            try:
                self.client = genai.Client(
                    vertexai=True, 
                    project="gen-lang-client-0142253597", 
                    location="us-central1"
                )
                logger.info("Cliente Gemini inicializado mediante Vertex AI.")
            except Exception as e:
                logger.warning(f"Fallo al inicializar Vertex AI: {e}")

    def _has_api_key(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your-"))

    def _ensure_client(self) -> bool:
        if self.client:
            return True
        logger.warning("GEMINI_API_KEY no esta configurada y Vertex AI falló; se omite llamada a Gemini.")
        return False

    async def generate_pedagogic_response(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        model: Optional[str] = None,
        response_schema: Optional[Any] = None,
        gemini_file_id: Optional[str] = None,
    ) -> str:
        if not self._ensure_client():
            return FALLBACK_MESSAGE

        chosen_model = model or self.model
        contents_list: List[str] = [f"SYSTEM: {system_prompt}"]

        if history:
            for turn in history:
                role = turn.get("role", "user").upper()
                text = turn.get("text") or turn.get("content", "")
                contents_list.append(f"{role}: {text}")

        contents_list.append(f"USER: {user_message}")
        prompt = "\n".join(contents_list)

        api_contents = [prompt]
        if gemini_file_id:
            try:
                gemini_file = self.client.files.get(name=gemini_file_id)
                api_contents.insert(0, gemini_file)
            except Exception as e:
                logger.warning(f"No se pudo cargar el archivo {gemini_file_id}: {e}")

        try:
            def call_api() -> Any:
                config_args = {
                    "temperature": temperature,
                }
                if response_schema:
                    config_args["response_mime_type"] = "application/json"
                    config_args["response_schema"] = response_schema
                else:
                    config_args["response_mime_type"] = "text/plain"
                    
                return self.client.models.generate_content(
                    model=chosen_model,
                    contents=api_contents,
                    config=types.GenerateContentConfig(**config_args),
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
        if not self._ensure_client():
            return FALLBACK_MESSAGE

        chosen_model = model or self.model

        try:
            if "," in canvas_b64_data:
                canvas_b64_data = canvas_b64_data.split(",", 1)[1]

            try:
                image_bytes = base64.b64decode(canvas_b64_data)
            except binascii.Error:
                raise ValueError("Estructura de imagen Canvas inválida")

            def call_api() -> Any:
                return self.client.models.generate_content(
                    model=chosen_model,
                    contents=[
                        f"SYSTEM: {system_prompt}",
                        f"USER: {user_message}",
                        types.Part.from_data(data=image_bytes, mime_type="image/png"),
                        "Analiza esta imagen y proporciona tu feedback pedagogico.",
                    ],
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        response_mime_type="text/plain",
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

        except ValueError:
            raise
        except Exception as error:
            logger.exception("Error analizando imagen con Gemini: %s", error)
            return FALLBACK_MESSAGE


default_gemini_client = GeminiClient()

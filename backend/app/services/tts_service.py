import base64
import io
from typing import Optional, Tuple
from gtts import gTTS
import logging

logger = logging.getLogger(__name__)


class TTSService:
    """
    Servicio de Texto a Voz (TTS) para generar respuestas de audio.
    Utiliza gTTS como fallback nativo con soporte para español latino.
    """

    def __init__(self, language: str = "es", lang_region: str = "es-mx"):
        """
        Inicializa el servicio TTS.

        Args:
            language: Código de idioma (ej. 'es' para español)
            lang_region: Región de idioma para acento natural (ej. 'es-mx' para México)
        """
        self.language = language
        self.lang_region = lang_region

    def text_to_speech(
        self, text: str, clean_text: bool = True
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Convierte texto a audio y lo codifica en Base64.

        Args:
            text: Texto a convertir a voz
            clean_text: Si es True, limpia caracteres especiales y Markdown

        Returns:
            Tupla (audio_b64, mime_type) o (None, None) si falla
        """
        try:
            if not text or len(text.strip()) == 0:
                logger.warning("Texto vacío recibido en TTS")
                return None, None

            # Limpiar texto de Markdown y caracteres especiales
            if clean_text:
                text = self._clean_text(text)

            # No limitar el texto para que lea la respuesta completa
            text_for_audio = text

            # Generar audio con gTTS
            tts = gTTS(text=text_for_audio, lang=self.language, slow=False)

            # Guardar en buffer en memoria
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            # Codificar a Base64
            audio_b64 = base64.b64encode(audio_buffer.getvalue()).decode("utf-8")

            logger.info(
                f"TTS generado exitosamente. Largo de audio: {len(audio_buffer.getvalue())} bytes"
            )
            return audio_b64, "audio/mpeg"

        except Exception as e:
            logger.error(f"Error en TTS: {str(e)}")
            return None, None

    def _clean_text(self, text: str) -> str:
        """
        Limpia el texto de caracteres especiales y Markdown para mejor pronunciación.
        """
        # Remover markdown
        text = text.replace("**", "").replace("__", "").replace("##", "")
        text = text.replace("#", "").replace("*", "").replace("-", " ")
        text = text.replace("[", "").replace("]", "").replace("(", "").replace(")", "")

        # Remover saltos de línea múltiples
        while "\n\n" in text:
            text = text.replace("\n\n", "\n")

        return text.strip()

    def _extract_first_paragraphs(self, text: str, max_chars: int = 500) -> str:
        """
        Extrae los primeros párrafos del texto para narración breve.
        """
        paragraphs = text.split("\n")
        result = ""

        for para in paragraphs:
            if len(result) + len(para) <= max_chars:
                result += para + " "
            else:
                break

        return result.strip()

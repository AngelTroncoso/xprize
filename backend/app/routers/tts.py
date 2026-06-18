from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import io
from gtts import gTTS
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["TTS"])


class TTSInput(BaseModel):
    text: str = Field(..., description="Texto a convertir a voz (máx. 500 caracteres)")
    session_id: str = Field(..., description="ID de sesión para tracking")


class TTSOutput(BaseModel):
    message: str
    audio_bytes: int


@router.post("/tts")
async def text_to_speech(input_data: TTSInput):
    """
    Convierte texto a audio MP3 usando gTTS en español latinoamericano.
    Retorna el audio como StreamingResponse con Content-Type: audio/mpeg.
    Límite: 500 caracteres de texto.
    """
    text = input_data.text.strip()

    if not text:
        raise HTTPException(status_code=422, detail="El texto no puede estar vacío")

    if len(text) > 500:
        text = text[:500]
        logger.info("Texto truncado a 500 caracteres para TTS")

    try:
        # Generar audio con gTTS — español latinoamericano (México)
        tts = gTTS(text=text, lang="es", slow=False, tld="com.mx")

        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        logger.info(
            f"TTS generado: {len(audio_buffer.getvalue())} bytes para sesión {input_data.session_id}"
        )

        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=tts_output.mp3",
                "Content-Length": str(len(audio_buffer.getvalue())),
            },
        )

    except Exception as e:
        logger.error(f"Error generando TTS: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generando audio: {str(e)}"
        )
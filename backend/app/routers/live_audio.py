"""
live_audio.py — Router de WebSocket para Audio en Tiempo Real (Estilo Gemini Live)

Tarea 2: Pipeline de Baja Latencia
- Endpoint WebSocket `/api/live` que actúa como proxy directo entre el frontend
  y la API Multimodal Live de Gemini.
- Flujo asíncrono: recibe chunks binarios de audio del micrófono del niño,
  los reenvía a Gemini Live, y retransmite el streaming de audio de respuesta.
- Incluye contexto MINEDUC (curso, asignatura, OA) en la inicialización.
"""

import asyncio
import json
import logging
import os
import base64
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from google import genai
from google.genai import types
import websockets

from app.models.database import db

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Live Audio"])

# ─── Constantes ───────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-2.0-flash-live-001")

ELEVENLABS_API_KEY = "sk_024b7419d845c3441310c0b794be5036cfdf7400c97059fd"
ELEVENLABS_VOICE_ID = "7QQzpAyzlKTVrRzQJmTE"

# ─── Constructor de Prompt del Sistema ────────────────────────────────────────

def build_live_system_prompt(
    curso: str,
    asignatura: str,
    id_oa: str,
    oa_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Construye el prompt del sistema para la sesión Live de Gemini.
    Incluye el contexto pedagógico del OA del MINEDUC para mantener el foco.
    """
    oa_desc = oa_context.get("descripcion", "") if oa_context else ""
    conceptos = ", ".join(oa_context.get("conceptos_clave", [])) if oa_context else ""
    indicadores = ", ".join(oa_context.get("indicadores_evaluacion", [])) if oa_context else ""

    parts = [
        f"Actúas como Súper Profesor para un alumno de {curso} en Chile.",
        f"Asignatura: {asignatura}.",
        f"Objetivo de Aprendizaje actual ({id_oa}): {oa_desc}.",
    ]

    if conceptos:
        parts.append(f"Conceptos clave: {conceptos}.")
    if indicadores:
        parts.append(f"Indicadores de evaluación: {indicadores}.")

    parts.append(
        "Eres el Súper Profesor, la persona más afable, dulce, paciente y buena gente que existe. "
        "Tu misión principal es MOTIVAR e INSPIRAR al niño. Celebra cada pequeño logro, "
        "hazle sentir que es increíblemente inteligente y capaz. Usa un tono cálido, humano y muy cercano "
        "en español chileno amigable (usa modismos suaves si aplica). "
        "Nunca lo regañes, si se equivoca dile que es una excelente oportunidad para aprender. "
        "Usa analogías divertidas y mágicas. Mantén tus respuestas conversacionales y breves, para mantener el diálogo vivo."
    )

    return " ".join(parts)


# ─── Recuperación de Contexto OA desde Supabase ──────────────────────────────

async def fetch_oa_context_from_supabase(
    curso: str,
    asignatura: str,
    id_oa: str,
) -> Optional[Dict[str, Any]]:
    supabase_client = db.get_client()
    if not supabase_client:
        return None

    try:
        def _query():
            return (
                supabase_client.table("curriculum_objectives")
                .select("id_oa, curso, asignatura, descripcion, conceptos_clave, indicadores_evaluacion")
                .eq("curso", curso)
                .eq("asignatura", asignatura)
                .eq("id_oa", id_oa)
                .limit(1)
                .maybe_single()
                .execute()
            )

        response = await asyncio.to_thread(_query)
        if response.data:
            return response.data
        return None
    except Exception as e:
        logger.error(f"[live_audio] Error consultando OA en Supabase: {e}")
        return None

# ─── ElevenLabs Audio Receiver ────────────────────────────────────────────────
async def read_from_elevenlabs(el_ws: websockets.WebSocketClientProtocol, client_ws: WebSocket):
    """Lee el audio generado por ElevenLabs y lo retransmite al Frontend en chunks MP3."""
    try:
        async for message in el_ws:
            try:
                data = json.loads(message)
                if "audio" in data and data["audio"]:
                    audio_bytes = base64.b64decode(data["audio"])
                    await client_ws.send_bytes(audio_bytes)
                if data.get("isFinal"):
                    break
            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        logger.error(f"[live_audio] Error en read_from_elevenlabs: {e}")


# ─── WebSocket Endpoint ──────────────────────────────────────────────────────

@router.websocket("/api/live")
async def live_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("[live_audio] Nueva conexión WebSocket aceptada")

    session_id: Optional[str] = None
    student_id: Optional[str] = None
    live_session: Any = None
    
    # Referencias para ElevenLabs
    el_ws: Optional[websockets.WebSocketClientProtocol] = None
    el_task: Optional[asyncio.Task] = None

    try:
        # ── 1. Inicialización ──────────────────────────
        init_data_raw = await websocket.receive_text()
        init_data = json.loads(init_data_raw)
        
        session_id = init_data.get("session_id")
        student_id = init_data.get("student_id")
        curso = init_data.get("curso")
        asignatura = init_data.get("asignatura")
        id_oa = init_data.get("id_oa")

        oa_context = await fetch_oa_context_from_supabase(curso, asignatura, id_oa)
        system_prompt = build_live_system_prompt(curso, asignatura, id_oa, oa_context)

        await websocket.send_json({
            "type": "init_ack",
            "session_id": session_id,
            "oa_found": oa_context is not None,
            "system_prompt_length": len(system_prompt),
        })

        # ── 2. Abrir sesión Gemini (MODO TEXTO) ────────────
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        live_session = await gemini_client.aio.live.connect(
            model=GEMINI_LIVE_MODEL,
            config=types.LiveConnectConfig(
                response_modalities=["text"],  # <--- CRÍTICO: Solo texto, usaremos ElevenLabs para el audio
                system_instruction=types.Part.from_text(system_prompt),
                audio_transcription_config=types.AudioTranscriptionConfig(
                    enabled=True,
                    language_code="es-ES",
                ),
            ),
        )

        # ── 3. Bucle bidireccional ───────────────────────────────

        async def receive_from_client():
            nonlocal live_session
            while True:
                try:
                    raw = await websocket.receive()
                    if raw["type"] == "websocket.disconnect":
                        break
                    
                    if "bytes" in raw:
                        # Enviar PCM del micrófono del niño a Gemini
                        await live_session.send(
                            types.LiveClientContent(
                                turns=[
                                    types.Content(
                                        role="user",
                                        parts=[types.Part.from_data(
                                            data=raw["bytes"],
                                            mime_type="audio/webm;codecs=opus"
                                        )]
                                    )
                                ],
                                turn_complete=True,
                            )
                        )
                    elif "text" in raw:
                        msg = json.loads(raw["text"])
                        if msg.get("type") == "interrupt":
                            # Si el frontend interrumpe, deberíamos idealmente parar el tts actual
                            pass
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"[live_audio] Error en receive_from_client: {e}")
                    break

        async def send_to_client():
            nonlocal live_session, el_ws, el_task
            try:
                async for response in live_session.receive():
                    if response is None:
                        continue

                    # Extraer el texto generado por Gemini
                    if hasattr(response, "server_content") and response.server_content:
                        sc = response.server_content
                        if sc.model_turn:
                            for part in sc.model_turn.parts:
                                if part.text:
                                    # Streaming text to frontend too for subtitles
                                    await websocket.send_json({
                                        "type": "response_text",
                                        "text": part.text
                                    })
                                    
                                    # Enviar a ElevenLabs
                                    if el_ws is None:
                                        # Iniciar nueva conexión WS con ElevenLabs para esta respuesta
                                        el_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream-input?model_id=eleven_multilingual_v2"
                                        el_ws = await websockets.connect(el_url, extra_headers={"xi-api-key": ELEVENLABS_API_KEY})
                                        # Inicialización del stream (voz en español)
                                        await el_ws.send(json.dumps({
                                            "text": " ",
                                            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
                                        }))
                                        # Arrancar receptor de MP3
                                        el_task = asyncio.create_task(read_from_elevenlabs(el_ws, websocket))
                                        
                                        # Notificar al frontend que empezó el audio
                                        await websocket.send_json({"type": "audio_start"})
                                    
                                    # Enviar el chunk de texto real
                                    await el_ws.send(json.dumps({"text": part.text}))

                    if response.turn_complete:
                        await websocket.send_json({"type": "turn_complete"})
                        # Cerrar el turno de ElevenLabs enviando cadena vacía
                        if el_ws is not None:
                            await el_ws.send(json.dumps({"text": ""}))
                            # el task se encargará de cerrarse cuando llegue isFinal
                            el_ws = None

            except Exception as e:
                logger.error(f"[live_audio] Error en send_to_client: {e}", exc_info=True)

        await asyncio.gather(receive_from_client(), send_to_client())

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"[live_audio] Error general: {e}", exc_info=True)
    finally:
        if live_session:
            await live_session.close()
        if el_ws:
            await el_ws.close()
        try:
            if websocket.client_state.name != "DISCONNECTED":
                await websocket.close()
        except Exception:
            pass
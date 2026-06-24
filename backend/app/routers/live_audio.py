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
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from google import genai
from google.genai import types

from app.models.database import db

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Live Audio"])

# ─── Constantes ───────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-2.0-flash-live-001")

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
        "Mantén un tono sumamente lúdico, empático, usa analogías simples para niños "
        "y fomenta la curiosidad. Responde en español chileno amigable. "
        "Genera audio de respuesta inmediato y natural."
    )

    return " ".join(parts)


# ─── Recuperación de Contexto OA desde Supabase ──────────────────────────────

async def fetch_oa_context_from_supabase(
    curso: str,
    asignatura: str,
    id_oa: str,
) -> Optional[Dict[str, Any]]:
    """
    Consulta curriculum_objectives en Supabase para obtener el contexto
    pedagógico completo del OA. Retorna None si no hay conexión o no existe.
    """
    supabase_client = db.get_client()
    if not supabase_client:
        logger.warning("[live_audio] Supabase no configurado. Continuando sin contexto curricular.")
        return None

    try:
        # Ejecutar en un thread para no bloquear el event loop
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
            return {
                "id_oa": response.data.get("id_oa"),
                "curso": response.data.get("curso"),
                "asignatura": response.data.get("asignatura"),
                "descripcion": response.data.get("descripcion"),
                "conceptos_clave": response.data.get("conceptos_clave", []),
                "indicadores_evaluacion": response.data.get("indicadores_evaluacion", []),
            }

        logger.warning(
            f"[live_audio] OA no encontrado: curso={curso}, asignatura={asignatura}, id_oa={id_oa}"
        )
        return None

    except Exception as e:
        logger.error(f"[live_audio] Error consultando OA en Supabase: {e}", exc_info=True)
        return None


# ─── WebSocket Endpoint ──────────────────────────────────────────────────────

@router.websocket("/api/live")
async def live_audio_endpoint(websocket: WebSocket):
    """
    WebSocket de baja latencia para el Modo Audio en Tiempo Real.

    Flujo:
    1. Cliente envía mensaje de inicialización JSON:
       { "type": "init", "session_id": "...", "student_id": "...",
         "curso": "...", "asignatura": "...", "id_oa": "..." }
    2. Backend recupera contexto pedagógico del OA desde Supabase.
    3. Backend abre sesión Live con Gemini Multimodal Live API.
    4. Cliente envía chunks binarios de audio (voz del micrófono).
    5. Backend los reenvía a Gemini Live.
    6. Gemini responde con streaming de audio → lo retransmite al cliente.
    7. Cierre: cualquiera de las partes desconecta.
    """
    await websocket.accept()
    logger.info("[live_audio] Nueva conexión WebSocket aceptada")

    # Variables de sesión
    session_id: Optional[str] = None
    student_id: Optional[str] = None
    curso: Optional[str] = None
    asignatura: Optional[str] = None
    id_oa: Optional[str] = None
    system_prompt: Optional[str] = None

    # Referencia a la sesión Live de Gemini
    live_session: Any = None

    try:
        # ── 1. Esperar mensaje de inicialización ──────────────────────────
        init_data_raw = await websocket.receive_text()
        try:
            init_data = json.loads(init_data_raw)
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "message": "El primer mensaje debe ser un JSON con tipo 'init'"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if init_data.get("type") != "init":
            await websocket.send_json({
                "type": "error",
                "message": "El primer mensaje debe ser de tipo 'init'"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        session_id = init_data.get("session_id")
        student_id = init_data.get("student_id")
        curso = init_data.get("curso")
        asignatura = init_data.get("asignatura")
        id_oa = init_data.get("id_oa")

        if not all([curso, asignatura, id_oa]):
            await websocket.send_json({
                "type": "error",
                "message": "init debe incluir: curso, asignatura, id_oa"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        logger.info(
            f"[live_audio] Sesión iniciada: student={student_id}, "
            f"curso={curso}, asignatura={asignatura}, id_oa={id_oa}"
        )

        # ── 2. Recuperar contexto pedagógico del OA ───────────────────────
        oa_context = await fetch_oa_context_from_supabase(curso, asignatura, id_oa)
        system_prompt = build_live_system_prompt(curso, asignatura, id_oa, oa_context)

        logger.info(f"[live_audio] Prompt del sistema construido ({len(system_prompt)} chars)")

        # Confirmar inicialización al cliente
        await websocket.send_json({
            "type": "init_ack",
            "session_id": session_id,
            "oa_found": oa_context is not None,
            "system_prompt_length": len(system_prompt),
        })

        # ── 3. Abrir sesión Live con Gemini Multimodal Live API ────────────
        if not GEMINI_API_KEY:
            logger.error("[live_audio] GEMINI_API_KEY no configurada")
            await websocket.send_json({
                "type": "error",
                "message": "API key de Gemini no configurada en el servidor"
            })
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        try:
            gemini_client = genai.Client(api_key=GEMINI_API_KEY)

            # Configurar sesión live con el contexto pedagógico como system instruction
            live_session = await gemini_client.aio.live.connect(
                model=GEMINI_LIVE_MODEL,
                config=types.LiveConnectConfig(
                    response_modalities=["audio"],
                    system_instruction=types.Part.from_text(system_prompt),
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Puck"  # Voz alegre y juvenil en español
                            )
                        )
                    ),
                    audio_transcription_config=types.AudioTranscriptionConfig(
                        enabled=True,
                        language_code="es-ES",
                    ),
                ),
            )
            logger.info("[live_audio] Sesión Live de Gemini establecida")

        except Exception as e:
            logger.error(f"[live_audio] Error conectando con Gemini Live: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "message": f"Error conectando con Gemini Live: {str(e)}"
            })
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        # ── 4. Bucle bidireccional de audio ───────────────────────────────
        # Usamos dos tareas asíncronas concurrentes:
        #   - task_recv: recibe audio del cliente → lo envía a Gemini
        #   - task_send: recibe audio de Gemini → lo envía al cliente

        async def receive_from_client():
            """Recibe chunks de audio del cliente y los reenvía a Gemini Live."""
            nonlocal live_session

            while True:
                try:
                    # Esperar mensaje (binario = audio, texto = control)
                    raw = await websocket.receive()

                    if raw["type"] == "websocket.disconnect":
                        logger.info("[live_audio] Cliente desconectado")
                        break

                    # Mensaje binario = chunk de audio del micrófono
                    if "bytes" in raw:
                        audio_bytes = raw["bytes"]
                        # Enviar a Gemini Live como input de audio
                        await live_session.send(
                            types.LiveClientContent(
                                turns=[
                                    types.Content(
                                        role="user",
                                        parts=[types.Part.from_data(
                                            data=audio_bytes,
                                            mime_type="audio/webm;codecs=opus"
                                        )]
                                    )
                                ],
                                turn_complete=True,
                            )
                        )
                    # Mensaje de texto = control/gestión
                    elif "text" in raw:
                        try:
                            msg = json.loads(raw["text"])
                            if msg.get("type") == "ping":
                                await websocket.send_json({"type": "pong"})
                            elif msg.get("type") == "bye":
                                logger.info("[live_audio] Cliente solicitó cierre ordenado")
                                break
                        except json.JSONDecodeError:
                            pass  # Ignorar textos no-JSON

                except WebSocketDisconnect:
                    logger.info("[live_audio] WebSocket desconectado (recv)")
                    break
                except Exception as e:
                    logger.error(f"[live_audio] Error en receive_from_client: {e}", exc_info=True)
                    break

        async def send_to_client():
            """Recibe streaming de audio de Gemini Live y lo retransmite al cliente."""
            nonlocal live_session

            try:
                async for response in live_session.receive():
                    if response is None:
                        continue

                    # Respuesta de audio (Gemini hablando)
                    if response.data:
                        # Enviar chunk de audio binario al cliente
                        await websocket.send_bytes(response.data)

                    # Transcripción de la voz del usuario (si está habilitada)
                    if response.turn_complete:
                        await websocket.send_json({
                            "type": "turn_complete",
                            "session_id": session_id,
                        })

                    # Manejar otros tipos de respuesta
                    if hasattr(response, "server_content") and response.server_content:
                        sc = response.server_content
                        if hasattr(sc, "interrupted") and sc.interrupted:
                            await websocket.send_json({
                                "type": "interrupted",
                                "session_id": session_id,
                            })

            except Exception as e:
                logger.error(f"[live_audio] Error en send_to_client: {e}", exc_info=True)

        # ── Ejecutar ambas direcciones concurrentemente ────────────────────
        await asyncio.gather(
            receive_from_client(),
            send_to_client(),
        )

    except WebSocketDisconnect:
        logger.info(f"[live_audio] Cliente desconectado abruptamente: session={session_id}")

    except Exception as e:
        logger.error(f"[live_audio] Error general en live_audio_endpoint: {e}", exc_info=True)

    finally:
        # ── Limpieza ──────────────────────────────────────────────────────
        if live_session:
            try:
                await live_session.close()
                logger.info("[live_audio] Sesión Live de Gemini cerrada")
            except Exception as e:
                logger.warning(f"[live_audio] Error cerrando sesión Gemini: {e}")

        try:
            if websocket.client_state.name != "DISCONNECTED":
                await websocket.close()
        except Exception:
            pass

        logger.info(
            f"[live_audio] Conexión finalizada: student={student_id}, "
            f"session={session_id}"
        )
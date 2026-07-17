import asyncio
import base64
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict

# Configuración de logging estructurado
logger = logging.getLogger(__name__)

# 🚨 CRÍTICO: Cargar variables de entorno ANTES de importar módulos o agentes locales
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.agents.pedagogic_agent import PedagogicAgent
from app.agents.validator_agent import ValidatorAgent
from app.agents.orchestrator import MasterOrchestrator
from app.models.database import db
from app.models.schemas import ChatInput, CanvasInput, AudioChunkInput
from app.services.curriculum_manager import CurriculumManager
from app.services.dynamic_loader import DynamicLoader
from app.services.tts_service import TTSService
from app.services.gemini_client import default_gemini_client
from app.routers import governance, curriculum, tts, live_audio
from app.api.analytics import router as analytics_router

app = FastAPI(
    title="Super_Profesor API",
    description="Backend para la plataforma educativa multi-agente con Gemini y Supabase (Nivel 4 Auto-Evolutivo)",
    version="1.0.0"
)

# Configuración CORS para producción y desarrollo
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
]
frontend_url = os.getenv("FRONTEND_URL", "").strip()
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

app.include_router(governance.router)
app.include_router(curriculum.router)
app.include_router(analytics_router)
app.include_router(tts.router)
app.include_router(live_audio.router)

curriculum_manager = CurriculumManager()
validator_agent = ValidatorAgent(curriculum_manager)
pedagogic_agent = PedagogicAgent()
tts_service = TTSService(language="es", lang_region="es-mx")
orchestrator = MasterOrchestrator(
    validator_agent=validator_agent,
    pedagogic_agent=pedagogic_agent,
)

@app.on_event("startup")
def startup_event():
    """Carga en caliente las herramientas aprobadas desde Supabase en el arranque."""
    loaded_count = DynamicLoader.load_all_active_tools()
    print(f"[Startup] Carga en caliente finalizada. {loaded_count} herramientas dinámicas activas.")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Super_Profesor (Nivel 4 Auto-Evolutivo)"}

@app.get("/health")
def health_check():
    supabase_status = "Connected" if db.get_client() else "Not Configured"
    return {
        "status": "healthy",
        "supabase_connection": supabase_status,
        "dynamic_tools_loaded": len(DynamicLoader._loaded_tools),
    }

def _generate_audio_response(text: str) -> tuple:
    """
    Genera respuesta de audio desde el texto pedagógico.
    Si falla, retorna (None, None) sin romper el flujo.
    """
    try:
        audio_b64, mime_type = tts_service.text_to_speech(text)
        return audio_b64, mime_type
    except Exception as e:
        logger.error(f"Error generando TTS: {str(e)}", exc_info=True)
        return None, None


def _save_student_progress(supabase_client, payload) -> Optional[dict]:
    progress_payload = {
        "student_id": payload.student_id,
        "curso": payload.curriculum_unit.curso,
        "asignatura": payload.curriculum_unit.asignatura,
        "id_oa": payload.target_oa.id_oa,
        "nivel_logro": payload.student_progress.mastery_level,
        "evaluation_history": payload.student_progress.evaluation_history,
        "aligned_resources": payload.student_progress.aligned_resources,
    }

    try:
        response = supabase_client.table("student_oa_progress").upsert(
            progress_payload,
            on_conflict="student_id,id_oa",
        ).execute()
        return getattr(response, "data", None)
    except Exception as e:
        logger.warning(f"No se pudo guardar progreso del estudiante {payload.student_id}: {str(e)}", exc_info=True)
        return None

@app.post("/api/chat")
async def chat_interaction(chat_request: ChatInput):
    if not chat_request.curso or not chat_request.asignatura:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe especificar curso y asignatura en la petición.",
        )

    supabase_client = db.get_client()

    session_id = None
    history = []

    try:
        # Intentar crear/recuperar sesión solo si Supabase está disponible y las tablas existen
        if supabase_client:
            session_id = getattr(chat_request, "session_id", None)
            if not session_id:
                try:
                    session_res = supabase_client.table("chat_sessions").insert({
                        "student_id": chat_request.student_id,
                        "started_at": datetime.utcnow().isoformat(),
                        "metadata": {"curso": chat_request.curso, "asignatura": chat_request.asignatura}
                    }).execute()
                    session_id = session_res.data[0]["id"]
                except Exception as e:
                    logger.warning(
                        f"No se pudo crear sesión de chat para student_id={chat_request.student_id}: {str(e)}. "
                        "Continuando en modo sin persistencia.",
                        exc_info=True
                    )

            if session_id:
                try:
                    history_res = supabase_client.table("chat_messages") \
                        .select("role, content") \
                        .eq("session_id", session_id) \
                        .order("timestamp", desc=True) \
                        .limit(6) \
                        .execute()
                    if history_res.data:
                        history = []
                        for turn in history_res.data[::-1]:
                            normalized = {
                                "role": turn.get("role", "user"),
                                "text": turn.get("content", ""),
                            }
                            history.append(normalized)
                    else:
                        history = []
                except Exception as e:
                    logger.warning(
                        f"No se pudo recuperar historial de chat para session_id={session_id}: {str(e)}. "
                        "Continuando sin historial.",
                        exc_info=True
                    )
    except Exception as e:
        logger.warning(
            f"Error general al inicializar contexto de chat para student_id={chat_request.student_id}: {str(e)}. "
            "Continuando en modo degradado.",
            exc_info=True
        )

    try:
        # 1. Enrutar a través del orchestrator (flujo multi-agente)
        result = await orchestrator.route(
            student_id=chat_request.student_id,
            message=chat_request.message,
            curso=chat_request.curso,
            asignatura=chat_request.asignatura,
            student_interest=chat_request.student_interest,
            current_topic=chat_request.current_topic,
            id_oa=chat_request.id_oa,
            gemini_file_id=chat_request.gemini_file_id,
        )

        response_text = result["response_text"]

        # 2. Generar TTS si está habilitado
        audio_b64 = None
        audio_mime_type = None
        if chat_request.enable_audio:
            audio_b64, audio_mime_type = _generate_audio_response(response_text)

        # 3. Persistir progreso en Supabase (si hay payload con OA y la tabla existe)
        saved_progress = None
        payload = result.get("payload")
        if supabase_client and payload:
            try:
                saved_progress = _save_student_progress(supabase_client, payload)
            except Exception as e:
                logger.warning(
                    f"Error al guardar progreso en _save_student_progress: {str(e)}",
                    exc_info=True
                )

        return {
            "session_id": session_id,
            "agent_used": result["agent_used"],
            "student_id": chat_request.student_id,
            "response_text": response_text,
            "interactive_exercise": result.get("interactive_exercise"),
            "oa_metadata": result["oa_metadata"],
            "audio_response_b64": audio_b64,
            "audio_mime_type": audio_mime_type,
            "progress_record": result["progress_record"],
            "code_review": result.get("code_review"),
            "saved_progress": saved_progress,
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/api/audio/process-chunk")
async def process_audio_chunk(audio_request: AudioChunkInput):
    """
    Endpoint REST para procesar ráfagas cortas de audio (chunks en Base64).
    
    Recibe el audio del alumno, lo envía a Gemini con el contexto pedagógico
    del OA (curso, asignatura, id_oa) y retorna el audio de respuesta generado.
    
    Este endpoint es la alternativa REST al WebSocket /api/live para cuando
    se requiere una integración más simple (no streaming bidireccional).
    """
    try:
        # 1. Recuperar contexto pedagógico del OA desde Supabase
        oa_context = None
        supabase_client = db.get_client()
        if supabase_client:
            try:
                def _query_oa():
                    return (
                        supabase_client.table("curriculum_objectives")
                        .select("descripcion, conceptos_clave, indicadores_evaluacion")
                        .eq("curso", audio_request.curso)
                        .eq("asignatura", audio_request.asignatura)
                        .eq("id_oa", audio_request.id_oa)
                        .limit(1)
                        .maybe_single()
                        .execute()
                    )
                response = await asyncio.to_thread(_query_oa)
                if response.data:
                    oa_context = response.data
            except Exception as e:
                logger.warning(f"Error consultando OA para audio chunk: {e}")

        # 2. Construir prompt del sistema con contexto MINEDUC
        conceptos = ", ".join(oa_context.get("conceptos_clave", [])) if oa_context else ""
        indicadores = ", ".join(oa_context.get("indicadores_evaluacion", [])) if oa_context else ""
        oa_desc = oa_context.get("descripcion", "") if oa_context else ""

        system_prompt = (
            f"Actúas como Súper Profesor para un alumno de {audio_request.curso} en Chile. "
            f"Asignatura: {audio_request.asignatura}. "
            f"Objetivo de Aprendizaje actual ({audio_request.id_oa}): {oa_desc}. "
            f"{f'Conceptos clave: {conceptos}.' if conceptos else ''} "
            f"{f'Indicadores de evaluación: {indicadores}.' if indicadores else ''} "
            "Mantén un tono sumamente lúdico, empático, usa analogías simples para niños "
            "y fomenta la curiosidad. Responde directamente en formato de audio optimizado "
            "para su reproducción instantánea."
        )

        # 3. Decodificar audio y enviar a Gemini
        audio_bytes = base64.b64decode(audio_request.audio_base64)

        response_text = await default_gemini_client.generate_pedagogic_response(
            system_prompt=system_prompt,
            user_message="[Audio del alumno procesado. Genera una respuesta pedagógica en audio.]",
            temperature=0.4,
        )

        # 4. Generar audio de respuesta con TTS
        audio_b64, mime_type = _generate_audio_response(response_text)

        return {
            "audio_base64": audio_b64 or "",
            "mime_type": mime_type or "audio/mpeg",
            "session_id": audio_request.session_id,
            "transcript": response_text,
        }

    except Exception as e:
        logger.exception(f"Error procesando chunk de audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando audio: {str(e)}",
        )


@app.get("/api/chat/sessions/{student_id}")
async def get_student_sessions(student_id: str):
    """
    Retorna las últimas 10 sesiones del estudiante con su primer mensaje.
    """
    supabase_client = db.get_client()
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    try:
        res = supabase_client.table("chat_sessions") \
            .select("*, chat_messages(content, timestamp)") \
            .eq("student_id", student_id) \
            .order("started_at", desc=True) \
            .limit(10) \
            .execute()

        sessions = []
        for s in res.data:
            # Ordenar mensajes para encontrar el primero
            messages = sorted(s.get("chat_messages", []), key=lambda x: x["timestamp"])
            first_msg = messages[0]["content"] if messages else None
            sessions.append({
                "session_id": s["id"],
                "started_at": s["started_at"],
                "metadata": s["metadata"],
                "first_message": first_msg
            })
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _build_canvas_system_prompt(
    curso: str,
    asignatura: str,
    id_oa: Optional[str] = None,
    oa_metadata: Optional[dict] = None,
) -> str:
    """
    Construye prompt del sistema para análisis de canvas pedagógico.
    """
    oa_context = ""
    if id_oa and oa_metadata:
        concepts = ", ".join(oa_metadata.get("conceptos_clave", []))
        oa_context = f"\nOA objetivo: {id_oa}\nConceptos clave: {concepts}"

    return f"""
Actúa como el Super_Profesor evaluando el cuaderno o pizarra de un alumno de {curso} en {asignatura}.

Tu rol es:
1. Analizar VISUALMENTE el dibujo o escritura del niño en la imagen.
2. Detectar qué conceptos están demostrando comprensión (ej. palitos para contar, figuras geométricas, operaciones).
3. Evaluar el nivel de dominio: emerging (inicial), developing (en desarrollo), proficient (competente), advanced (avanzado).
4. Proporcionar retroalimentación constructiva, empática y motivadora.
5. Asignar una puntuación 0-1 de avance en el aprendizaje.{oa_context}

Responde estructuradamente con: 
- Análisis visual (qué observas)
- Nivel de comprensión detectado
- Feedback pedagógico positivo
- Sugerencias específicas de mejora
""".strip()


def _parse_comprehension_level(text: str) -> str:
    """
    Infiere el nivel de comprensión desde el análisis textual.
    """
    text_lower = text.lower()
    if "avanzado" in text_lower or "muy bien" in text_lower or "excelente" in text_lower:
        return "advanced"
    elif "competente" in text_lower or "correcto" in text_lower or "bien" in text_lower:
        return "proficient"
    elif "desarrollo" in text_lower or "intenta" in text_lower:
        return "developing"
    else:
        return "emerging"


def _extract_mastery_score(text: str) -> float:
    """
    Extrae una puntuación de avance del análisis (0-1).
    Busca palabras clave o números en el texto.
    """
    text_lower = text.lower()
    if "avanzado" in text_lower or "excelente" in text_lower:
        return 0.9
    elif "competente" in text_lower or "bien" in text_lower:
        return 0.7
    elif "desarrollo" in text_lower or "en progreso" in text_lower:
        return 0.5
    else:
        return 0.3


async def _save_canvas_progress(
    supabase_client,
    student_id: str,
    curso: str,
    asignatura: str,
    id_oa: Optional[str],
    comprehension_level: str,
    mastery_advancement: float,
) -> Optional[dict]:
    """
    Guarda el progreso del análisis de canvas en Supabase.
    """
    if not id_oa:
        return None

    try:
        mastery_map = {
            "emerging": "not_started",
            "developing": "in_progress",
            "proficient": "partial",
            "advanced": "mastered",
        }
        new_level = mastery_map.get(comprehension_level, "in_progress")

        progress_payload = {
            "student_id": student_id,
            "curso": curso,
            "asignatura": asignatura,
            "id_oa": id_oa,
            "nivel_logro": new_level,
            "evaluation_history": [
                {
                    "evaluation_type": "canvas_visual_analysis",
                    "timestamp": None,
                    "score": mastery_advancement,
                }
            ],
            "aligned_resources": [],
        }

        response = supabase_client.table("student_oa_progress").upsert(
            progress_payload,
            on_conflict="student_id,id_oa",
        ).execute()
        return getattr(response, "data", None)
    except Exception as e:
        logger.error(f"Error guardando progreso de canvas: {str(e)}", exc_info=True)
        return None


@app.post("/api/canvas/analyze")
async def analyze_canvas(canvas_request: CanvasInput):
    """
    Endpoint para análisis visual de dibujos/escritura del alumno en la pizarra.
    Utiliza Gemini multimodal para interpretar el canvas y generar feedback pedagógico.
    """
    try:
        # Recuperar metadatos del OA si se proporciona id_oa
        oa_metadata = None
        if canvas_request.id_oa:
            oa_metadata = curriculum_manager.get_oa_by_id(canvas_request.id_oa)

        # Construir prompts
        system_prompt = _build_canvas_system_prompt(
            canvas_request.curso,
            canvas_request.asignatura,
            canvas_request.id_oa,
            oa_metadata,
        )

        user_context = f"El alumno ha dibujado lo siguiente. {canvas_request.prompt_adicional or ''}"

        # Analizar imagen con Gemini
        visual_analysis = await default_gemini_client.analyze_canvas_image(
            canvas_b64_data=canvas_request.canvas_data,
            system_prompt=system_prompt,
            user_message=user_context,
            temperature=0.4,
        )

        # Inferir nivel de comprensión y puntuación
        comprehension_level = _parse_comprehension_level(visual_analysis)
        mastery_advancement = _extract_mastery_score(visual_analysis)

        # Generar audio si está habilitado
        audio_b64 = None
        audio_mime_type = None
        if canvas_request.enable_audio:
            audio_b64, audio_mime_type = _generate_audio_response(visual_analysis)

        # Guardar progreso en Supabase
        saved_progress = None
        supabase_client = db.get_client()
        if supabase_client and canvas_request.id_oa:
            saved_progress = await _save_canvas_progress(
                supabase_client,
                canvas_request.student_id,
                canvas_request.curso,
                canvas_request.asignatura,
                canvas_request.id_oa,
                comprehension_level,
                mastery_advancement,
            )

        return {
            "agent": "CanvasVisualAnalyzer",
            "student_id": canvas_request.student_id,
            "id_oa": canvas_request.id_oa,
            "oa_metadata": oa_metadata,
            "visual_analysis": visual_analysis,
            "pedagogic_feedback": visual_analysis,
            "audio_feedback_b64": audio_b64,
            "audio_mime_type": audio_mime_type,
            "comprehension_level": comprehension_level,
            "mastery_advancement": mastery_advancement,
            "saved_progress": saved_progress,
        }

    except Exception as e:
        logger.exception(f"Error en análisis de canvas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

import os
from datetime import datetime
from typing import Optional, List, Dict

# 🚨 CRÍTICO: Cargar variables de entorno ANTES de importar módulos o agentes locales
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, status
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware

from app.agents.pedagogic_agent import PedagogicAgent
from app.agents.validator_agent import ValidatorAgent
from app.agents.orchestrator import MasterOrchestrator
from app.models.database import db
from app.models.schemas import ChatInput, CanvasInput
from app.services.curriculum_manager import CurriculumManager
from app.auth.dependencies import get_current_user
from app.services.dynamic_loader import DynamicLoader
from app.services.tts_service import TTSService
from app.services.gemini_client import default_gemini_client
from app.routers import governance, curriculum
from app.api.analytics import router as analytics_router

app = FastAPI(
    title="Super_Profesor API",
    description="Backend para la plataforma educativa multi-agente con Gemini y Supabase (Nivel 4 Auto-Evolutivo)",
    version="1.0.0"
)

# Configuración extendida de CORS para permitir la conexión fluida con Lovable y entornos locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Habilitado para desarrollo ágil y conexión directa con Lovable Cloud
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(governance.router)
app.include_router(curriculum.router)
app.include_router(analytics_router)

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
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generando TTS: {str(e)}")
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
    except Exception:
        return None

@app.post("/api/chat")
async def chat_interaction(chat_request: ChatInput, current_user_id: str = Depends(get_current_user)):
    if not chat_request.curso or not chat_request.asignatura:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe especificar curso y asignatura en la petición.",
        )

    supabase_client = db.get_client()
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase no configurado")

    # Asegura que el student_id en la petición coincida con el user_id autenticado
    if chat_request.student_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para acceder a sesiones de chat de otros estudiantes"
        )

    try:
        # 1. Recuperar o crear sesión de chat
        session_id = getattr(chat_request, "session_id", None)
        if not session_id:
            session_res = supabase_client.table("chat_sessions").insert({
                "student_id": chat_request.student_id,
                "started_at": datetime.utcnow().isoformat(),
                "metadata": {"curso": chat_request.curso, "asignatura": chat_request.asignatura}
            }).execute()
            session_id = session_res.data[0]["id"]

        # 2. Recuperar historial de la sesión (últimos 6 mensajes)
        history_res = supabase_client.table("chat_messages") \
            .select("role, content") \
            .eq("session_id", session_id) \
            .order("timestamp", desc=True) \
            .limit(6) \
            .execute()
        history = history_res.data[::-1] if history_res.data else []

        # 3. Registrar mensaje del usuario
        supabase_client.table("chat_messages").insert({
            "session_id": session_id,
            "role": "user",
            "content": chat_request.message,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()

        # 4. Enrutar a través del orchestrator (flujo multi-agente)
        result = await orchestrator.route(
            student_id=chat_request.student_id,
            message=chat_request.message,
            curso=chat_request.curso,
            asignatura=chat_request.asignatura,
            history=history,
            student_interest=chat_request.student_interest,
            current_topic=chat_request.current_topic,
        )

        response_text = result["response_text"]

        # 5. Registrar respuesta del asistente
        supabase_client.table("chat_messages").insert({
            "session_id": session_id,
            "role": "assistant",
            "content": response_text,
            "agent_used": result["agent_used"],
            "timestamp": datetime.utcnow().isoformat()
        }).execute()

        # 6. Generar TTS si está habilitado
        audio_b64 = None
        audio_mime_type = None
        if chat_request.enable_audio:
            audio_b64, audio_mime_type = _generate_audio_response(response_text)

        # 7. Persistir progreso en Supabase (si hay payload con OA)
        saved_progress = None
        payload = result.get("payload")
        if payload:
            saved_progress = _save_student_progress(supabase_client, payload)

        return {
            "session_id": session_id,
            "agent_used": result["agent_used"],
            "student_id": chat_request.student_id,
            "response_text": response_text,
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


@app.get("/api/chat/sessions/{student_id}")
async def get_student_sessions(student_id: str, current_user_id: str = Depends(get_current_user)):
    """
    Retorna las últimas 10 sesiones del estudiante con su primer mensaje.
    """
    supabase_client = db.get_client()
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    # Asegura que el student_id en la ruta coincida con el user_id autenticado
    if student_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para acceder a sesiones de chat de otros estudiantes"
        )
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
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error guardando progreso de canvas: {str(e)}")
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
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Error en análisis de canvas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
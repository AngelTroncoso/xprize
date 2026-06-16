import os
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.agents.pedagogic_agent import PedagogicAgent
from app.agents.validator_agent import ValidatorAgent
from app.models.database import db
from app.models.schemas import ChatInput
from app.services.curriculum_manager import CurriculumManager
from app.services.dynamic_loader import DynamicLoader
from app.routers import governance, curriculum
from app.api.analytics import router as analytics_router

app = FastAPI(
    title="Super_Profesor API",
    description="Backend para la plataforma educativa multi-agente con Gemini y Supabase (Nivel 4 Auto-Evolutivo)",
    version="1.0.0"
)

frontend_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if os.getenv("FRONTEND_URL"):
    frontend_origins.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
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
async def chat_interaction(chat_request: ChatInput):
    if not chat_request.curso or not chat_request.asignatura:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe especificar curso y asignatura en la petición.",
        )

    try:
        payload = await validator_agent.analyze_student_input(
            student_id=chat_request.student_id,
            student_message=chat_request.message,
            curso=chat_request.curso,
            asignatura=chat_request.asignatura,
        )

        response_text = await pedagogic_agent.generate_lesson(payload, chat_request.message)

        saved_progress = None
        supabase_client = db.get_client()
        if supabase_client:
            saved_progress = _save_student_progress(supabase_client, payload)

        return {
            "agent": "PedagogicAgent",
            "student_id": chat_request.student_id,
            "oa_metadata": {
                "id_oa": payload.target_oa.id_oa,
                "descripcion": payload.target_oa.descripcion,
                "conceptos_clave": payload.target_oa.conceptos_clave,
                "indicadores_evaluacion": payload.target_oa.indicadores_evaluacion,
                "curso": payload.curriculum_unit.curso,
                "asignatura": payload.curriculum_unit.asignatura,
            },
            "pedagogic_response": response_text,
            "progress_record": payload.student_progress.model_dump(),
            "saved_progress": saved_progress,
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

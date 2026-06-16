from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import ChatInput
from app.agents.orchestrator import MasterOrchestrator
from app.models.database import db
from app.services.dynamic_loader import DynamicLoader
from app.routers import governance

app = FastAPI(
    title="Super_Profesor API",
    description="Backend para la plataforma educativa multi-agente con Gemini y Supabase (Nivel 4 Auto-Evolutivo)",
    version="1.0.0"
)

# Habilitar CORS para conectar con el frontend de Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción cambiar por la URL del frontend en Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(governance.router)

orchestrator = MasterOrchestrator()

@app.on_event("startup")
def startup_event():
    """Al iniciar la aplicación, carga en caliente todas las herramientas aprobadas de la DB."""
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
        "dynamic_tools_loaded": len(DynamicLoader._loaded_tools)
    }

@app.post("/api/chat")
async def chat_interaction(chat_input: ChatInput):
    try:
        result = orchestrator.process_student_input(chat_input)
        
        # Opcional: Guardar en base de datos si Supabase está configurado
        supabase_client = db.get_client()
        if supabase_client:
            # Registrar el mensaje en la tabla chat_messages
            pass
            
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

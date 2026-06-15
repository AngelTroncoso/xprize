from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import ChatInput
from app.agents.orchestrator import MasterOrchestrator
from app.models.database import db

app = FastAPI(
    title="Super_Profesor API",
    description="Backend para la plataforma educativa multi-agente con Gemini y Supabase",
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

orchestrator = MasterOrchestrator()

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Super_Profesor"}

@app.get("/health")
def health_check():
    supabase_status = "Connected" if db.get_client() else "Not Configured"
    return {
        "status": "healthy",
        "supabase_connection": supabase_status
    }

@app.post("/api/chat")
async def chat_interaction(chat_input: ChatInput):
    try:
        result = orchestrator.process_student_input(chat_input)
        
        # Opcional: Guardar en base de datos si Supabase está configurado
        supabase_client = db.get_client()
        if supabase_client:
            # Registrar el mensaje en la tabla chat_messages
            # en un flujo completo registraríamos tanto el user message como el assistant response
            pass
            
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

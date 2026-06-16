from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from app.models.database import db
from app.services.dynamic_loader import DynamicLoader

router = APIRouter(prefix="/api/governance", tags=["Gobernanza & HITL"])

class ApprovalRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None
    reviewer_id: Optional[str] = None

@router.get("/approvals")
def get_pending_approvals():
    """Obtiene la lista de herramientas dinámicas pendientes de revisión por parte de profesores/admin."""
    supabase_client = db.get_client()
    if not supabase_client:
        # Modo desarrollo / mock si Supabase no está configurado
        return [
            {
                "id": "mock-id-1",
                "tool_name": "validate_fibonacci",
                "description": "Valida lógica de Fibonacci",
                "code": "def validate_fibonacci(INPUT_DATA):\n    return 'mock'",
                "status": "pending"
            }
        ]

    try:
        response = supabase_client.table("tool_approvals").select("*").eq("status", "pending").execute()
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve/{approval_id}")
def process_approval(approval_id: str, request: ApprovalRequest):
    """
    Aprueba o rechaza una herramienta generada por IA.
    Si se aprueba, se compila e inyecta dinámicamente en memoria (sys.modules)
    y se registra en la tabla de herramientas activas.
    """
    supabase_client = db.get_client()
    
    # 1. Recuperar la herramienta de la base de datos o simular
    tool_data = None
    if not supabase_client:
        if approval_id == "mock-id-1":
            tool_data = {
                "tool_name": "validate_fibonacci",
                "code": "def validate_fibonacci(INPUT_DATA):\n    return True",
                "description": "Valida lógica de Fibonacci"
            }
    else:
        try:
            response = supabase_client.table("tool_approvals").select("*").eq("id", approval_id).single().execute()
            tool_data = response.data
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Aprobación no encontrada: {e}")

    if not tool_data:
        raise HTTPException(status_code=404, detail="Herramienta de aprobación no encontrada.")

    # 2. Registrar decisión
    status_str = "approved" if request.approved else "rejected"
    
    if supabase_client:
        try:
            # Actualizar estado de aprobación
            supabase_client.table("tool_approvals").update({
                "status": status_str,
                "feedback": request.feedback,
                "reviewed_by": request.reviewer_id
            }).eq("id", approval_id).execute()
            
            if request.approved:
                # Insertar en dynamic_tools para persistencia de carga en futuros arranques
                supabase_client.table("dynamic_tools").insert({
                    "name": tool_data["tool_name"],
                    "description": tool_data["description"],
                    "code": tool_data["code"],
                    "author_agent": "EvolutionEngine"
                }).execute()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fallo al actualizar base de datos: {e}")

    # 3. Si se aprueba, cargar en caliente en el intérprete
    if request.approved:
        try:
            DynamicLoader.load_tool_from_code(tool_data["code"], tool_data["tool_name"])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Herramienta aprobada pero falló compilación en caliente: {str(e)}"
            )

    return {
        "status": status_str,
        "tool_name": tool_data["tool_name"],
        "message": f"Herramienta marcada como {status_str} exitosamente."
    }

@router.get("/metrics")
def get_system_metrics():
    """Devuelve métricas de confiabilidad, AgentOps y calificaciones del Juez."""
    supabase_client = db.get_client()
    if not supabase_client:
        return {
            "avg_judge_score": 4.5,
            "total_traces": 15,
            "active_dynamic_tools": list(DynamicLoader._loaded_tools.keys()),
            "system_health": "Healthy (Local Mock Mode)"
        }

    try:
        # Traer total de trazas
        traces_count = supabase_client.table("agent_traces").select("id", count="exact").execute()
        
        # Traer promedio del Juez
        judge_res = supabase_client.table("judge_evaluations").select("score").execute()
        scores = [item["score"] for item in judge_res.data] if judge_res.data else []
        avg_score = sum(scores) / len(scores) if scores else 5.0
        
        return {
            "avg_judge_score": round(avg_score, 2),
            "total_traces": traces_count.count or 0,
            "active_dynamic_tools": list(DynamicLoader._loaded_tools.keys()),
            "system_health": "Healthy (Supabase Connected)"
        }
    except Exception as e:
        return {
            "error": str(e),
            "active_dynamic_tools": list(DynamicLoader._loaded_tools.keys()),
            "system_health": "Degraded"
        }

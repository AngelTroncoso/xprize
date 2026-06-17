"""
Router para exponer el currículo oficial de MINEDUC Chile y el progreso de estudiantes.
Alineado con la estructura JSON ingestada en curriculum_data.json
"""

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.services.curriculum_manager import CurriculumManager
from app.models.database import db
from app.models.schemas import OAProgressRecord

router = APIRouter(prefix="/api/curriculum", tags=["Currículo MINEDUC"])

# Instanciar el gestor curricular (carga y indexa automáticamente)
curriculum_manager = CurriculumManager()


def _validate_student_uuid(student_id: str) -> str:
    try:
        return str(UUID(str(student_id)))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="student_id debe ser un UUID válido compatible con Supabase.",
        )

# ============================================
# ENDPOINTS DE CONSULTA CURRICULAR
# ============================================

@router.get("/oas")
def get_all_oas(
    curso: Optional[str] = Query(None, description="Filtrar por curso (ej. '3ro Basico')"),
    asignatura: Optional[str] = Query(None, description="Filtrar por asignatura (ej. 'Matematica')")
):
    """
    Obtiene todos los Objetivos de Aprendizaje, opcionalmente filtrados.
    
    **Ejemplo sin filtros**: `GET /api/curriculum/oas`
    Retorna: Lista de 11 OA de 3ro Básico - Matemática
    
    **Ejemplo con filtros**: `GET /api/curriculum/oas?curso=3ro Basico&asignatura=Matematica`
    Retorna: Los 11 OA filtrados
    """
    if curso and asignatura:
        oas = curriculum_manager.search_oa_by_course_and_subject(curso, asignatura)
        return {
            "curso": curso,
            "asignatura": asignatura,
            "total_count": len(oas),
            "objetivos_aprendizaje": oas
        }
    
    # Si no hay filtros, retorna toda la estructura curricular
    return {
        "total_units": len(curriculum_manager.curriculum_data),
        "curriculum": curriculum_manager.curriculum_data
    }

@router.get("/oas/{oa_id}")
def get_oa_details(oa_id: str):
    """
    Obtiene los detalles completos de un OA específico.
    
    **Estructura retornada**:
    - `id_oa`: Identificador único
    - `curso`: Grado/curso
    - `asignatura`: Nombre de la asignatura
    - `eje_tematico`: Eje temático
    - `descripcion`: Descripción oficial
    - `indicadores_evaluacion`: Criterios de evaluación (usado por Agente Evaluador)
    - `conceptos_clave`: Conceptos fundamentales (usado por Agente Pedagógico)
    """
    oa_data = curriculum_manager.get_oa_by_id(oa_id)
    if not oa_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Objetivo de Aprendizaje '{oa_id}' no encontrado en el currículo oficial"
        )
    return oa_data

@router.get("/oas/{oa_id}/evaluation-indicators")
def get_evaluation_indicators(oa_id: str):
    """
    Obtiene SOLO los indicadores de evaluación de un OA.
    
    Estos son los ÚNICOS criterios válidos que debe usar el Agente Evaluador.
    """
    indicators = curriculum_manager.get_evaluation_indicators(oa_id)
    if not indicators:
        oa = curriculum_manager.get_oa_by_id(oa_id)
        if not oa:
            raise HTTPException(status_code=404, detail=f"OA '{oa_id}' no encontrado")
        # Si el OA existe pero no tiene indicadores, retorna lista vacía
        return {"id_oa": oa_id, "indicadores_evaluacion": []}
    
    return {
        "id_oa": oa_id,
        "indicadores_evaluacion": indicators
    }

@router.get("/oas/{oa_id}/key-concepts")
def get_key_concepts(oa_id: str):
    """
    Obtiene los conceptos clave que el alumno debe dominar para este OA.
    
    Usado por:
    - Agente Pedagógico: para diseñar analogías y ejercicios específicos
    - Agente Evaluador: para validar comprensión de conceptos
    """
    concepts = curriculum_manager.get_key_concepts(oa_id)
    if not concepts:
        oa = curriculum_manager.get_oa_by_id(oa_id)
        if not oa:
            raise HTTPException(status_code=404, detail=f"OA '{oa_id}' no encontrado")
        return {"id_oa": oa_id, "conceptos_clave": []}
    
    return {
        "id_oa": oa_id,
        "conceptos_clave": concepts
    }

@router.get("/search")
def search_oas(
    concept: Optional[str] = Query(None, description="Buscar OA por concepto clave")
):
    """
    Busca OA por concepto clave (búsqueda fuzzy).
    
    **Ejemplo**: `GET /api/curriculum/search?concept=multiplicacion`
    Retorna: Lista de OA que contienen 'multiplicacion' en sus conceptos_clave
    """
    if not concept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar el parámetro 'concept' para buscar"
        )
    
    oa_ids = curriculum_manager.search_oa_by_concept(concept)
    oa_list = [curriculum_manager.get_oa_by_id(oa_id) for oa_id in oa_ids]
    
    return {
        "query": concept,
        "total_results": len(oa_list),
        "resultados": oa_list
    }

# ============================================
# ENDPOINTS DE PROGRESO DE ESTUDIANTE
# ============================================

@router.get("/student/{student_id}/progress")
def get_student_progress(student_id: str):
    """
    Obtiene el progreso del estudiante en TODOS los OA del currículo.
    
    **Estructura retornada** (para graficar):
    ```json
    {
      "student_id": "STU_001",
      "curso": "3ro Basico",
      "asignatura": "Matematica",
      "progress_by_oa": {
        "OA_01": {
          "id_oa": "OA_01",
          "mastery_level": "mastered",
          "last_evaluation_date": "2026-06-15",
          "evaluation_count": 3
        },
        "OA_02": {
          "id_oa": "OA_02",
          "mastery_level": "partial",
          "last_evaluation_date": "2026-06-14",
          "evaluation_count": 2
        }
      },
      "summary": {
        "total_oas": 11,
        "mastered": 5,
        "partial": 3,
        "in_progress": 2,
        "not_started": 1,
        "overall_mastery_percentage": 65
      }
    }
    ```
    """
    student_id = _validate_student_uuid(student_id)
    supabase_client = db.get_client()
    
    if not supabase_client:
        # Modo desarrollo: retorna datos simulados
        return _mock_student_progress(student_id)
    
    try:
        # Obtener registros de progreso del estudiante desde Supabase
        response = supabase_client.table("student_oa_progress").select("*").eq(
            "student_id", student_id
        ).execute()
        
        progress_records = {rec["id_oa"]: rec for rec in response.data}
        
        # Construir estructura para el frontend
        return _build_progress_response(student_id, progress_records)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/student/{student_id}/next-topic")
def recommend_next_topic(student_id: str):
    """
    Recomienda el siguiente OA a trabajar basado en el progreso actual.
    
    **Lógica**:
    1. Busca OA en estado "partial" (reforzar)
    2. Si no hay, busca el primer "not_started" con prerequisitos completados
    3. Si todos están dominados, sugiere OA de expansión
    """
    student_id = _validate_student_uuid(student_id)
    supabase_client = db.get_client()
    
    if not supabase_client:
        return {
            "student_id": student_id,
            "recommended_oa_id": "OA_04",
            "reason": "Siguiente en secuencia curricular (desarrollo)"
        }
    
    try:
        # Obtener progreso actual
        response = supabase_client.table("student_oa_progress").select("*").eq(
            "student_id", student_id
        ).execute()
        
        progress_map = {
            rec["id_oa"]: rec.get("nivel_logro", rec.get("mastery_level", "not_started"))
            for rec in response.data
        }
        
        # 1. Buscar OA en "partial"
        for oa_id, oa_data in curriculum_manager._oa_index.items():
            if progress_map.get(oa_id) == "partial":
                return {
                    "student_id": student_id,
                    "recommended_oa_id": oa_id,
                    "reason": "Reforzar - OA parcialmente dominado",
                    "oa_data": oa_data
                }
        
        # 2. Buscar primer "not_started"
        for oa_id in sorted(curriculum_manager._oa_index.keys()):
            if progress_map.get(oa_id) != "mastered":
                oa_data = curriculum_manager.get_oa_by_id(oa_id)
                return {
                    "student_id": student_id,
                    "recommended_oa_id": oa_id,
                    "reason": "Nuevo - Siguiente en secuencia",
                    "oa_data": oa_data
                }
        
        # 3. Todos dominados
        return {
            "student_id": student_id,
            "recommended_oa_id": None,
            "reason": "¡Todos los OA dominados! Felicidades."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# HELPER FUNCTIONS
# ============================================

def _build_progress_response(student_id: str, progress_records: Dict[str, Any]) -> Dict[str, Any]:
    """Construye la respuesta de progreso estructurada para el frontend."""
    
    # Mapear estado de cada OA
    progress_by_oa = {}
    mastery_counts = {
        "mastered": 0,
        "partial": 0,
        "in_progress": 0,
        "not_started": 0
    }
    
    for oa_id, oa_data in curriculum_manager._oa_index.items():
        rec = progress_records.get(oa_id, {})
        mastery = rec.get("nivel_logro", rec.get("mastery_level", "not_started"))
        
        progress_by_oa[oa_id] = {
            "id_oa": oa_id,
            "descripcion": oa_data.get("descripcion"),
            "mastery_level": mastery,
            "last_evaluation_date": rec.get("last_evaluation_date"),
            "evaluation_count": len(rec.get("evaluation_history", []))
        }
        
        mastery_counts[mastery] += 1
    
    total_oas = len(progress_by_oa)
    overall_percentage = round(
        (mastery_counts["mastered"] * 100) / total_oas
    ) if total_oas > 0 else 0
    
    return {
        "student_id": student_id,
        "curso": "3ro Basico",
        "asignatura": "Matematica",
        "progress_by_oa": progress_by_oa,
        "summary": {
            "total_oas": total_oas,
            **mastery_counts,
            "overall_mastery_percentage": overall_percentage
        }
    }

def _mock_student_progress(student_id: str) -> Dict[str, Any]:
    """Retorna datos simulados de progreso para modo desarrollo."""
    return {
        "student_id": student_id,
        "curso": "3ro Basico",
        "asignatura": "Matematica",
        "progress_by_oa": {
            "OA_01": {"id_oa": "OA_01", "mastery_level": "mastered", "evaluation_count": 3},
            "OA_02": {"id_oa": "OA_02", "mastery_level": "mastered", "evaluation_count": 2},
            "OA_03": {"id_oa": "OA_03", "mastery_level": "partial", "evaluation_count": 2},
            "OA_04": {"id_oa": "OA_04", "mastery_level": "in_progress", "evaluation_count": 1},
            "OA_05": {"id_oa": "OA_05", "mastery_level": "not_started", "evaluation_count": 0},
            "OA_06": {"id_oa": "OA_06", "mastery_level": "not_started", "evaluation_count": 0},
            "OA_07": {"id_oa": "OA_07", "mastery_level": "not_started", "evaluation_count": 0},
            "OA_08": {"id_oa": "OA_08", "mastery_level": "not_started", "evaluation_count": 0},
            "OA_09": {"id_oa": "OA_09", "mastery_level": "not_started", "evaluation_count": 0},
            "OA_10": {"id_oa": "OA_10", "mastery_level": "not_started", "evaluation_count": 0},
            "OA_11": {"id_oa": "OA_11", "mastery_level": "not_started", "evaluation_count": 0},
        },
        "summary": {
            "total_oas": 11,
            "mastered": 2,
            "partial": 1,
            "in_progress": 1,
            "not_started": 7,
            "overall_mastery_percentage": 18
        }
    }

import json
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class CrossValidationResult(BaseModel):
    oa_id: str = Field(..., description="ID del Objetivo de Aprendizaje (OA) de Mineduc Chile")
    enrichment_analogies: List[str] = Field(..., description="Analogías pedagógicas sugeridas para enriquecer el OA")
    academic_prerequisites: List[str] = Field(..., description="Prerrequisitos académicos implícitos o no declarados")
    remediation_strategies: List[str] = Field(..., description="Estrategias de nivelación para alumnos rezagados en este OA")
    confidence_score: float = Field(..., description="Puntuación de alineación de la fuente (0.0 a 1.0)")

class StructuredLesson(BaseModel):
    oa_id: str = Field(..., description="ID del OA de Mineduc Chile correspondiente")
    grade: str = Field(..., description="Curso (ej. 5° Básico)")
    subject: str = Field(..., description="Asignatura (ej. Matemáticas)")
    lesson_title: str = Field(..., description="Título de la lección estructurada")
    pedagogical_sequence: List[str] = Field(..., description="Secuencia de pasos o momentos pedagógicos")
    analogies: List[str] = Field(..., description="Analogías adaptadas para el aula")
    evaluation_indicators: List[str] = Field(..., description="Indicadores específicos de evaluación")

class CurriculumManager:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "dummy-key")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3.5-flash"
        self._source_priority_index: Dict[str, float] = {}
        
        # Cargar y indexar currículo oficial
        self.curriculum_data = self._load_curriculum()
        self._oa_index: Dict[str, Dict[str, Any]] = self._build_oa_index()

    def _load_curriculum(self) -> List[Dict[str, Any]]:
        """Carga el JSON curricular oficial de MINEDUC desde el almacenamiento local."""
        curriculum_path = os.path.join(
            os.path.dirname(__file__),
            "../models/curriculum_data.json"
        )
        if os.path.exists(curriculum_path):
            with open(curriculum_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _build_oa_index(self) -> Dict[str, Dict[str, Any]]:
        """
        Construye un índice rápido de búsqueda para todos los OA.
        Estructura: { "OA_01": {curso, asignatura, eje_tematico, ...datos_oa} }
        """
        index = {}
        for unit in self.curriculum_data:
            for oa in unit.get("objetivos_aprendizaje", []):
                oa_id = oa.get("id_oa")
                if oa_id:
                    index[oa_id] = {
                        "curso": unit.get("curso"),
                        "asignatura": unit.get("asignatura"),
                        "eje_tematico": unit.get("eje_tematico"),
                        **oa  # Spread: id_oa, descripcion, indicadores_evaluacion, conceptos_clave
                    }
        return index

    def get_oa_by_id(self, oa_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves complete OA data by ID. Returns None if not found."""
        return self._oa_index.get(oa_id)

    def get_evaluation_indicators(self, oa_id: str) -> List[str]:
        """
        Devuelve los indicadores de evaluación específicos de un OA.
        Estos son los ÚNICOS criterios válidos para evaluar dominio.
        """
        oa = self.get_oa_by_id(oa_id)
        if oa:
            return oa.get("indicadores_evaluacion", [])
        return []

    def get_key_concepts(self, oa_id: str) -> List[str]:
        """Devuelve los conceptos clave que el alumno debe dominar para este OA."""
        oa = self.get_oa_by_id(oa_id)
        if oa:
            return oa.get("conceptos_clave", [])
        return []

    def search_oa_by_course_and_subject(self, curso: str, asignatura: str) -> List[Dict[str, Any]]:
        """Busca todos los OA de un curso y asignatura específicos."""
        results = []
        for oa_id, oa_data in self._oa_index.items():
            if oa_data.get("curso") == curso and oa_data.get("asignatura") == asignatura:
                results.append(oa_data)
        return results

    def search_oa_by_concept(self, concept: str) -> List[str]:
        """Busca todos los OA que incluyan un concepto clave específico (búsqueda fuzzy)."""
        concept_lower = concept.lower()
        results = []
        for oa_id, oa_data in self._oa_index.items():
            conceptos = [c.lower() for c in oa_data.get("conceptos_clave", [])]
            if any(concept_lower in c or c in concept_lower for c in conceptos):
                results.append(oa_id)
        return results

    def cross_validate_sources(self, official_oa_json: Dict[str, Any], complementary_md_text: str) -> CrossValidationResult:
        """
        Contrasta la información de una fuente complementaria (.md) con un OA oficial de Mineduc (JSON).
        Identifica oportunidades de enriquecimiento, prerrequisitos académicos y estrategias de remediación.
        """
        prompt = f"""
        Actúa como el Director Curricular y Gestor de Conocimiento de Super_Profesor.
        Tu misión es validar de forma cruzada y contrastar un Objetivo de Aprendizaje (OA) oficial de Mineduc Chile con una fuente de texto complementaria.
        
        OA Oficial (JSON):
        {json.dumps(official_oa_json, indent=2, ensure_ascii=False)}
        
        Texto Complementario (Markdown):
        {complementary_md_text}
        
        Determina:
        a) Si enriquece el concepto con mejores analogías.
        b) Si añade prerrequisitos académicos implícitos.
        c) Si ofrece estrategias de remediación para alumnos rezagados.
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CrossValidationResult,
                temperature=0.2
            )
        )
        return response.parsed

    def generate_aligned_lesson(
        self, 
        grade: str, 
        subject: str, 
        oa_id: str, 
        official_oa_details: Dict[str, Any], 
        student_interest: str
    ) -> StructuredLesson:
        """
        Genera un plan de clase estructurado alineado explícitamente a los OA chilenos.
        """
        prompt = f"""
        Actúa como el Director Curricular de Super_Profesor. Genera un plan de clase adaptado para {grade} en {subject}.
        Debe alinearse con el ID del OA chileno: {oa_id}.
        
        Detalles Oficiales del OA:
        {json.dumps(official_oa_details, indent=2, ensure_ascii=False)}
        
        Interés del Alumno para Personalización:
        {student_interest}
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StructuredLesson,
                temperature=0.5
            )
        )
        return response.parsed

    def update_source_priority(self, source_name: str, performance_score: float):
        """Ajusta dinámicamente la prioridad de una fuente según el feedback de comprensión."""
        current = self._source_priority_index.get(source_name, 1.0)
        # Ajuste ponderado simple
        self._source_priority_index[source_name] = round((current * 0.7) + (performance_score * 0.3), 2)

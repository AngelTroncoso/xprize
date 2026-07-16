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
        
        self.use_local_fallback = os.getenv("USE_LOCAL_FALLBACK", "").strip().lower() in ("1", "true", "yes")
        
        # Cargar e indexar currículo oficial
        self.curriculum_data = self._load_curriculum()
        self._oa_index: Dict[str, Dict[str, Any]] = self._build_oa_index()

        # DEBUG: confirmar carga real
        print(f"[CurriculumManager] units={len(self.curriculum_data)} index={len(self._oa_index)} keys={list(self._oa_index.keys())[:10]}")

    def _load_curriculum(self) -> List[Dict[str, Any]]:
        """Carga el curriculo oficial de MINEDUC desde Supabase o almacenamiento local."""
        # 1. Intentar desde Supabase
        supabase_curriculum = self._load_curriculum_from_supabase()
        if supabase_curriculum:
            return supabase_curriculum

        # 2. Fallback: archivo JSON estructurado (malla_curricular_oficial.json)
        official_path = os.path.join(
            os.path.dirname(__file__),
            "../data/mallas_mineduc/malla_curricular_oficial.json"
        )
        if os.path.exists(official_path):
            with open(official_path, 'r', encoding='utf-8') as f:
                official_records = json.load(f)
            # Validar formato: lista de unidades estructuradas
            if official_records and isinstance(official_records[0], dict) and "objetivos_aprendizaje" in official_records[0]:
                print("[CurriculumManager] Cargando malla OFICIAL desde malla_curricular_oficial.json...")
                return official_records
            # Si no, intentar convertir asumiendo que es plano
            elif official_records and isinstance(official_records[0], dict) and "codigo_oa" in official_records[0]:
                print("[CurriculumManager] Cargando malla plana desde malla_curricular_oficial.json...")
                return self._convert_flat_to_units(official_records)

        # 3. Fallback: archivo JSON legacy (con objetivos_aprendizaje)
        curriculum_path = os.path.join(
            os.path.dirname(__file__),
            "../models/curriculum_data.json"
        )
        if os.path.exists(curriculum_path):
            with open(curriculum_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        return []

    @staticmethod
    def _convert_flat_to_units(flat_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convierte un listado plano (curso, asignatura, eje, codigo_oa, descripcion_oa)
        a la estructura de unidades esperada por _build_oa_index."""
        from collections import OrderedDict
        units_map: Dict[str, Dict[str, Any]] = OrderedDict()

        for rec in flat_records:
            curso = rec.get("curso", "")
            asignatura = rec.get("asignatura", "")
            eje = rec.get("eje", "")
            key = f"{curso}|{asignatura}|{eje}"

            if key not in units_map:
                units_map[key] = {
                    "curso": curso,
                    "asignatura": asignatura,
                    "eje_tematico": eje,
                    "objetivos_aprendizaje": [],
                }

            units_map[key]["objetivos_aprendizaje"].append({
                "id_oa": rec.get("codigo_oa", ""),
                "descripcion": rec.get("descripcion_oa", ""),
                "indicadores_evaluacion": [],
                "conceptos_clave": [],
            })

        return list(units_map.values())

    def _load_curriculum_from_supabase(self) -> List[Dict[str, Any]]:
        if self.use_local_fallback:
            return []

        try:
            from app.models.database import db

            supabase_client = db.get_client()
            if not supabase_client:
                return []

            units_response = supabase_client.table("curriculum_units").select("*").execute()
            objectives_response = supabase_client.table("curriculum_objectives").select("*").execute()
        except Exception:
            return []

        units = getattr(units_response, "data", []) or []
        objectives = getattr(objectives_response, "data", []) or []
        objectives_by_unit: Dict[str, List[Dict[str, Any]]] = {}
        for objective in objectives:
            unit_id = objective.get("unit_id")
            if not unit_id:
                continue
            objectives_by_unit.setdefault(unit_id, []).append({
                "id_oa": objective.get("id_oa"),
                "descripcion": objective.get("descripcion"),
                "indicadores_evaluacion": objective.get("indicadores_evaluacion") or [],
                "conceptos_clave": objective.get("conceptos_clave") or [],
            })

        curriculum: List[Dict[str, Any]] = []
        for unit in units:
            unit_id = unit.get("id")
            curriculum.append({
                "curso": unit.get("curso"),
                "asignatura": unit.get("asignatura"),
                "eje_tematico": unit.get("eje_tematico"),
                "objetivos_aprendizaje": objectives_by_unit.get(unit_id, []),
            })
        return curriculum

    def _build_oa_index(self) -> Dict[str, Dict[str, Any]]:
        """
        Construye un índice rápido de búsqueda para todos los OA.
        Usa clave compuesta ``"{id_oa}|{curso}|{asignatura}"`` para soportar
        códigos de OA repetidos entre cursos/asignaturas (ej. OA_01 en 1° y 5° básico).
        """
        index = {}
        for unit in self.curriculum_data:
            for oa in unit.get("objetivos_aprendizaje", []):
                oa_id = oa.get("id_oa")
                if not oa_id:
                    continue
                key = f"{oa_id}|{unit.get('curso','')}|{unit.get('asignatura','')}"
                index[key] = {
                    "curso": unit.get("curso"),
                    "asignatura": unit.get("asignatura"),
                    "eje_tematico": unit.get("eje_tematico"),
                    **oa
                }
        return index

    def get_oa_by_id(
        self,
        oa_id: str,
        curso: Optional[str] = None,
        asignatura: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves complete OA data by ID.

        Flexible con búsquedas:
        - Si ``oa_id`` contiene ``|`` (clave compuesta tipo ``"OA_01|5° Básico|Matemáticas"``),
          se busca directamente en el índice.
        - Si ``oa_id`` es un ID simple (ej. ``"OA_01"``), se busca de forma eficiente
          y se retorna la primera coincidencia. Opcionalmente se pueden pasar
          ``curso`` y ``asignatura`` para desambiguar cuando existan duplicados.

        Returns ``None`` si no se encuentra ninguna coincidencia.
        """
        # Búsqueda directa por clave compuesta (más rápida)
        if "|" in oa_id:
            return self._oa_index.get(oa_id)

        # Búsqueda por ID simple: iterar sobre el índice
        # (el tamaño del índice es reducido, del orden de ~87 OAs)
        oa_id_lower = oa_id.strip().lower()
        matches: List[Dict[str, Any]] = []

        for key, value in self._oa_index.items():
            # Extraer el id_oa del inicio de la clave compuesta
            stored_oa_id = key.split("|", 1)[0]
            if stored_oa_id.strip().lower() != oa_id_lower:
                continue

            # Si hay filtros de curso/asignatura, usarlos para desambiguar
            if curso is not None:
                if value.get("curso", "").strip().lower() != curso.strip().lower():
                    continue
            if asignatura is not None:
                if value.get("asignatura", "").strip().lower() != asignatura.strip().lower():
                    continue

            matches.append(value)

        # Retornar la primera coincidencia; si no hay, None
        return matches[0] if matches else None

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
        import unicodedata
        curso_norm = unicodedata.normalize("NFC", curso)
        asig_norm = unicodedata.normalize("NFC", asignatura)
        results = []
        for oa_id, oa_data in self._oa_index.items():
            stored_curso = unicodedata.normalize("NFC", oa_data.get("curso", ""))
            stored_asig = unicodedata.normalize("NFC", oa_data.get("asignatura", ""))
            if stored_curso == curso_norm and stored_asig == asig_norm:
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

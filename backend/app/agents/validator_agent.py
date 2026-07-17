import re
from typing import Any, Dict, List, Optional

from app.models.schemas import (
    CurriculumUnit,
    ObjetivoAprendizaje,
    OAProgressRecord,
    ValidatorToPedagoguePayload,
)
from app.services.curriculum_manager import CurriculumManager
from app.services.gemini_client import GeminiClient, default_gemini_client


class ValidatorAgent:
    def __init__(
        self,
        curriculum_manager: CurriculumManager,
        gemini_client: Optional[GeminiClient] = None,
        use_llm: bool = True,
    ) -> None:
        self.curriculum_manager = curriculum_manager
        self.gemini_client = gemini_client or default_gemini_client
        self.use_llm = use_llm

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def _filter_oas_by_course_subject(self, curso: str, asignatura: str) -> List[str]:
        return [
            oa_id
            for oa_id, oa_data in self.curriculum_manager._oa_index.items()
            if oa_data.get("curso") == curso and oa_data.get("asignatura") == asignatura
        ]

    def _extract_candidate_oa_ids(
        self, student_message: str, curso: str, asignatura: str
    ) -> List[str]:
        normalized = self._normalize(student_message)
        candidate_oas = self._filter_oas_by_course_subject(curso, asignatura)
        candidates: List[str] = []

        # Detectar referencias explícitas a OAs con regex insensible a mayúsculas/minúsculas
        explicit_matches = re.findall(r"\b(OA_[0-9]{1,3})\b", normalized, re.IGNORECASE)
        for oa_id in explicit_matches:
            normalized_oa = oa_id.upper()
            if normalized_oa in candidate_oas:
                candidates.append(normalized_oa)

        query_tokens = set(re.findall(r"\w+", normalized))
        scoring: Dict[str, int] = {}

        for oa_id in candidate_oas:
            oa_data = self.curriculum_manager._oa_index[oa_id]
            text = self._normalize(
                " ".join(
                    [
                        oa_data.get("descripcion", ""),
                        " ".join(oa_data.get("indicadores_evaluacion", [])),
                        " ".join(oa_data.get("conceptos_clave", [])),
                    ]
                )
            )
            token_matches = sum(1 for token in query_tokens if token in text)
            if token_matches > 0:
                scoring[oa_id] = token_matches

        for oa_id, _ in sorted(scoring.items(), key=lambda item: item[1], reverse=True):
            if oa_id not in candidates:
                candidates.append(oa_id)

        return candidates

    async def _infer_oa_with_gemini(
        self, student_message: str, curso: str, asignatura: str
    ) -> Optional[str]:
        candidate_oas = self._filter_oas_by_course_subject(curso, asignatura)
        candidate_list = "\n".join(
            [
                f"{oa_id}: {self.curriculum_manager._oa_index[oa_id].get('descripcion', '')}"
                for oa_id in candidate_oas
            ]
        )

        system_prompt = (
            "Actúa como un clasificador curricular para el currículo MINEDUC chileno. "
            "Recibe la consulta del alumno y devuelve SOLO el ID del OA más relevante "
            "para el curso y asignatura indicados, usando el formato OA_XX. "
            "Si no hay correspondencia clara, responde NONE."
        )

        user_message = (
            f"Curso: {curso}\nAsignatura: {asignatura}\n"
            f"Consulta del alumno: {student_message}\n"
            f"OA disponibles:\n{candidate_list}"
        )

        raw = await self.gemini_client.generate_pedagogic_response(
            system_prompt=system_prompt,
            user_message=user_message,
            history=None,
            temperature=0.0,
        )

        match = re.search(r"\b(OA_[0-9]{1,3})\b", raw, re.IGNORECASE)
        if match:
            candidate = match.group(1).upper()
            return candidate if candidate in candidate_oas else None

        return None

    async def analyze_student_input(
        self,
        student_id: str,
        student_message: str,
        curso: str,
        asignatura: str,
        id_oa: Optional[str] = None,
    ) -> ValidatorToPedagoguePayload:
        selected_oa = None

        if id_oa and self.curriculum_manager.get_oa_by_id(id_oa, curso=curso, asignatura=asignatura):
            selected_oa = id_oa
        else:
            candidate_ids = self._extract_candidate_oa_ids(student_message, curso, asignatura)
            for oa in candidate_ids:
                if self.curriculum_manager.get_oa_by_id(oa, curso=curso, asignatura=asignatura):
                    selected_oa = oa
                    break

            if not selected_oa and self.use_llm:
                selected_oa = await self._infer_oa_with_gemini(student_message, curso, asignatura)

        if not selected_oa:
            raise ValueError(
                "No se pudo inferir un OA para la consulta del alumno dentro del curso y asignatura especificados."
            )

        return self._build_validation_payload(student_id, student_message, selected_oa, curso, asignatura)

    def _build_validation_payload(
        self,
        student_id: str,
        student_message: str,
        oa_id: str,
        curso: str,
        asignatura: str,
    ) -> ValidatorToPedagoguePayload:
        raw_oa = self.curriculum_manager.get_oa_by_id(oa_id, curso=curso, asignatura=asignatura)
        if not raw_oa:
            raise ValueError(f"OA no encontrada en el currículo: {oa_id} para {curso} - {asignatura}")

        curriculum_unit = CurriculumUnit(
            curso=raw_oa.get("curso", ""),
            asignatura=raw_oa.get("asignatura", ""),
            eje_tematico=raw_oa.get("eje_tematico", ""),
            objetivos_aprendizaje=[
                ObjetivoAprendizaje(
                    id_oa=raw_oa["id_oa"],
                    descripcion=raw_oa.get("descripcion", ""),
                    indicadores_evaluacion=raw_oa.get("indicadores_evaluacion", []),
                    conceptos_clave=raw_oa.get("conceptos_clave", []),
                )
            ],
        )

        progress_record = OAProgressRecord(
            student_id=student_id,
            id_oa=oa_id,
            mastery_level="in_progress",
            last_evaluation_date=None,
            evaluation_history=[],
            aligned_resources=[],
        )

        return ValidatorToPedagoguePayload(
            student_id=student_id,
            timestamp=None,
            curriculum_unit=curriculum_unit,
            target_oa=curriculum_unit.objetivos_aprendizaje[0],
            student_progress=progress_record,
            evidence=[],
            validation_notes=f"Consulta del alumno: {student_message}",
        )

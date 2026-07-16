"""
MasterOrchestrator — Rutea las peticiones entrantes al agente correcto.

Flujo multi-agente:
  1. Recibe { student_id, message, curso, asignatura } desde el endpoint.
  2. Clasifica la intención según el mensaje (keyword-based routing).
  3. Delega al agente correspondiente (ValidatorAgent, PedagogicAgent, o flujo combinado).
  4. Retorna respuesta estructurada con agent_used, response_text, y metadatos.
"""
import logging
from typing import Any, Dict, Optional, List

from app.agents.pedagogic_agent import PedagogicAgent
from app.agents.validator_agent import ValidatorAgent
from app.models.schemas import ValidatorToPedagoguePayload

logger = logging.getLogger(__name__)


class MasterOrchestrator:
    """Orquestador central del flujo multi-agente.

    Input esperado::
        student_id : str
        message    : str
        curso      : str
        asignatura : str
        history    : list (opcional)
        student_interest : str (opcional)
        current_topic    : str (opcional)

    Output::
        dict con "agent_used", "response_text", "oa_metadata",
        "progress_record", y opcionalmente "code_review".
    """

    def __init__(
        self,
        validator_agent: ValidatorAgent,
        pedagogic_agent: PedagogicAgent,
    ) -> None:
        self.validator = validator_agent
        self.pedagogue = pedagogic_agent

    # ──────────────────────────────────────────────
    #  Ruta principal
    # ──────────────────────────────────────────────

    async def route(
        self,
        student_id: str,
        message: str,
        curso: str,
        asignatura: str,
        history: Optional[List[Dict[str, str]]] = None,
        student_interest: Optional[str] = None,
        current_topic: Optional[str] = None,
        id_oa: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Clasifica el mensaje y delega al agente adecuado.

        Returns:
            {
                "agent_used": str,
                "response_text": str,
                "oa_metadata": dict | None,
                "progress_record": dict | None,
                "payload": ValidatorToPedagoguePayload | None,
                "code_review": dict | None,   # sólo si es solicitud de validación
            }
        """
        msg_lower = message.strip().lower()

        # ── Rama 1: Validación de código / ejercicio ──
        if (
            message.strip().startswith("def ")
            or "class " in message
            or "```" in message
            or "validar" in msg_lower
            or "revisar" in msg_lower
        ):
            return await self._route_code_validation(
                student_id, message, curso, asignatura, current_topic
            )

        # ── Rama 2: Consulta pedagógica (default) ──
        #  1. ValidatorAgent → detecta OA
        #  2. PedagogicAgent → genera lección
        return await self._route_pedagogic(
            student_id, message, curso, asignatura, history, id_oa
        )

    # ──────────────────────────────────────────────
    #  Rama: Validación de código
    # ──────────────────────────────────────────────

    async def _route_code_validation(
        self,
        student_id: str,
        message: str,
        curso: str,
        asignatura: str,
        current_topic: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evalúa código/ejercicio usando el agente validador
        (consulta directa a Gemini con structured output)."""
        exercise_desc = (
            f"Resolver un ejercicio sobre el tema actual: {current_topic or 'Programación básica'}"
        )

        # El ValidatorAgent tiene acceso a GeminiClient, pero no expone
        # un método público de code-review. Usamos el cliente directamente.
        from app.services.gemini_client import default_gemini_client

        system_prompt = (
            "Actúa como el Agente Validador de Super_Profesor. Revisa minuciosamente "
            "la entrega del estudiante. Evalúa la lógica, la sintaxis (si aplica) y si "
            "cumple con los requerimientos. Ofrece sugerencias de mejora y código "
            "optimizado si es útil. Devuelve un análisis textual completo."
        )

        user_message = (
            f"Descripción del Ejercicio:\n{exercise_desc}\n\n"
            f"Entrega del Estudiante:\n{message}"
        )

        response_text = await default_gemini_client.generate_pedagogic_response(
            system_prompt=system_prompt,
            user_message=user_message,
            history=None,
            temperature=0.1,
        )

        return {
            "agent_used": "ValidatorAgent (code review)",
            "response_text": response_text,
            "oa_metadata": None,
            "progress_record": None,
            "payload": None,
            "code_review": {
                "exercise": exercise_desc,
                "submission": message,
            },
        }

    # ──────────────────────────────────────────────
    #  Rama: Consulta pedagógica (chat estándar)
    # ──────────────────────────────────────────────

    async def _route_pedagogic(
        self,
        student_id: str,
        message: str,
        curso: str,
        asignatura: str,
        history: Optional[List[Dict[str, str]]] = None,
        id_oa: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Flujo estándar: Validator → OA detection → PedagogicAgent → lección."""
        # 1. ValidatorAgent: detecta OA
        payload = await self.validator.analyze_student_input(
            student_id=student_id,
            student_message=message,
            curso=curso,
            asignatura=asignatura,
            id_oa=id_oa,
        )

        # 2. PedagogicAgent: genera lección
        response_text = await self.pedagogue.generate_lesson(
            payload=payload,
            student_message=message,
            history=history,
        )

        return {
            "agent_used": "ValidatorAgent → PedagogicAgent",
            "response_text": response_text,
            "oa_metadata": {
                "id_oa": payload.target_oa.id_oa,
                "descripcion": payload.target_oa.descripcion,
                "conceptos_clave": payload.target_oa.conceptos_clave,
                "indicadores_evaluacion": payload.target_oa.indicadores_evaluacion,
                "curso": payload.curriculum_unit.curso,
                "asignatura": payload.curriculum_unit.asignatura,
            },
            "progress_record": payload.student_progress.model_dump(),
            "payload": payload,
            "code_review": None,
        }
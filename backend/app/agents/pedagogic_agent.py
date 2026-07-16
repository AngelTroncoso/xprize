import os
from pathlib import Path
from typing import Dict, Optional, List

from app.models.schemas import ValidatorToPedagoguePayload
from app.services.gemini_client import GeminiClient, default_gemini_client


class PedagogicAgent:
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        recursos_path: Optional[str] = None,
    ) -> None:
        self.gemini_client = gemini_client or default_gemini_client
        self.recursos_path = recursos_path or os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "recursos_externos",
            "apis_educativas.md",
        )

    def _read_external_resources(self) -> str:
        path = Path(self.recursos_path).resolve()
        if not path.exists() or not path.is_file():
            return (
                "No se encontró el archivo de recursos externos. "
                "Incluye recomendaciones de Khan Academy, GeoGebra y PhET según los conceptos clave."
            )

        with path.open("r", encoding="utf-8") as infile:
            return infile.read().strip()

    def _build_system_prompt(
        self,
        payload: ValidatorToPedagoguePayload,
        external_resources: str,
        student_message: str,
    ) -> str:
        concepts = ", ".join(payload.target_oa.conceptos_clave)
        indicators = "\n".join(f"- {item}" for item in payload.target_oa.indicadores_evaluacion)

        return f"""
Actúa como un tutor pedagógico experto de Super_Profesor para un estudiante de 3° básico.
Tu respuesta debe ser empática, interactiva y basada exclusivamente en el OA oficial de MINEDUC.

Información curricular obligatoria:
- Descripción: {payload.target_oa.descripcion}
- Conceptos clave: {concepts}
- Indicadores de evaluación:
{indicators}

No inventes nuevos conceptos ni desvíes el enfoque. Debes sugerir un recurso externo concreto que apoye la práctica del OA y que sea coherente con los conceptos clave.
Utiliza el archivo de recursos externos como anclaje rígido a continuación:
{external_resources}

INSTRUCCIONES CRÍTICAS PARA SALIDA DE AUDIO:
- Responde en español latino natural, sin asteriscos, guiones largos ni caracteres especiales innecesarios.
- Los primeros dos párrafos deben ser claros y pronunciables: evita Markdown complejo en las primeras líneas.
- Estructura: Introducción amigable → Ejemplo → Actividad → Recomendación de recurso.
- Usa frases cortas y naturales, como si hablaras con un niño de 8-9 años.
- No incluyas códigos de programación, símbolos matemáticos complejos, ni abreviaturas raras en el audio.

El resultado debe ser una mini-lección para el estudiante, con:
1. Explicación breve y amigable (primeros párrafos claros para audio).
2. Ejemplo interactivo.
3. Actividad práctica sugerida.
4. Recomendación explícita de un recurso externo (Khan Academy, GeoGebra o PhET) que refuerce los conceptos.
""".strip()

    def _build_user_message(self, payload: ValidatorToPedagoguePayload, student_message: str) -> str:
        if "[SISTEMA: Iniciar clase para OA]" in student_message:
            return f"""
El estudiante acaba de seleccionar este Objetivo de Aprendizaje en el catálogo para iniciar una nueva lección interactiva.
Actúa proactivamente: dale una bienvenida muy cálida y entusiasta, y hazle una pregunta inicial exploratoria o lúdica relacionada con los conceptos clave del OA para despertar su curiosidad y comenzar la clase.

Contexto adicional:
- Curso: {payload.curriculum_unit.curso}
- Asignatura: {payload.curriculum_unit.asignatura}
- OA objetivo: {payload.target_oa.id_oa}
""".strip()

        return f"""
La consulta del alumno: {student_message}

Contexto adicional:
- Curso: {payload.curriculum_unit.curso}
- Asignatura: {payload.curriculum_unit.asignatura}
- OA objetivo: {payload.target_oa.id_oa}

Responde como un tutor de 3° básico y usa lenguaje claro, afectuoso, con ejemplos visuales o manipulativos.
""".strip()

    async def generate_lesson(
        self,
        payload: ValidatorToPedagoguePayload,
        student_message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        external_resources = self._read_external_resources()
        system_prompt = self._build_system_prompt(payload, external_resources, student_message)
        user_message = self._build_user_message(payload, student_message)

        return await self.gemini_client.generate_pedagogic_response(
            system_prompt=system_prompt,
            user_message=user_message,
            history=history,
            temperature=0.4,
        )

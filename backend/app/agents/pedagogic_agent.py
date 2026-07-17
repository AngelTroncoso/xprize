import os
from pathlib import Path
from typing import Dict, Optional, List, Any

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

No inventes nuevos conceptos ni desvíes el enfoque. IMPORTANTE: NO recomiendes plataformas externas (como Khan Academy, YouTube, etc.). Tú eres el profesor y la plataforma actual (Super_Profesor) tiene todo lo necesario.

INSTRUCCIONES CRÍTICAS PARA SALIDA DE AUDIO Y CONVERSACIÓN:
- Responde en español latino natural, sin asteriscos, guiones largos ni caracteres especiales innecesarios.
- Los primeros dos párrafos deben ser claros y pronunciables: evita Markdown complejo en las primeras líneas.
- Estructura sugerida para tus respuestas: Empatía/Validación → Explicación muy breve → Reto o Pregunta interactiva.
- Usa frases cortas y naturales, como si hablaras con un niño de 8-9 años.
- No seas "escueto" o aburrido. ¡Sé creativo! Usa metáforas divertidas y juegos imaginarios.
- Invita constantemente al alumno a usar la **Pizarra interactiva** que tiene en su pantalla. Pídele que dibuje, que resuelva ahí los ejercicios o que escriba sus respuestas.
- Cuando quieras proponer una actividad formal (múltiple opción, rellenar espacios, o mostrar una imagen de apoyo), rellena el campo `interactive_exercise` en tu respuesta JSON. Si es solo conversación o quieres que dibuje libremente, deja ese campo nulo.

El resultado debe ser una experiencia interactiva para el estudiante, con:
1. Explicación creativa, amigable y muy entretenida.
2. Ejemplos lúdicos relacionados con los intereses de los niños.
3. Actividad práctica sugerida para resolver directamente en la Pizarra interactiva.
""".strip()

    def _build_user_message(self, payload: ValidatorToPedagoguePayload, student_message: str) -> str:
        if "[SISTEMA: Iniciar clase para OA]" in student_message:
            return f"""
El estudiante acaba de seleccionar este Objetivo de Aprendizaje en el catálogo para iniciar una nueva lección interactiva.
Actúa proactivamente: dale una bienvenida muy cálida y entusiasta, y hazle una pregunta inicial exploratoria o lúdica relacionada con los conceptos clave del OA para despertar su curiosidad y comenzar la clase.
¡MUY IMPORTANTE!: Esta es sólo la frase inicial para saludar. Tu respuesta debe ser EXTREMADAMENTE CORTA (máximo 2 párrafos breves). NO le des una lección completa todavía, NO incluyas recomendaciones externas aún. Sólo preséntate, dile qué van a aprender hoy y hazle una pregunta corta para iniciar la conversación.

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

Responde como un tutor de 3° básico. Sé creativo, entretenido y muy afectuoso. NO seas escueto, desarrolla ejemplos lúdicos. Invita SIEMPRE al alumno a usar la Pizarra interactiva para dibujar o resolver los ejercicios que le propongas.
""".strip()

    async def generate_lesson(
        self,
        payload: ValidatorToPedagoguePayload,
        student_message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        external_resources = self._read_external_resources()
        system_prompt = self._build_system_prompt(payload, external_resources, student_message)
        user_message = self._build_user_message(payload, student_message)

        from app.models.schemas import PedagogicResponseSchema
        import json

        response_str = await self.gemini_client.generate_pedagogic_response(
            system_prompt=system_prompt,
            user_message=user_message,
            history=history,
            temperature=0.4,
            response_schema=PedagogicResponseSchema,
        )
        
        try:
            data = json.loads(response_str)
            return {
                "response_text": data.get("response_text", "Hubo un error al generar la respuesta."),
                "interactive_exercise": data.get("interactive_exercise")
            }
        except Exception:
            return {
                "response_text": response_str,
                "interactive_exercise": None
            }

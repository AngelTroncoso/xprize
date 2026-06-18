import os
from google import genai
from google.genai import types
from app.models.schemas import ChatInput, DiagnosticResult, LessonPlan, CodeReview
from typing import Dict, Any

class MasterOrchestrator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "dummy-key")
        self.client = genai.Client(api_key=api_key)
        self.fast_model = "gemini-1.5-flash"
        self.reasoning_model = "gemini-1.5-pro"

    def _generate_diagnostic(self, responses: str) -> DiagnosticResult:
        prompt = f"""
        Actúa como el Agente Evaluador de Super_Profesor. Tu objetivo es analizar el desempeño del estudiante
        basándote en sus respuestas u opiniones y devolver un diagnóstico estructurado.
        
        Respuestas del estudiante:
        {responses}
        """
        response = self.client.models.generate_content(
            model=self.fast_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DiagnosticResult,
                temperature=0.2
            )
        )
        return response.parsed

    def _generate_personalized_lesson(self, topic: str, student_interest: str) -> LessonPlan:
        prompt = f"""
        Actúa como el Agente Pedagógico de Super_Profesor. Tu objetivo es explicar el tema técnico: "{topic}"
        de una manera altamente clara, utilizando analogías creativas basadas en el interés del estudiante: "{student_interest}".
        
        Asegúrate de estructurar el contenido de la lección usando Markdown.
        Define objetivos claros y crea ejercicios de práctica rápidos que reten al estudiante.
        """
        response = self.client.models.generate_content(
            model=self.reasoning_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LessonPlan,
                temperature=0.7
            )
        )
        return response.parsed

    def _audit_code_or_exercise(self, exercise_description: str, student_submission: str) -> CodeReview:
        prompt = f"""
        Actúa como el Agente Validador de Super_Profesor. Revisa minuciosamente la entrega del estudiante.
        
        Descripción del Ejercicio:
        {exercise_description}
        
        Entrega del Estudiante:
        {student_submission}
        
        Evalúa la lógica, la sintaxis (si aplica) y si cumple con los requerimientos. Ofrece sugerencias de mejora y código optimizado si es útil.
        """
        response = self.client.models.generate_content(
            model=self.fast_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CodeReview,
                temperature=0.1
            )
        )
        return response.parsed

    def process_student_input(self, data: ChatInput) -> Dict[str, Any]:
        """
        Analiza el input y delega al agente correspondiente.
        En una implementación completa, se puede usar un clasificador (router model)
        para discernir la intención. Aquí demostramos el ruteo básico.
        """
        message = data.message.strip()
        
        # 1. Si parece código o el mensaje explícitamente pide revisión, activar Agente Validador
        if message.startswith("def ") or "class " in message or "```" in message or "validar" in message.lower():
            # Mock del ejercicio que estaría resolviendo en su plan actual
            exercise_desc = f"Resolver un ejercicio sobre el tema actual: {data.current_topic or 'Programación básica'}"
            review: CodeReview = self._audit_code_or_exercise(exercise_desc, message)
            return {
                "agent": "Agente Validador",
                "type": "code_review",
                "content": review.model_dump()
            }
            
        # 2. Si el estudiante pide iniciar un tema o aprender algo nuevo, activar Agente Pedagógico
        elif "explicar" in message.lower() or "aprender" in message.lower() or "tema" in message.lower():
            topic = data.current_topic or message
            interest = data.student_interest or "deportes"
            lesson: LessonPlan = self._generate_personalized_lesson(topic, interest)
            return {
                "agent": "Agente Pedagógico",
                "type": "lesson_plan",
                "content": lesson.model_dump()
            }
            
        # 3. Por defecto, tratar como una interacción general o un autodiagnóstico
        else:
            diagnostic: DiagnosticResult = self._generate_diagnostic(message)
            return {
                "agent": "Agente Evaluador",
                "type": "diagnostic",
                "content": diagnostic.model_dump()
            }

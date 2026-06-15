from app.services.gemini import GeminiService
from app.models.schemas import ChatInput, DiagnosticResult, LessonPlan, CodeReview
from typing import Dict, Any

class MasterOrchestrator:
    def __init__(self):
        self.gemini = GeminiService()

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
            review: CodeReview = self.gemini.audit_code_or_exercise(exercise_desc, message)
            return {
                "agent": "Agente Validador",
                "type": "code_review",
                "content": review.model_dump()
            }
            
        # 2. Si el estudiante pide iniciar un tema o aprender algo nuevo, activar Agente Pedagógico
        elif "explicar" in message.lower() or "aprender" in message.lower() or "tema" in message.lower():
            topic = data.current_topic or message
            interest = data.student_interest or "deportes"
            lesson: LessonPlan = self.gemini.generate_personalized_lesson(topic, interest)
            return {
                "agent": "Agente Pedagógico",
                "type": "lesson_plan",
                "content": lesson.model_dump()
            }
            
        # 3. Por defecto, tratar como una interacción general o un autodiagnóstico
        else:
            diagnostic: DiagnosticResult = self.gemini.generate_diagnostic(message)
            return {
                "agent": "Agente Evaluador",
                "type": "diagnostic",
                "content": diagnostic.model_dump()
            }

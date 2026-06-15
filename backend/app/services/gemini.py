import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from app.models.schemas import DiagnosticResult, LessonPlan, CodeReview

load_dotenv()

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Fallback en caso de que no esté seteada aún en desarrollo
            api_key = "dummy-key"
        self.client = genai.Client(api_key=api_key)
        
        # Modelos vigentes en 2026
        self.fast_model = "gemini-3.5-flash"
        self.reasoning_model = "gemini-3.1-pro"

    def generate_diagnostic(self, responses: str) -> DiagnosticResult:
        """
        Agente Evaluador: Mapea debilidades y genera un diagnóstico estructurado
        """
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

    def generate_personalized_lesson(self, topic: str, student_interest: str) -> LessonPlan:
        """
        Agente Pedagógico: Genera una lección personalizada usando analogías de interés
        """
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

    def audit_code_or_exercise(self, exercise_description: str, student_submission: str) -> CodeReview:
        """
        Agente Validador: Audita código u otras entregas en menos de 90 segundos
        """
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

import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from app.models.database import db

class JudgeEvaluationResult(BaseModel):
    score: int = Field(..., description="Calificación de la interacción del 1 al 5. 5 es excelente.")
    reasoning: str = Field(..., description="Explicación detallada de la puntuación en base a las rúbricas pedagógicas.")

class JudgeAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "dummy-key")
        self.client = genai.Client(api_key=api_key)
        self.judge_model = "gemini-3.5-flash"

    def evaluate_trace(self, trace_id: str, span_name: str, input_val: str, output_val: str) -> JudgeEvaluationResult:
        """
        Agente Juez (LLM-as-a-Judge): Evalúa de forma automática la calidad del feedback
        pedagógico y la asertividad de las respuestas de los agentes.
        """
        prompt = f"""
        Actúas como el Agente Juez (Calidad Pedagógica y Técnica) en la plataforma Super_Profesor.
        Tu misión es evaluar la respuesta del tutor (assistant) al estudiante (user) en base a estas directrices:
        
        Rúbrica de Puntuación:
        - 1 Punto (Muy Mala): La respuesta es errónea, contiene código con bugs críticos o viola políticas de seguridad.
        - 2 Puntos (Insuficiente): El tono es plano, repite datos secos sin analogías o no responde el centro de la pregunta.
        - 3 Puntos (Aceptable): Resuelve la duda, pero es verbosa y no incita a la interacción o el razonamiento del estudiante.
        - 4 Puntos (Buena): Usa analogías claras adaptadas a los intereses, el tono es alentador y el código es correcto.
        - 5 Puntos (Excelente): Aplica el método socrático perfectamente, reta al alumno con analogías asombrosas y da feedback de código accionable y limpio.
        
        Detalles del Span: {span_name}
        Entrada (Estudiante):
        {input_val}
        
        Salida del Agente (Super_Profesor):
        {output_val}
        
        Realiza una evaluación constructiva y genera tu puntuación final.
        """
        try:
            response = self.client.models.generate_content(
                model=self.judge_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=JudgeEvaluationResult,
                    temperature=0.2
                )
            )
            result: JudgeEvaluationResult = response.parsed
            
            # Registrar en la base de datos
            self._save_evaluation(trace_id, result)
            return result
        except Exception as e:
            print(f"Error en la ejecución del Agente Juez: {e}")
            return JudgeEvaluationResult(
                score=3,
                reasoning=f"Fallo al ejecutar evaluación del Juez: {str(e)}"
            )

    def _save_evaluation(self, trace_id: str, result: JudgeEvaluationResult):
        supabase_client = db.get_client()
        if not supabase_client:
            print(f"[AgentOps Judge Result] Trace ID: {trace_id} - Score: {result.score} - Reasoning: {result.reasoning}")
            return

        try:
            supabase_client.table("judge_evaluations").insert({
                "trace_id": trace_id,
                "score": result.score,
                "reasoning": result.reasoning
            }).execute()
        except Exception as e:
            print(f"Error al guardar evaluación del Juez en base de datos: {e}")

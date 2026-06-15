from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# --- Agente Evaluador Schemas ---
class SkillEvaluation(BaseModel):
    topic: str = Field(..., description="El tema específico evaluado")
    skill_level: Literal["beginner", "intermediate", "advanced"] = Field(..., description="Nivel detectado")
    score: float = Field(..., description="Puntuación (0 a 100)")

class DiagnosticResult(BaseModel):
    student_id: str = Field(..., description="ID del estudiante")
    overall_level: Literal["beginner", "intermediate", "advanced"] = Field(..., description="Nivel general estimado")
    strengths: List[str] = Field(..., description="Puntos fuertes identificados")
    weaknesses: List[str] = Field(..., description="Gaps o áreas de oportunidad")
    evaluations: List[SkillEvaluation] = Field(..., description="Resultados detallados por área")
    recommended_start_topic: str = Field(..., description="Tema recomendado para comenzar")

# --- Agente Pedagógico Schemas ---
class Analogy(BaseModel):
    concept: str = Field(..., description="Concepto técnico complejo a explicar")
    analogy_text: str = Field(..., description="Analogía adaptada al interés del alumno")
    explanation: str = Field(..., description="Explicación detallada conectando la analogía con el concepto técnico")

class Exercise(BaseModel):
    title: str = Field(..., description="Título del ejercicio")
    description: str = Field(..., description="Instrucciones del ejercicio")
    starting_code: Optional[str] = Field(None, description="Código inicial si aplica")
    expected_output_description: str = Field(..., description="Descripción detallada de la salida esperada")

class LessonPlan(BaseModel):
    topic: str = Field(..., description="Tema principal de la lección")
    title: str = Field(..., description="Título atractivo de la lección")
    objectives: List[str] = Field(..., description="Objetivos pedagógicos")
    content: str = Field(..., description="Contenido explicativo de la lección en formato Markdown")
    analogies: List[Analogy] = Field(..., description="Analogías personalizadas de soporte")
    exercises: List[Exercise] = Field(..., description="Ejercicios prácticos de evaluación rápida")
    estimated_duration_minutes: int = Field(20, description="Duración estimada")

# --- Agente Validador Schemas ---
class CodeError(BaseModel):
    line_number: Optional[int] = Field(None, description="Línea donde ocurre el error")
    error_type: str = Field(..., description="Tipo de error (sintaxis, lógica, estilo)")
    message: str = Field(..., description="Mensaje explicativo del error")

class CodeReview(BaseModel):
    is_correct: bool = Field(..., description="Indica si la entrega cumple con los requisitos del ejercicio")
    score: float = Field(..., description="Calificación del 0 al 100")
    errors: List[CodeError] = Field(default=[], description="Lista de errores encontrados")
    suggestions: List[str] = Field(default=[], description="Sugerencias de optimización o estilo")
    improved_code: Optional[str] = Field(None, description="Versión optimizada o corregida del código")
    explanation: str = Field(..., description="Explicación pedagógica constructiva del feedback")

# --- General Chat Schemas ---
class ChatInput(BaseModel):
    message: str = Field(..., description="El mensaje o código del estudiante")
    session_id: str = Field(..., description="ID de la sesión de chat")
    student_interest: Optional[str] = Field(None, description="Interés/Hobby para analogías (ej. fútbol, música, videojuegos)")
    current_topic: Optional[str] = Field(None, description="Tema en estudio actualmente")

from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

# --- Esquemas Curriculares (MINEDUC Chile) ---
class ObjetivoAprendizaje(BaseModel):
    id_oa: str = Field(..., description="Identificador único del Objetivo de Aprendizaje (ej. OA_01)")
    descripcion: str = Field(..., description="Descripción oficial del OA")
    indicadores_evaluacion: List[str] = Field(default=[], description="Criterios específicos de evaluación")
    conceptos_clave: List[str] = Field(..., description="Conceptos fundamentales a dominar")

class CurriculumUnit(BaseModel):
    curso: str = Field(..., description="Grado/curso (ej. 3ro Basico)")
    asignatura: str = Field(..., description="Nombre de la asignatura")
    eje_tematico: str = Field(..., description="Eje temático principal")
    objetivos_aprendizaje: List[ObjetivoAprendizaje] = Field(..., description="Lista de OA del eje")

class OAProgressRecord(BaseModel):
    student_id: str = Field(..., description="ID del estudiante")
    id_oa: str = Field(..., description="ID del Objetivo de Aprendizaje")
    mastery_level: Literal["not_started", "in_progress", "partial", "mastered"] = Field(
        default="not_started", 
        description="Nivel de dominio del OA"
    )
    last_evaluation_date: Optional[str] = Field(None, description="Fecha de última evaluación")
    evaluation_history: List[Dict[str, Any]] = Field(default=[], description="Historial de evaluaciones")
    aligned_resources: List[str] = Field(default=[], description="IDs de recursos recomendados")

# --- Payload entre Agentes: Validador → Pedagógico ---
class ValidatorToPedagoguePayload(BaseModel):
    student_id: str = Field(..., description="ID del estudiante")
    timestamp: Optional[str] = Field(None, description="Timestamp de la evaluación / interacción")
    curriculum_unit: CurriculumUnit = Field(..., description="Unidad curricular completa asociada al OA")
    target_oa: ObjetivoAprendizaje = Field(..., description="El OA objetivo que fue evaluado")
    student_progress: OAProgressRecord = Field(..., description="Registro de progreso actual para este OA")
    evidence: Optional[List[str]] = Field(default=[], description="Evidencias textuales o referencias a entregas del alumno")
    validation_notes: Optional[str] = Field(None, description="Notas interpretativas del Agente Validador para el Pedagogo")

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
    student_id: str = Field(..., description="ID del estudiante")
    curso: Optional[str] = Field(None, description="Curso del estudiante (ej. 3ro Basico)")
    asignatura: Optional[str] = Field(None, description="Asignatura solicitada (ej. Matematica)")
    message: str = Field(..., description="El mensaje o duda del estudiante")
    session_id: Optional[str] = Field(None, description="ID de la sesión de chat")
    student_interest: Optional[str] = Field(None, description="Interés/Hobby para analogías (ej. fútbol, música, videojuegos)")
    current_topic: Optional[str] = Field(None, description="Tema en estudio actualmente")
    enable_audio: bool = Field(default=True, description="Si es True, genera audio TTS de la respuesta")

class ChatResponse(BaseModel):
    agent: str = Field(..., description="Agente que generó la respuesta")
    student_id: str = Field(..., description="ID del estudiante")
    oa_metadata: Dict[str, Any] = Field(..., description="Metadatos del Objetivo de Aprendizaje")
    pedagogic_response: str = Field(..., description="Respuesta textual del agente pedagógico")
    audio_response_b64: Optional[str] = Field(None, description="Respuesta en audio codificada en Base64 (si enable_audio=True)")
    audio_mime_type: Optional[str] = Field(None, description="Tipo MIME del audio (ej. audio/mpeg)")
    progress_record: Dict[str, Any] = Field(..., description="Registro de progreso del estudiante")
    saved_progress: Optional[Dict[str, Any]] = Field(None, description="Resultado de persistencia en Supabase")

# --- Canvas Interactivo (Pizarra Compartida) ---
class CanvasInput(BaseModel):
    student_id: str = Field(..., description="ID del estudiante")
    curso: str = Field(..., description="Curso del estudiante (ej. 3ro Basico)")
    asignatura: str = Field(..., description="Asignatura (ej. Matematica)")
    id_oa: Optional[str] = Field(None, description="ID del OA objetivo (ej. OA_01)")
    canvas_data: str = Field(..., description="Imagen del trazo en formato Base64/DataURL")
    prompt_adicional: Optional[str] = Field(None, description="Texto o nota adicional del alumno junto al dibujo")
    enable_audio: bool = Field(default=True, description="Si es True, genera feedback en audio")

class CanvasResponse(BaseModel):
    agent: str = Field(..., description="Agente que generó el feedback")
    student_id: str = Field(..., description="ID del estudiante")
    id_oa: Optional[str] = Field(None, description="OA analizado")
    oa_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos del OA si está disponible")
    visual_analysis: str = Field(..., description="Análisis visual del dibujo del alumno")
    pedagogic_feedback: str = Field(..., description="Retroalimentación pedagógica estructurada")
    audio_feedback_b64: Optional[str] = Field(None, description="Feedback en audio codificado en Base64")
    audio_mime_type: Optional[str] = Field(None, description="Tipo MIME del audio")
    comprehension_level: Literal["emerging", "developing", "proficient", "advanced"] = Field(
        ..., description="Nivel de comprensión detectado del alumno"
    )
    mastery_advancement: float = Field(..., description="Puntuación 0-1 de avance en dominio del OA")
    saved_progress: Optional[Dict[str, Any]] = Field(None, description="Registro guardado en Supabase")

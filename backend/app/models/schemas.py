from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Dict, Any
from uuid import UUID


def _validate_uuid(value: str) -> str:
    # Retornamos el valor directamente sin forzar que sea un UUID válido.
    # Esto permite compatibilidad con frontend que envía "1".
    return str(value)

class StudentIdUUIDMixin(BaseModel):
    student_id: str = Field(..., description="UUID o ID del estudiante")

    @field_validator("student_id")
    @classmethod
    def validate_student_id(cls, value: str) -> str:
        return _validate_uuid(value)

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

class OAProgressRecord(StudentIdUUIDMixin):
    id_oa: str = Field(..., description="ID del Objetivo de Aprendizaje")
    mastery_level: Literal["not_started", "in_progress", "partial", "mastered"] = Field(
        default="not_started", 
        description="Nivel de dominio del OA"
    )
    last_evaluation_date: Optional[str] = Field(None, description="Fecha de última evaluación")
    evaluation_history: List[Dict[str, Any]] = Field(default=[], description="Historial de evaluaciones")
    aligned_resources: List[str] = Field(default=[], description="IDs de recursos recomendados")

# --- Payload entre Agentes: Validador → Pedagógico ---
class ValidatorToPedagoguePayload(StudentIdUUIDMixin):
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

class DiagnosticResult(StudentIdUUIDMixin):
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
class ChatInput(StudentIdUUIDMixin):
    curso: Optional[str] = Field(None, description="Curso del estudiante (ej. 3ro Basico)")
    asignatura: Optional[str] = Field(None, description="Asignatura solicitada (ej. Matematica)")
    message: str = Field(..., description="El mensaje o duda del estudiante")
    session_id: Optional[str] = Field(None, description="ID de la sesión de chat")
    student_interest: Optional[str] = Field(None, description="Interés/Hobby para analogías (ej. fútbol, música, videojuegos)")
    current_topic: Optional[str] = Field(None, description="Tema en estudio actualmente")
    enable_audio: bool = Field(default=True, description="Si es True, genera audio TTS de la respuesta")
    id_oa: Optional[str] = Field(None, description="ID del OA objetivo explícito (ej. OA_01)")
    gemini_file_id: Optional[str] = Field(None, description="ID del archivo PDF del libro subido a Gemini")

# --- Ejercicios Interactivos Dinámicos ---
class InteractiveExercise(BaseModel):
    type: Literal["multiple_choice", "fill_in_blanks", "visual_image"] = Field(..., description="Tipo de ejercicio interactivo")
    title: str = Field(..., description="Título o instrucción principal del ejercicio")
    # Para multiple_choice
    options: Optional[List[str]] = Field(None, description="Opciones disponibles si es selección múltiple")
    correct_option: Optional[str] = Field(None, description="Opción correcta esperada")
    # Para fill_in_blanks
    text_with_blanks: Optional[str] = Field(None, description="Texto con huecos representados por ___ (tres guiones bajos)")
    blanks_answers: Optional[List[str]] = Field(None, description="Respuestas esperadas en orden para los huecos")
    # Para visual_image
    image_prompt: Optional[str] = Field(None, description="Prompt descriptivo para buscar o generar una imagen")
    image_url: Optional[str] = Field(None, description="URL de la imagen (puede ser autogenerado por el backend)")

class PedagogicResponseSchema(BaseModel):
    response_text: str = Field(..., description="La respuesta pedagógica principal dirigida al alumno")
    interactive_exercise: Optional[InteractiveExercise] = Field(None, description="Ejercicio interactivo estructurado si corresponde a la lección")

class ChatResponse(BaseModel):
    agent: str = Field(..., alias="agent_used", description="Agente que generó la respuesta")
    student_id: str = Field(..., description="ID del estudiante")
    session_id: Optional[str] = Field(None, description="ID de la sesión de chat")
    response_text: str = Field(..., alias="response_text", description="Respuesta textual del agente pedagógico")
    interactive_exercise: Optional[Dict[str, Any]] = Field(None, description="Estructura del ejercicio interactivo dinámico generado por IA")
    oa_metadata: Dict[str, Any] = Field(..., description="Metadatos del Objetivo de Aprendizaje")
    audio_response_b64: Optional[str] = Field(None, description="Respuesta en audio codificada en Base64 (si enable_audio=True)")
    audio_mime_type: Optional[str] = Field(None, description="Tipo MIME del audio (ej. audio/mpeg)")
    progress_record: Dict[str, Any] = Field(..., description="Registro de progreso del estudiante")
    code_review: Optional[Dict[str, Any]] = Field(None, description="Resultado de revisión de código si aplica")
    saved_progress: Optional[Dict[str, Any]] = Field(None, description="Resultado de persistencia en Supabase")

# --- Audio Chunk (Tarea 1: Modo Audio en Tiempo Real - REST) ---
class AudioChunkInput(BaseModel):
    student_id: str = Field(..., description="UUID del estudiante")
    session_id: str = Field(..., description="ID de la sesión de chat activa")
    curso: str = Field(..., description="Curso del estudiante (ej. 3ro Basico)")
    asignatura: str = Field(..., description="Asignatura (ej. Matematica)")
    id_oa: str = Field(..., description="ID del OA objetivo (ej. OA_01)")
    audio_base64: str = Field(..., description="Chunk de audio del micrófono codificado en Base64")
    chunk_ts: Optional[str] = Field(None, description="Timestamp UTC ISO del chunk para correlación")


class AudioChunkResponse(BaseModel):
    audio_base64: str = Field(..., description="Audio de respuesta generado por IA en Base64")
    mime_type: str = Field(default="audio/mpeg", description="Tipo MIME del audio de respuesta")
    session_id: str = Field(..., description="ID de la sesión correlacionada")
    transcript: str = Field(..., description="Texto transcrito de la respuesta pedagógica")


# --- Canvas Interactivo (Pizarra Compartida) ---
class CanvasInput(StudentIdUUIDMixin):
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

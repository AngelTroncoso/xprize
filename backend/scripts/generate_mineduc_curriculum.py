import json
import os
from typing import List, Dict, Any
from pydantic import BaseModel
from google import genai
from google.genai import types
import google.auth

class OA(BaseModel):
    codigo_oa: str
    descripcion: str
    indicadores_evaluacion: List[str]
    conceptos_clave: List[str]

class CurriculumUnit(BaseModel):
    curso: str
    asignatura: str
    eje_tematico: str
    objetivos_aprendizaje: List[OA]

class CurriculumResponse(BaseModel):
    unidades: List[CurriculumUnit]

def main():
    print("Iniciando generación de currículum MINEDUC (Vertex AI)...")
    credentials, project_id = google.auth.default()
    if not project_id:
        print("Error: No se pudo determinar el project_id. Asegúrate de haber hecho 'gcloud auth application-default login'")
        return

    # Usar el cliente genai con Vertex AI
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location="us-central1"
    )

    cursos = [
        "1° Básico", "2° Básico", "3° Básico", "4° Básico",
        "5° Básico", "6° Básico", "7° Básico", "8° Básico"
    ]
    asignaturas = [
        "Matemática", 
        "Lenguaje y Comunicación", 
        "Ciencias Naturales",
        "Historia y Geografía"
    ]

    todas_las_unidades = []

    for curso in cursos:
        for asignatura in asignaturas:
            print(f"Generando OAs para {curso} - {asignatura}...")
            
            prompt = f"""
            Actúa como el experto curricular del MINEDUC de Chile.
            Provee los Objetivos de Aprendizaje (OA) OFICIALES Y REALES (Bases Curriculares / Priorización) para:
            Curso: {curso}
            Asignatura: {asignatura}
            
            Agrupa los OA por su 'eje_tematico' real (ej. 'Números y Operaciones', 'Lectura', 'Ciencias de la Vida', etc.).
            Para cada OA incluye su código (ej. 'OA_01'), su descripción completa, una lista de indicadores de evaluación y conceptos clave.
            Incluye al menos los 3 a 5 OA más importantes por eje temático para que la malla sea representativa y rigurosa.
            """
            
            try:
                response = client.models.generate_content(
                    model='gemini-1.5-pro',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=CurriculumResponse,
                        temperature=0.1
                    )
                )
                if response.parsed and response.parsed.unidades:
                    todas_las_unidades.extend([u.model_dump() for u in response.parsed.unidades])
                    print(f"  -> OK. Añadidos {len(response.parsed.unidades)} ejes.")
                else:
                    print("  -> Respuesta vacía.")
            except Exception as e:
                print(f"  -> Error: {e}")

    output_path = os.path.join(
        os.path.dirname(__file__), 
        "../app/data/mallas_mineduc/malla_curricular_oficial.json"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(todas_las_unidades, f, ensure_ascii=False, indent=2)
    
    print(f"\n¡Proceso finalizado! Se guardó la malla en: {output_path}")

if __name__ == "__main__":
    main()

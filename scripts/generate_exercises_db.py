import os
import sys
import json
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
if not os.environ.get("SUPABASE_URL"):
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Credenciales de Supabase no encontradas en el archivo .env")
    sys.exit(1)

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY no encontrada en .env")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

async def generate_exercises_for_oa(id_oa: str, curso: str, asignatura: str):
    """
    Usa Gemini para generar 10 ejercicios progresivos para un OA específico
    y los inserta en Supabase.
    """
    print(f"Generando 10 ejercicios para OA: {id_oa} ({curso} - {asignatura})...")
    
    prompt = f"""
    Eres un experto pedagogo de Chile. Para el Objetivo de Aprendizaje o capítulo '{id_oa}' ({asignatura}, {curso}), 
    necesito que generes EXACTAMENTE 10 ejercicios interactivos con una dificultad progresiva (del 1 al 10).
    
    El formato de salida debe ser un JSON válido, sin markdown alrededor, con esta estructura:
    [
      {{
        "dificultad": 1,
        "contenido": {{
          "pregunta": "¿Cuánto es 2+2?",
          "tipo": "alternativa",
          "opciones": ["3", "4", "5"],
          "respuesta_correcta": "4",
          "explicacion": "Porque al sumar dos elementos más dos elementos, obtenemos cuatro."
        }},
        "feedback_inmediato": {{
          "acierto": "¡Excelente! Has sumado muy bien.",
          "error": "Recuerda usar tus dedos para contar. Intenta de nuevo."
        }}
      }}
    ]
    Asegúrate de que la dificultad 1 sea muy básica y la dificultad 10 sea un desafío avanzado. 
    ¡Devuelve ÚNICAMENTE la lista JSON!
    """
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        ejercicios = json.loads(text.strip())
        
        # Guardar en Supabase
        for ej in ejercicios:
            record = {
                "id_oa": id_oa,
                "curso": curso,
                "asignatura": asignatura,
                "dificultad": ej["dificultad"],
                "contenido": ej["contenido"],
                "feedback_inmediato": ej.get("feedback_inmediato", {})
            }
            supabase.table("exercises").insert(record).execute()
            
        print(f"✅ ¡10 ejercicios generados y guardados exitosamente para {id_oa}!")
        
    except Exception as e:
        print(f"❌ Error al generar/guardar para {id_oa}: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Uso: python generate_exercises_db.py <ID_OA_o_Capítulo> <Curso> <Asignatura>")
        print("Ejemplo: python generate_exercises_db.py 'Unidad 1: Números hasta el 1 000' '3° Básico' 'Matemática'")
        sys.exit(1)
        
    id_oa = sys.argv[1]
    curso = sys.argv[2]
    asignatura = sys.argv[3]
    
    asyncio.run(generate_exercises_for_oa(id_oa, curso, asignatura))

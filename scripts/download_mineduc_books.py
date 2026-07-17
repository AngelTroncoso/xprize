import os
import sys
import json
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno (asumimos que existe un .env en el directorio actual o superior)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Credenciales de Supabase no encontradas en el archivo .env")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================================================================
# NOTA IMPORTANTE PARA EL USUARIO:
# Actualmente, el Mineduc requiere acceso mediante RUT (catalogotextos.mineduc.cl)
# para descargar la mayoría de los textos escolares oficiales. 
#
# Este script utiliza un catálogo predefinido de enlaces de ejemplo. Si tienes 
# los enlaces directos a los PDFs, puedes agregarlos a este diccionario.
# Si tienes los PDFs localmente, podemos modificar el script para subirlos 
# directamente a Supabase Storage y a Gemini File API.
# ==============================================================================

BOOKS_CATALOG = [
    {
        "curso": "3° Básico",
        "asignatura": "Matemática",
        "titulo": "Texto del Estudiante Matemática 3° Básico",
        "portada_url": "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72016:Texto-del-Estudiante-Matematica-3-Basico.jpg", 
        "pdf_url": "https://www.curriculumnacional.cl/614/articles-145417_recurso_pdf.pdf", # URL Pública de ejemplo
        "gemini_file_id": "" # Aquí irá el ID de Gemini File API una vez subido
    },
    {
        "curso": "4° Básico",
        "asignatura": "Matemática",
        "titulo": "Texto del Estudiante Matemática 4° Básico",
        "portada_url": "https://www.curriculumnacional.cl/portal/Secciones/Textos-Escolares/72017:Texto-del-Estudiante-Matematica-4-Basico.jpg",
        "pdf_url": "https://www.curriculumnacional.cl/614/articles-145418_recurso_pdf.pdf",
        "gemini_file_id": ""
    }
    # ... Puedes agregar el resto de los cursos aquí.
]

def setup_database():
    """Crea la tabla textbooks en Supabase si no existe (usando RPC o manualmente)"""
    print("Configurando base de datos (se requiere crear la tabla 'textbooks' vía migraciones).")
    # Nota: Este script asume que la tabla 'textbooks' ya existe o se creará 
    # por separado en Supabase. Estructura:
    # id (uuid), curso (text), asignatura (text), titulo (text), portada_url (text), pdf_url (text), gemini_file_id (text)

def register_books():
    """Inserta los libros del catálogo en Supabase."""
    print(f"Registrando {len(BOOKS_CATALOG)} libros en la base de datos...")
    
    for book in BOOKS_CATALOG:
        # Verificar si el libro ya existe
        result = supabase.table("textbooks").select("id").eq("curso", book["curso"]).eq("asignatura", book["asignatura"]).execute()
        
        if result.data and len(result.data) > 0:
            print(f"✅ El libro '{book['titulo']}' ya está registrado.")
        else:
            # Insertar el nuevo libro
            try:
                res = supabase.table("textbooks").insert(book).execute()
                print(f"📥 Registrado nuevo libro: {book['titulo']}")
            except Exception as e:
                print(f"❌ Error al registrar {book['titulo']}: {e}")

def upload_to_gemini(local_pdf_path: str):
    """
    Subir PDF a Gemini File API.
    Requiere google-generativeai.
    """
    try:
        import google.generativeai as genai
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=GEMINI_API_KEY)
        
        print(f"Subiendo {local_pdf_path} a Gemini...")
        gemini_file = genai.upload_file(local_pdf_path, mime_type="application/pdf")
        print(f"Archivo subido a Gemini con ID: {gemini_file.name}")
        return gemini_file.name
    except ImportError:
        print("Falta google-generativeai. Ejecuta: pip install google-generativeai")
        return None
    except Exception as e:
        print(f"Error subiendo a Gemini: {e}")
        return None

if __name__ == "__main__":
    print("Iniciando integración de Textos Escolares MINEDUC...")
    setup_database()
    register_books()
    print("\nProceso finalizado. Puedes usar 'upload_to_gemini()' si cuentas con los PDFs locales.")

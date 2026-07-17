import os
import sys
import urllib.request
from dotenv import load_dotenv
from google import genai

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ No se encontró GEMINI_API_KEY en .env")
    sys.exit(1)

client = genai.Client(api_key=api_key)

BOOKS_TO_UPLOAD = [
    {
        "id": "mat-3",
        "titulo": "Matemática 3° Básico",
        "pdf_url": "https://www.curriculumnacional.cl/614/articles-145417_recurso_pdf.pdf",
        "filename": "mat-3.pdf"
    }
]

def download_file(url: str, filepath: str):
    print(f"Descargando {url}...")
    urllib.request.urlretrieve(url, filepath)
    print(f"Descarga completa: {filepath}")

def main():
    downloads_dir = os.path.join(os.path.dirname(__file__), "downloads")
    os.makedirs(downloads_dir, exist_ok=True)

    for book in BOOKS_TO_UPLOAD:
        filepath = os.path.join(downloads_dir, book["filename"])
        if not os.path.exists(filepath):
            download_file(book["pdf_url"], filepath)
        else:
            print(f"El archivo {filepath} ya existe, saltando descarga.")

        print(f"Subiendo {book['titulo']} a Gemini API...")
        # Upload to Gemini
        gemini_file = client.files.upload(file=filepath, config={"display_name": book["titulo"]})
        
        print(f"✅ {book['titulo']} subido correctamente!")
        print(f"ID del archivo (gemini_file_id): {gemini_file.name}")
        print("-" * 40)

if __name__ == "__main__":
    main()

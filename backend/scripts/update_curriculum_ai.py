import requests
import json
import os
import sys

BACKEND_URL = "https://superprofesor-backend-253925950091.us-central1.run.app"

CURSOS = [
    "1° Básico", "2° Básico", "3° Básico", "4° Básico",
    "5° Básico", "6° Básico", "7° Básico", "8° Básico"
]

ASIGNATURAS = [
    "Matemática", 
    "Lenguaje y Comunicación", 
    "Ciencias Naturales",
    "Historia y Geografía",
    "Inglés",
    "Música",
    "Arte",
    "Tecnología",
    "Educación Física y Salud"
]

def main():
    print("==========================================================")
    print("AGENTE CURRICULAR IA - ACTUALIZACIÓN DINÁMICA DEL MINEDUC")
    print("==========================================================")
    print("Este script consultará los modelos de IA de Google a través")
    print("del servidor backend para reconstruir o actualizar toda la")
    print("base de datos oficial de Objetivos de Aprendizaje (OAs).")
    
    todas_las_unidades = []

    for curso in CURSOS:
        for asignatura in ASIGNATURAS:
            print(f"Descargando {curso} - {asignatura}...")
            
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/curriculum/generate_oa",
                    params={"curso": curso, "asignatura": asignatura},
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "unidades" in data and isinstance(data["unidades"], list):
                        todas_las_unidades.extend(data["unidades"])
                        print(f"  -> ¡Éxito! Obtenidas {len(data['unidades'])} unidades temáticas.")
                    else:
                        print(f"  -> Advertencia: Respuesta inesperada de la IA para {asignatura}.")
                else:
                    print(f"  -> Error {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"  -> Error de red: {e}")

    if not todas_las_unidades:
        print("\n[!] No se pudieron obtener OAs. La base de datos no se modificará.")
        sys.exit(1)

    output_path = os.path.join(
        os.path.dirname(__file__), 
        "../app/data/mallas_mineduc/malla_curricular_oficial.json"
    )
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(todas_las_unidades, f, ensure_ascii=False, indent=2)
    
    print("\n==========================================================")
    print(f"¡ACTUALIZACIÓN COMPLETADA CON ÉXITO!")
    print(f"Se han generado y consolidado {len(todas_las_unidades)} registros estructurados.")
    print(f"Guardado en: {output_path}")
    print("Para aplicar los cambios a nivel global, redespliega el backend:")
    print("gcloud run deploy superprofesor-backend --source . --region us-central1 --allow-unauthenticated")
    print("==========================================================")

if __name__ == "__main__":
    main()

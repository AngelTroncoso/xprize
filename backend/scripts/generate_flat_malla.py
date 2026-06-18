"""
Genera malla_curricular_produccion.json (formato plano) desde curriculo_integrado.json
Extrayendo registros únicos (curso, asignatura, codigo_oa, eje, descripcion_oa)
"""
import json
import os
from pathlib import Path

CURRICULO_PATH = Path(__file__).resolve().parents[2] / "curriculo_integrado.json"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "mallas_mineduc" / "malla_curricular_produccion.json"

def main():
    with open(CURRICULO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    seen = set()
    records = []

    for curso_entry in data:
        curso = curso_entry.get("curso", "")
        proyectos = curso_entry.get("proyectos_integrados", [])

        for proyecto in proyectos:
            for obj in proyecto.get("objetivos_articulados", []):
                codigo_oa = obj.get("codigo_oa", "")
                asignatura = obj.get("asignatura", "")
                key = (curso, asignatura, codigo_oa)

                if key not in seen:
                    seen.add(key)
                    records.append({
                        "curso": curso,
                        "asignatura": asignatura,
                        "eje": obj.get("eje", ""),
                        "codigo_oa": codigo_oa,
                        "descripcion_oa": obj.get("descripcion_oa", "")
                    })

    records.sort(key=lambda r: (r["curso"], r["asignatura"], r["codigo_oa"]))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"✅ Archivo generado: {OUTPUT_PATH}")
    print(f"📊 Total registros OA únicos: {len(records)}")

if __name__ == "__main__":
    main()
"""
Merge script: Integrates nuevas_materias.json (MINEDUC Ciencias Naturales e Historia)
into curriculo_integrado.json preserving the existing structure and subjects.

Usage:
    python scripts/merge_curriculum.py
"""
import json
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULO_FILE = PROJECT_ROOT / "curriculo_integrado.json"
NUEVAS_FILE = PROJECT_ROOT / "nuevas_materias.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    print("🔀 Starting curriculum merge...")

    # --- Validate inputs ---
    if not CURRICULO_FILE.exists():
        raise FileNotFoundError(f"Missing file: {CURRICULO_FILE}")
    if not NUEVAS_FILE.exists():
        raise FileNotFoundError(f"Missing file: {NUEVAS_FILE}")

    curriculo = load_json(CURRICULO_FILE)
    nuevas = load_json(NUEVAS_FILE)

    # curriculo_integrado.json is a LIST of {curso, proyectos_integrados}
    # nuevas_materias.json is {asignaturas: {NombreAsignatura: {cursos: {NombreCurso: {unidades: [...]}}}}}

    if not isinstance(curriculo, list):
        raise ValueError("curriculo_integrado.json must be a JSON array at root level")
    if "asignaturas" not in nuevas:
        raise ValueError("nuevas_materias.json must contain 'asignaturas' at root level")

    nuevas_asignaturas = nuevas["asignaturas"]

    # Build a quick lookup: curso -> existing entry in curriculo list
    existing_cursos = {item["curso"]: item for item in curriculo}

    # Track added subjects per course for logging
    added_subjects: Dict[str, list] = {}

    for asignatura_nombre, data_asig in nuevas_asignaturas.items():
        cursos = data_asig.get("cursos", {})
        for curso_nombre, data_curso in cursos.items():
            unidades = data_curso.get("unidades", [])

            if not unidades:
                print(f"  ⚠️  No units found for {asignatura_nombre} / {curso_nombre}")
                continue

            # Ensure the course entry exists in the main curriculo list
            if curso_nombre not in existing_cursos:
                new_entry = {"curso": curso_nombre, "proyectos_integrados": []}
                curriculo.append(new_entry)
                existing_cursos[curso_nombre] = new_entry

            entry = existing_cursos[curso_nombre]

            # Convert units -> "proyectos_integrados" so the shape matches
            nuevos_proyectos = []
            for unidad in unidades:
                # Build objetivos_articulados in the format expected by the catalog
                objetivos_articulados = []
                for oa in unidad.get("objetivos_aprendizaje", []):
                    objetivos_articulados.append({
                        "asignatura": asignatura_nombre,
                        "codigo_oa": oa.get("id_oa", ""),
                        "eje": oa.get("eje", ""),
                        "descripcion_oa": oa.get("descripcion", ""),
                        "conceptos_clave": oa.get("conceptos_clave", []),
                        "indicadores_evaluacion": oa.get("indicadores_evaluacion", []),
                    })

                proyecto = {
                    "id_proyecto": unidad.get("id_unidad", ""),
                    "nombre_proyecto": unidad.get("nombre_unidad", ""),
                    "descripcion": (
                        f"Unidad curricular MINEDUC — {asignatura_nombre}. "
                        f"Eje: {unidades[0].get('objetivos_aprendizaje', [{}])[0].get('eje', '')}"
                        if unidades
                        else f"Unidad curricular MINEDUC — {asignatura_nombre}."
                    ),
                    "objetivos_articulados": objetivos_articulados,
                    "_source": "nuevas_materias.json",
                }
                nuevos_proyectos.append(proyecto)

            # Append without deduplicating Matemática/Lenguaje
            entry["proyectos_integrados"].extend(nuevos_proyectos)

            # Log
            if curso_nombre not in added_subjects:
                added_subjects[curso_nombre] = []
            added_subjects[curso_nombre].append(asignatura_nombre)

    # --- Write merged file ---
    with CURRICULO_FILE.open("w", encoding="utf-8") as f:
        json.dump(curriculo, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Merge completed successfully.")
    print(f"   Courses updated: {len(added_subjects)}")
    for curso, asigs in sorted(added_subjects.items()):
        print(f"   - {curso}: {', '.join(asigs)}")
    print(f"\n📁 Output written to: {CURRICULO_FILE}")


if __name__ == "__main__":
    main()
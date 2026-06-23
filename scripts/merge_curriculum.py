"""
Merge script: Integrates xprize/nuevas_materias_2.json into xprize/backend/data/curriculum_consolidado.json.

- Reads strictly from nuevas_materias_2.json
- Flattens "vertientes" on Religión / Formación Valórica into sub-asignaturas unified (ej: "Religión / Formación Valórica - Católica")
- Exports consolidated curriculum to backend/data/curriculum_consolidado.json
"""
import json
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NUEVAS_FILE = PROJECT_ROOT / "nuevas_materias_2.json"
OUTPUT_FILE = PROJECT_ROOT / "backend" / "data" / "curriculum_consolidado.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def flatten_vertientes(asignatura_nombre: str, data_asig: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    If the subject has a 'vertientes' key, expand each vertiente into a unified sub-subject key.
    Otherwise returns {asignatura_nombre: data_asig} (with 'cursos' extracted for uniformity).
    """
    if "vertientes" in data_asig:
        expanded = {}
        for vertiente_nombre, vertiente_data in data_asig["vertientes"].items():
            unified_name = f'{asignatura_nombre} - {vertiente_nombre}'
            expanded[unified_name] = vertiente_data
        return expanded
    else:
        return {asignatura_nombre: data_asig}


def main() -> None:
    print("🔀 Starting curriculum merge from xprize/nuevas_materias_2.json...")

    if not NUEVAS_FILE.exists():
        raise FileNotFoundError(f"Missing file: {NUEVAS_FILE}")

    nuevas = load_json(NUEVAS_FILE)
    if "asignaturas" not in nuevas:
        raise ValueError("nuevas_materias_2.json must contain 'asignaturas' at root level")

    nuevas_asignaturas = nuevas["asignaturas"]

    # Build consolidated structure preserving the shape used by downstream scripts:
    # {asignaturas: {NombreAsignatura: {cursos: {NombreCurso: {...}}}}}
    consolidated: Dict[str, Dict[str, Any]] = {"asignaturas": {}}

    added_subjects: Dict[str, list] = {}

    for asignatura_nombre, data_asig in nuevas_asignaturas.items():
        expanded_subjects = flatten_vertientes(asignatura_nombre, data_asig)

        for sub_nombre, sub_data in expanded_subjects.items():
            cursos = sub_data.get("cursos", {})
            if not cursos:
                print(f"  ⚠️  No courses found for {sub_nombre}")
                continue

            # Ensure the subject exists in consolidated map (accumulate if repeated)
            if sub_nombre not in consolidated["asignaturas"]:
                consolidated["asignaturas"][sub_nombre] = {"cursos": {}}

            for curso_nombre, data_curso in cursos.items():
                unidades = data_curso.get("unidades", [])
                if not unidades:
                    print(f"  ⚠️  No units found for {sub_nombre} / {curso_nombre}")
                    continue

                # Preserve curso entry in consolidated
                if curso_nombre not in consolidated["asignaturas"][sub_nombre]["cursos"]:
                    consolidated["asignaturas"][sub_nombre]["cursos"][curso_nombre] = {
                        "unidades": []
                    }

                # Append units for this curso (avoid duplicates if script re-run)
                existing_ids = {u.get("id_unidad") for u in consolidated["asignaturas"][sub_nombre]["cursos"][curso_nombre]["unidades"]}
                new_units = [u for u in unidades if u.get("id_unidad") not in existing_ids]
                consolidated["asignaturas"][sub_nombre]["cursos"][curso_nombre]["unidades"].extend(new_units)

                if curso_nombre not in added_subjects:
                    added_subjects[curso_nombre] = []
                added_subjects[curso_nombre].append(sub_nombre)

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(consolidated, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Merge completed successfully.")
    print(f"   Courses updated: {len(added_subjects)}")
    for curso, asigs in sorted(added_subjects.items()):
        print(f"   - {curso}: {', '.join(asigs)}")
    print(f"\n📁 Output written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
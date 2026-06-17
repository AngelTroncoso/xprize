import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

from dotenv import load_dotenv
from supabase import create_client


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "app" / "data" / "mallas_mineduc"


def _load_payloads() -> Iterable[tuple[Path, Dict[str, Any]]]:
    for file_path in sorted(DATA_DIR.glob("*.json")):
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    yield file_path, item
        elif isinstance(payload, dict):
            yield file_path, payload


def _required_text(payload: Dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Campo requerido ausente o invalido: {key}")
    return value.strip()


def _as_text_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def main() -> None:
    load_dotenv(BACKEND_DIR / ".env")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL y SUPABASE_KEY deben estar configuradas en backend/.env")

    client = create_client(url, key)
    units_count = 0
    objectives_count = 0

    for file_path, unit in _load_payloads():
        curso = _required_text(unit, "curso")
        asignatura = _required_text(unit, "asignatura")
        eje_tematico = _required_text(unit, "eje_tematico")

        unit_payload = {
            "curso": curso,
            "asignatura": asignatura,
            "eje_tematico": eje_tematico,
            "source_file": file_path.name,
        }
        unit_response = client.table("curriculum_units").upsert(
            unit_payload,
            on_conflict="curso,asignatura,eje_tematico",
        ).execute()

        unit_rows = unit_response.data or []
        if unit_rows:
            unit_id = unit_rows[0]["id"]
        else:
            lookup = client.table("curriculum_units").select("id").eq(
                "curso", curso
            ).eq("asignatura", asignatura).eq("eje_tematico", eje_tematico).single().execute()
            unit_id = lookup.data["id"]

        units_count += 1

        objectives = unit.get("objetivos_aprendizaje", [])
        if not isinstance(objectives, list):
            continue

        rows = []
        for oa in objectives:
            if not isinstance(oa, dict):
                continue
            rows.append({
                "unit_id": unit_id,
                "curso": curso,
                "asignatura": asignatura,
                "eje_tematico": eje_tematico,
                "id_oa": _required_text(oa, "id_oa"),
                "descripcion": _required_text(oa, "descripcion"),
                "indicadores_evaluacion": _as_text_list(oa.get("indicadores_evaluacion")),
                "conceptos_clave": _as_text_list(oa.get("conceptos_clave")),
                "metadata": {
                    key: value
                    for key, value in oa.items()
                    if key not in {"id_oa", "descripcion", "indicadores_evaluacion", "conceptos_clave"}
                },
            })

        if rows:
            client.table("curriculum_objectives").upsert(
                rows,
                on_conflict="curso,asignatura,id_oa",
            ).execute()
            objectives_count += len(rows)

    print(f"Curriculum sincronizado: {units_count} unidades, {objectives_count} objetivos.")


if __name__ == "__main__":
    main()

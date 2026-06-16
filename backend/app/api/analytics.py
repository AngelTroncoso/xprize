import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.models.database import db

router = APIRouter(prefix="/api", tags=["Analytics"])

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "mallas_mineduc"


def _list_malla_files() -> List[Path]:
    if not DATA_DIR.exists() or not DATA_DIR.is_dir():
        return []
    return sorted(DATA_DIR.glob("*.json"))


def _load_curriculum_units() -> List[Dict[str, Any]]:
    units: List[Dict[str, Any]] = []
    for file_path in _list_malla_files():
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue

        if isinstance(payload, list):
            units.extend(payload)
        elif isinstance(payload, dict):
            units.append(payload)

    return units


def _fetch_student_progress(student_id: str) -> Dict[str, Dict[str, Any]]:
    client = db.get_client()
    if not client:
        return {}

    try:
        response = client.table("student_oa_progress").select("*").eq(
            "student_id", student_id
        ).execute()
        rows = response.data or []
        if not isinstance(rows, list):
            return {}

        return {row["id_oa"]: row for row in rows if row.get("id_oa")}
    except Exception:
        return {}


def _build_curriculum_tree(
    units: List[Dict[str, Any]],
    progress_records: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    hierarchy: Dict[str, Dict[str, Any]] = {}

    for unit in units:
        curso = unit.get("curso", "Desconocido")
        asignatura = unit.get("asignatura", "General")
        eje_tematico = unit.get("eje_tematico", "Sin Eje Temático")

        curso_node = hierarchy.setdefault(curso, {"curso": curso, "asignaturas": {}})
        asignatura_node = curso_node["asignaturas"].setdefault(
            asignatura,
            {"asignatura": asignatura, "ejes": {}}
        )
        eje_node = asignatura_node["ejes"].setdefault(
            eje_tematico,
            {"eje_tematico": eje_tematico, "oas": []}
        )

        for oa in unit.get("objetivos_aprendizaje", []):
            oa_id = oa.get("id_oa")
            if not oa_id:
                continue

            record = progress_records.get(oa_id, {})
            mastery_level = record.get("mastery_level", "not_started")
            last_evaluation_date = record.get("last_evaluation_date")
            evaluation_history = record.get("evaluation_history", [])

            eje_node["oas"].append({
                "id_oa": oa_id,
                "descripcion": oa.get("descripcion", ""),
                "conceptos_clave": oa.get("conceptos_clave", []),
                "nivel_logro": mastery_level,
                "mastery_level": mastery_level,
                "last_evaluation_date": last_evaluation_date,
                "evaluation_count": len(evaluation_history),
            })

    result: List[Dict[str, Any]] = []
    for curso_node in hierarchy.values():
        asignaturas: List[Dict[str, Any]] = []
        for asignatura_node in curso_node["asignaturas"].values():
            ejes: List[Dict[str, Any]] = []
            for eje_node in asignatura_node["ejes"].values():
                ejes.append(eje_node)
            asignatura_node["ejes"] = ejes
            asignaturas.append(asignatura_node)
        curso_node["asignaturas"] = asignaturas
        result.append(curso_node)

    return result


def _summarize_progress(progress_records: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    counts = {"mastered": 0, "partial": 0, "in_progress": 0, "not_started": 0}
    for record in progress_records.values():
        level = record.get("mastery_level", "not_started")
        counts[level] = counts.get(level, 0) + 1
    return counts


def _count_tree_mastery(tree: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"mastered": 0, "partial": 0, "in_progress": 0, "not_started": 0}
    for curso in tree:
        for asignatura in curso.get("asignaturas", []):
            for eje in asignatura.get("ejes", []):
                for oa in eje.get("oas", []):
                    level = oa.get("mastery_level", "not_started")
                    counts[level] = counts.get(level, 0) + 1
    return counts


def _build_progress_response(student_id: str, tree: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = _count_tree_mastery(tree)
    total_oas = sum(totals.values())
    overall_percentage = round((totals["mastered"] * 100) / total_oas) if total_oas else 0

    return {
        "student_id": student_id,
        "curriculum_tree": tree,
        "summary": {
            "total_oas": total_oas,
            **totals,
            "overall_mastery_percentage": overall_percentage,
        },
    }


@router.get("/students/{student_id}/progress")
def get_student_progress(student_id: str):
    curriculum_units = _load_curriculum_units()
    if not curriculum_units:
        raise HTTPException(
            status_code=500,
            detail="No se encontraron archivos de malla curricular en backend/app/data/mallas_mineduc.",
        )

    progress_records = _fetch_student_progress(student_id)
    tree = _build_curriculum_tree(curriculum_units, progress_records)
    response = _build_progress_response(student_id, tree)
    response["data_source"] = "supabase" if db.get_client() and progress_records else "mock"
    return response

"""
Seed script for curriculum tables in Supabase.
Reads the flat malla_curricular_produccion.json (87 OA records)
and upserts into curriculum_units and curriculum_objectives tables.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from supabase import create_client


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "app" / "data" / "mallas_mineduc"


def _load_flat_records() -> List[Dict[str, Any]]:
    """Loads the flat OA records from malla_curricular_produccion.json"""
    file_path = DATA_DIR / "malla_curricular_produccion.json"
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    load_dotenv(BACKEND_DIR / ".env")

    url = os.getenv("SUPABASE_URL")
    # Use SUPABASE_SECRET_KEY if available (service_role privileges bypasses RLS), else fallback to SUPABASE_KEY
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY (or SUPABASE_KEY) must be set in backend/.env")

    client = create_client(url, key)
    records = _load_flat_records()
    print(f"📄 Loaded {len(records)} flat OA records from malla_curricular_produccion.json")

    # Organize records by (curso, asignatura, eje) -> [records]
    from collections import OrderedDict

    units_map: Dict[str, Dict[str, Any]] = OrderedDict()

    for rec in records:
        curso = rec.get("curso", "")
        asignatura = rec.get("asignatura", "")
        eje = rec.get("eje", "")
        key = f"{curso}|{asignatura}|{eje}"

        if key not in units_map:
            units_map[key] = {
                "curso": curso,
                "asignatura": asignatura,
                "eje_tematico": eje,
                "source_file": "malla_curricular_produccion.json",
                "objetivos": [],
            }

        units_map[key]["objetivos"].append({
            "codigo_oa": rec.get("codigo_oa", ""),
            "descripcion_oa": rec.get("descripcion_oa", ""),
        })

    units_count = 0
    objectives_count = 0

    for key, unit in units_map.items():
        curso = unit["curso"]
        asignatura = unit["asignatura"]
        eje = unit["eje_tematico"]

        # Insert / upsert curriculum unit
        unit_payload = {
            "curso": curso,
            "asignatura": asignatura,
            "eje_tematico": eje,
            "source_file": unit["source_file"],
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
            ).eq("asignatura", asignatura).eq("eje_tematico", eje).single().execute()
            unit_id = lookup.data["id"]

        units_count += 1

        # Insert objectives for this unit
        rows = []
        for obj in unit["objetivos"]:
            source_record = next((r for r in records if r.get("codigo_oa") == obj["codigo_oa"] and r.get("asignatura") == asignatura), {})
            row_payload = {
                "unit_id": unit_id,
                "curso": curso,
                "asignatura": asignatura,
                "eje_tematico": eje,
                "id_oa": obj["codigo_oa"],
                "descripcion": obj["descripcion_oa"],
                "indicadores_evaluacion": source_record.get("indicadores_evaluacion", []),
                "conceptos_clave": source_record.get("conceptos_clave", []),
                "metadata": {},
            }
            # clave_compuesta se agregará después de aplicar la migración 004
            rows.append(row_payload)

        if rows:
            client.table("curriculum_objectives").upsert(
                rows,
                on_conflict="curso,asignatura,id_oa",
            ).execute()
            objectives_count += len(rows)

        print(f"  ✅ Unit '{curso} | {asignatura} | {eje}': {len(rows)} objectives upserted")

    print(f"\n{'='*60}")
    print(f"📊 Curriculum sync complete:")
    print(f"   Units: {units_count}")
    print(f"   Objectives: {objectives_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
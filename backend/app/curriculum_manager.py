import json
import logging
import os
from typing import Any, Dict, List, Optional

from app.models.schemas import CurriculumUnit, ObjetivoAprendizaje

logger = logging.getLogger(__name__)


class CurriculumManager:
    """Gestor ligero para cargar e interrogar mallas curriculares.

    Actualmente apunta a `data/mallas_mineduc/matematica_3basico.json` pero
    permite extenderse para cargar múltiples unidades en el futuro.
    """

    def __init__(self, data_paths: Optional[List[str]] = None) -> None:
        self._units: List[Dict[str, Any]] = []
        self._oa_index: Dict[str, Dict[str, Any]] = {}

        # Por defecto, carga la malla de 3ro básico que ya existe en el repo
        if data_paths is None:
            base = os.path.dirname(__file__)
            default_path = os.path.join(base, "data", "mallas_mineduc", "matematica_3basico.json")
            data_paths = [default_path]

        for path in data_paths:
            try:
                self._load_and_index(path)
            except Exception as exc:
                logger.exception("Error cargando currículo desde %s: %s", path, exc)

    def _load_and_index(self, path: str) -> None:
        """Carga un archivo JSON y lo indexa por `id_oa`.

        Si el archivo contiene una unidad curricular válida, la añade al
        listado interno y registra cada `ObjetivoAprendizaje` en el índice.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Archivo de currículo no encontrado: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # El JSON puede ser una lista de unidades o una sola unidad
        units = data if isinstance(data, list) else [data]

        for unit in units:
            try:
                # Validar unidad mínima con Pydantic
                CurriculumUnit.parse_obj(unit)
                self._units.append(unit)
                for oa in unit.get("objetivos_aprendizaje", []):
                    oa_id = oa.get("id_oa")
                    if oa_id:
                        # Guardar referencia completa incluyendo metadatos de la unidad
                        self._oa_index[oa_id] = {"curso": unit.get("curso"),
                                                 "asignatura": unit.get("asignatura"),
                                                 "eje_tematico": unit.get("eje_tematico"),
                                                 **oa}
            except Exception as exc:
                logger.warning("Unidad curricular inválida en %s: %s", path, exc)

    def get_oa_by_id(self, id_oa: str) -> Optional[Dict[str, Any]]:
        """Devuelve la representación validada (dict) de un OA por su `id_oa`.

        Retorna None si no existe; no lanza excepción para facilitar consumo por agentes.
        """
        raw = self._oa_index.get(id_oa)
        if not raw:
            logger.debug("OA no encontrado: %s", id_oa)
            return None

        try:
            oa_obj: ObjetivoAprendizaje = ObjetivoAprendizaje.parse_obj(raw)
            return oa_obj.dict()
        except Exception as exc:
            # Si la validación falla, registramos y devolvemos el contenido crudo
            logger.exception("Fallo validación OA %s: %s", id_oa, exc)
            return raw

    def get_oas_by_concept(self, concept: str) -> List[Dict[str, Any]]:
        """Busca todos los OA que contengan `concept` en sus `conceptos_clave`.

        La búsqueda es case-insensitive y admite coincidencias parciales.
        """
        if not concept:
            return []

        q = concept.strip().lower()
        results: List[Dict[str, Any]] = []

        for oa_id, oa_data in self._oa_index.items():
            conceptos = oa_data.get("conceptos_clave", []) or []
            conceptos_lower = [str(c).lower() for c in conceptos]
            if any(q in c or c in q for c in conceptos_lower):
                try:
                    validated = ObjetivoAprendizaje.parse_obj(oa_data).dict()
                    results.append(validated)
                except Exception:
                    # Fallback: devolver la versión cruda si falla la validación
                    results.append(oa_data)

        return results

    def all_oa_ids(self) -> List[str]:
        """Retorna una lista de todos los `id_oa` indexados."""
        return list(self._oa_index.keys())


__all__ = ["CurriculumManager"]

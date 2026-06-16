from typing import Dict, Any, List, Optional

EXTERNAL_RESOURCES = [
    {
        "name": "Wikipedia API",
        "type": "API",
        "url": "https://www.mediawiki.org/wiki/API:Main_page",
        "purpose": "Proporciona acceso a artículos enciclopédicos, definiciones, biografías, historia, ciencias y cultura general.",
        "output_format": "JSON / REST",
        "category": "General Knowledge"
    },
    {
        "name": "Wikimedia REST API",
        "type": "API",
        "url": "https://api.wikimedia.org",
        "purpose": "Acceso a contenidos estructurados, imágenes, resúmenes de artículos y recursos multimedia.",
        "output_format": "JSON / REST",
        "category": "Media"
    },
    {
        "name": "Khan Academy API",
        "type": "API",
        "url": "https://www.khanacademy.org/api/v1",
        "purpose": "Ejercicios, videos, rutas de aprendizaje de matemáticas, ciencias, historia y programación para educación básica.",
        "output_format": "JSON / REST",
        "category": "Gamification & Exercises"
    },
    {
        "name": "UNESCO DataHub API",
        "type": "API",
        "url": "https://data.unesco.org/api/v1/console",
        "purpose": "Acceso a estadísticas educativas, indicadores globales de aprendizaje y políticas internacionales.",
        "output_format": "JSON / REST",
        "category": "Statistics"
    },
    {
        "name": "PhET Interactive Simulations",
        "type": "Repositorio",
        "url": "https://phet.colorado.edu",
        "purpose": "Simulaciones interactivas para enseñanza de matemáticas, física, química y ciencias naturales.",
        "output_format": "HTML / Estático",
        "category": "Simulations"
    },
    {
        "name": "GeoGebra Resources",
        "type": "Repositorio",
        "url": "https://www.geogebra.org",
        "purpose": "Recursos interactivos para matemáticas, geometría, álgebra y visualización de conceptos abstractos.",
        "output_format": "JSON / HTML",
        "category": "Simulations"
    },
    {
        "name": "CK-12 Foundation",
        "type": "Repositorio",
        "url": "https://www.ck12.org",
        "purpose": "Contenido K-12 en matemáticas y ciencias con simulaciones y ejercicios adaptativos.",
        "output_format": "Estático",
        "category": "Gamification & Exercises"
    },
    {
        "name": "OpenAlex API",
        "type": "API",
        "url": "https://api.openalex.org",
        "purpose": "Acceso a literatura científica global, autores, instituciones y conceptos educativos.",
        "output_format": "JSON / REST",
        "category": "Research"
    },
    {
        "name": "ERIC",
        "type": "Repositorio",
        "url": "https://eric.ed.gov",
        "purpose": "Principal fuente mundial de investigación educativa, estrategias pedagógicas y estudios de aprendizaje infantil.",
        "output_format": "Estático",
        "category": "Research"
    }
]

class ResourceResolver:
    @staticmethod
    def select_resource(subject: str, needs_interactive: bool = False, needs_research: bool = False) -> Dict[str, Any]:
        """
        Mapeo Semántico: Selecciona dinámicamente el mejor recurso basándose en la materia e interactividad necesaria.
        """
        subj = subject.lower()
        
        if needs_research:
            return next(r for r in EXTERNAL_RESOURCES if r["category"] == "Research")
            
        if "matem" in subj or "cienc" in subj or "físic" in subj or "quím" in subj:
            if needs_interactive:
                return next(r for r in EXTERNAL_RESOURCES if r["name"] == "PhET Interactive Simulations")
            return next(r for r in EXTERNAL_RESOURCES if r["name"] == "Khan Academy API")
            
        if "histor" in subj or "social" in subj or "lengua" in subj:
            return next(r for r in EXTERNAL_RESOURCES if r["name"] == "Wikipedia API")
            
        # Fallback general
        return next(r for r in EXTERNAL_RESOURCES if r["name"] == "Wikimedia REST API")

    @staticmethod
    def simulate_payload(resource_name: str, query: str) -> Dict[str, Any]:
        """
        Simula mentalmente el payload de consulta hacia la API del recurso para validación.
        """
        if "Wikipedia" in resource_name:
            return {
                "method": "GET",
                "url": f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json",
                "headers": {"User-Agent": "SuperProfesor/1.0"}
            }
        elif "Khan" in resource_name:
            return {
                "method": "GET",
                "url": f"https://www.khanacademy.org/api/v1/topic/{query.lower()}/exercises",
                "headers": {"Accept": "application/json"}
            }
        elif "OpenAlex" in resource_name:
            return {
                "method": "GET",
                "url": f"https://api.openalex.org/works?filter=title.search:{query}",
                "headers": {"User-Agent": "mailto:admin@superprofesor.org"}
            }
        
        return {
            "method": "GET",
            "url": f"https://api.example.com/search?q={query}",
            "headers": {"Accept": "application/json"}
        }

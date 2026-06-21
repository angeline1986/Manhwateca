from pathlib import Path

from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
)
from manhwateca.database.manga_repository import MangaRepository


CATALOG_PATH = Path("data/mangas.json")


def active_catalog_source(project_root, repository_factory=MangaRepository):
    try:
        mangas = repository_factory().list_mangas()
    except (DatabaseConfigurationError, DatabaseConnectionError) as error:
        return {
            "kind": "json",
            "label": "JSON legado",
            "detail": str(CATALOG_PATH),
            "count": _json_catalog_count(project_root),
            "fallback_reason": str(error),
        }

    return {
        "kind": "postgresql",
        "label": "PostgreSQL",
        "detail": "vw_mangas",
        "count": len(mangas),
        "mangas": mangas,
    }


def _json_catalog_count(project_root):
    path = Path(project_root) / CATALOG_PATH
    if not path.is_file():
        return 0
    try:
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    return len(data) if isinstance(data, list) else 0

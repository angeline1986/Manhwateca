import json
import os
from pathlib import Path


CATALOG_FILE = Path("data/mangas.json")
MANGAUPDATES_FILE = Path("data/mangaupdates.json")
CSV_FILE = Path("reports/integrations/manhwateca_import.csv")


def build_status(project_root):
    project_root = Path(project_root)
    catalog_path = project_root / CATALOG_FILE
    catalog_count, catalog_error = _catalog_info(catalog_path)
    manga_root = os.getenv("MANGA_ROOT", "").strip()
    notion_ready = all(
        os.getenv(name, "").strip()
        for name in ("NOTION_TOKEN", "NOTION_DATABASE_ID")
    )
    return {
        "application": "Manhwateca",
        "status": "ok",
        "version": "web-1.0",
        "catalog": {
            "available": catalog_path.is_file() and catalog_error is None,
            "count": catalog_count,
            "path": str(CATALOG_FILE),
            "error": catalog_error,
        },
        "library": {
            "configured": bool(manga_root),
            "available": bool(manga_root) and Path(manga_root).is_dir(),
        },
        "mangaupdates": {
            "cache_available": (project_root / MANGAUPDATES_FILE).is_file(),
            "csv_available": (project_root / CSV_FILE).is_file(),
        },
        "notion": {"configured": notion_ready},
    }


def _catalog_info(path):
    if not path.is_file():
        return 0, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return 0, str(error)
    if not isinstance(data, list):
        return 0, "Formato inválido: era esperada uma lista."
    return len(data), None

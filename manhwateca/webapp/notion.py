import json
import os
from pathlib import Path

from dotenv import load_dotenv

from manhwateca.library_organizer.discovery import find_manga_folders
from manhwateca.library_organizer.grouping import (
    is_group_folder,
    is_legacy_container,
)
from manhwateca.library_organizer.discovery import is_manga_folder
from manhwateca.shared.titles import get_canonical_manga_name
from manhwateca.webapp.data_source import active_catalog_source


STATUS_PATH = Path("reports/integrations/notion_import_status.json")
CATALOG_PATH = Path("data/mangas.json")

load_dotenv()


def notion_status(project_root):
    path = Path(project_root) / STATUS_PATH
    if not path.is_file():
        return _empty_status()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_status(error="O arquivo de status está inválido.")
    summary = data.get("resumo", {})
    library_names, catalog_names, source = _local_library_state(project_root)
    status_catalog_total = summary.get("total_catalogo", 0)
    uncataloged = sorted(
        library_names - catalog_names,
        key=str.casefold,
    )
    stale = status_catalog_total != len(catalog_names)
    return {
        "available": True,
        "stale": stale,
        "updated_at": data.get("atualizado_em"),
        "mode": data.get("modo"),
        "summary": {
            "catalog": summary.get("total_catalogo", 0),
            "current_catalog": len(catalog_names),
            "imported": summary.get("total_importadas", 0),
            "current_batch": summary.get("importadas_neste_lote", 0),
            "pending": summary.get("total_pendentes", 0),
            "duplicates": summary.get("total_duplicadas", 0),
            "library": len(library_names),
            "uncataloged": len(uncataloged),
        },
        "source": source,
        "current_batch": data.get("importadas_neste_lote", []),
        "pending": data.get("pendentes", []),
        "duplicates": data.get("duplicadas", []),
        "uncataloged": uncataloged,
        "error": None,
    }


def _local_library_state(project_root):
    source = active_catalog_source(project_root)
    if source["kind"] == "postgresql":
        catalog_names = {
            record.title
            for record in source.get("mangas", [])
            if getattr(record, "title", None)
        }
    else:
        catalog_path = Path(project_root) / CATALOG_PATH
        try:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            catalog = []
        catalog_names = {
            item.get("nome")
            for item in catalog
            if isinstance(item, dict) and item.get("nome")
        }

    root_value = os.getenv("MANGA_ROOT", "").strip()
    if not root_value:
        return catalog_names, catalog_names, _public_source(source)
    library_root = Path(root_value).expanduser()
    if not library_root.is_dir():
        return catalog_names, catalog_names, _public_source(source)
    folders = find_manga_folders(
        library_root,
        is_group_folder,
        lambda path: is_manga_folder(
            path,
            is_group_folder,
            is_legacy_container,
        ),
    )
    library_names = {
        get_canonical_manga_name(folder.name)
        for folder in folders
    }
    return library_names, catalog_names, _public_source(source)


def _public_source(source):
    return {
        key: value
        for key, value in source.items()
        if key != "mangas"
    }


def _empty_status(error=None):
    return {
        "available": False,
        "stale": False,
        "updated_at": None,
        "mode": None,
        "summary": {
            "catalog": 0,
            "current_catalog": 0,
            "imported": 0,
            "current_batch": 0,
            "pending": 0,
            "duplicates": 0,
            "library": 0,
            "uncataloged": 0,
        },
        "source": {"kind": "unknown", "label": "Indisponível"},
        "current_batch": [],
        "pending": [],
        "duplicates": [],
        "uncataloged": [],
        "error": error,
    }

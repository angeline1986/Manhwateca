import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*_args, **_kwargs):
        return False

from manhwateca.library_organizer.discovery import find_manga_folders
from manhwateca.library_organizer.grouping import (
    is_group_folder,
    is_legacy_container,
)
from manhwateca.library_organizer.discovery import is_manga_folder
from manhwateca.notion_sync.matching import normalize_title
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
    library_names, catalog_names, catalog_keys, source = _local_library_state(project_root)
    status_catalog_total = summary.get("total_catalogo", 0)
    uncataloged = sorted(
        [
            name
            for name in library_names
            if normalize_title(name) not in catalog_keys
        ],
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
        records = source.get("mangas", [])
        catalog_names = {
            record.title
            for record in records
            if getattr(record, "title", None)
        }
        catalog_keys = _catalog_keys_from_records(records)
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
        catalog_keys = {normalize_title(name) for name in catalog_names if name}

    root_value = os.getenv("MANGA_ROOT", "").strip()
    if not root_value:
        return catalog_names, catalog_names, catalog_keys, _public_source(source)
    library_root = Path(root_value).expanduser()
    if not library_root.is_dir():
        return catalog_names, catalog_names, catalog_keys, _public_source(source)
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
    return library_names, catalog_names, catalog_keys, _public_source(source)


def _catalog_keys_from_records(records):
    keys = set()
    for record in records:
        for name in _record_names(record):
            normalized = normalize_title(name)
            if normalized:
                keys.add(normalized)
    return keys


def _record_names(record):
    title = getattr(record, "title", None)
    if title:
        yield title
    alternative = getattr(record, "alternative_title", None)
    if not alternative:
        return
    for separator in ("|", ";"):
        alternative = alternative.replace(separator, "\n")
    for name in alternative.splitlines():
        name = name.strip()
        if name:
            yield name


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

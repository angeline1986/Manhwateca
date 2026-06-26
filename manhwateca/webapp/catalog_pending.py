import os
from pathlib import Path

from manhwateca.catalog.scanner import build_manga, save_mangas_to_database
from manhwateca.library_organizer.discovery import find_manga_folders
from manhwateca.library_organizer.discovery import is_manga_folder
from manhwateca.library_organizer.grouping import (
    is_group_folder,
    is_legacy_container,
)
from manhwateca.shared.titles import get_canonical_manga_name
from manhwateca.webapp.notion import notion_status


def catalog_single_work(name: str) -> dict:
    name = str(name or "").strip()
    if not name:
        raise ValueError("Informe a obra para catalogar.")

    folder = _find_work_folder(name)
    if folder is None:
        raise KeyError(name)

    manga = build_manga(folder, {})
    saved = save_mangas_to_database([manga])
    return {
        "saved": saved,
        "work": manga["nome"],
        "path": str(folder),
    }


def reconcile_catalog_aliases(project_root: Path | str = ".") -> dict:
    project_root = Path(project_root)
    status = notion_status(project_root)
    pending = status.get("uncataloged", [])
    if status.get("source", {}).get("kind") != "postgresql":
        return {
            "applied": 0,
            "skipped": len(pending),
            "reason": "PostgreSQL indisponível.",
            "items": [],
        }

    return {
        "applied": 0,
        "skipped": len(pending),
        "items": [],
        "reason": "Atualização feita diretamente contra PostgreSQL; nenhum JSON foi usado.",
    }


def _find_work_folder(name: str) -> Path | None:
    root_value = os.getenv("MANGA_ROOT", "").strip()
    if not root_value:
        raise RuntimeError("MANGA_ROOT não configurado.")

    library_root = Path(root_value).expanduser()
    if not library_root.is_dir():
        raise RuntimeError("MANGA_ROOT não está acessível.")

    expected = get_canonical_manga_name(name).casefold()
    folders = find_manga_folders(
        library_root,
        is_group_folder,
        lambda path: is_manga_folder(
            path,
            is_group_folder,
            is_legacy_container,
        ),
    )
    for folder in folders:
        if get_canonical_manga_name(folder.name).casefold() == expected:
            return folder
    return None

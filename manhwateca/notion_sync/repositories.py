import csv
import json

from manhwateca.database import MangaRepository


def load_mangas(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Catálogo não encontrado: {path}. Execute scripts/scan.py primeiro."
        )
    with path.open("r", encoding="utf-8") as file:
        mangas = json.load(file)
    if not isinstance(mangas, list):
        raise ValueError(f"Formato inválido em {path}: era esperada uma lista.")
    return mangas


def load_mangas_from_database(repository=None):
    repository = repository or MangaRepository()
    return [
        _manga_record_to_catalog_item(manga)
        for manga in repository.list_mangas()
    ]


def load_csv_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_metadata(path):
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, dict) else {}


def _manga_record_to_catalog_item(manga):
    return {
        "nome": manga.title,
        "alias": _aliases(manga.alternative_title),
        "status": _notion_status(manga.reading_status),
        "nota": _notion_note(manga),
        "ultimo_lido": _number_or_zero(manga.last_read_chapter),
        "main_caps": _number_or_zero(manga.latest_available_chapter),
        "chapters_found": _number_or_zero(manga.latest_available_chapter),
        "side_stories_found": 0,
        "tamanho": manga.size_label or "Curto",
        "count_status": manga.count_status or "OK",
        "mangaupdates_latest_chapter": _number_or_none(
            manga.latest_mangaupdates_chapter
        ),
        "mangaupdates_url": manga.mangaupdates_url,
        "tematica": manga.themes or [],
        "formato": manga.format,
        "universo": [],
        "nivel_picancia": manga.spice_level,
        "notion_page_id": manga.notion_page_id,
        "notion_sync_status": manga.notion_sync_status,
    }


def _aliases(value):
    if not value:
        return []
    return [item.strip() for item in str(value).split("|") if item.strip()]


def _notion_status(value):
    mapping = {
        "Quero Ler": "Quero ler",
        "Aguardando Atualização": "Em espera",
    }
    value = str(value or "").strip()
    return mapping.get(value, value or "Quero ler")


def _notion_note(manga):
    if manga.personal_rank in {"Topzera", "Legalzin"}:
        return manga.personal_rank
    return "Ok"


def _number_or_zero(value):
    value = _number_or_none(value)
    return 0 if value is None else value


def _number_or_none(value):
    if value is None:
        return None
    number = float(value)
    return int(number) if number.is_integer() else number

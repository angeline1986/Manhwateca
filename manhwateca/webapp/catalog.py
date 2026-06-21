import json
from pathlib import Path

from manhwateca.database.manga_repository import MangaRepository
from manhwateca.webapp.data_source import active_catalog_source


CATALOG_PATH = Path("data/mangas.json")
COMPARISON_FIELDS = (
    "ultimo_lido",
    "proximo_a_ler",
    "main_caps",
    "tamanho",
    "chapters_found",
    "side_stories_found",
    "count_status",
)


def load_database_catalog(repository_factory=MangaRepository):
    repository = repository_factory()
    return [_database_manga(record) for record in repository.list_mangas()]


def load_catalog(project_root):
    path = Path(project_root) / CATALOG_PATH
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def catalog_payload(project_root, latest_changes=None, repository_factory=MangaRepository):
    source = active_catalog_source(project_root, repository_factory)
    if source["kind"] == "postgresql":
        mangas = [_database_manga(record) for record in source.get("mangas", [])]
    else:
        mangas = load_catalog(project_root)

    return {
        "source": _public_source(source),
        "summary": build_summary(mangas),
        "changes": latest_changes or {"new": [], "updated": [], "removed": []},
        "mangas": [public_manga(manga) for manga in mangas],
    }


def _public_source(source):
    return {
        key: value
        for key, value in source.items()
        if key != "mangas"
    }


def build_summary(mangas):
    return {
        "total": len(mangas),
        "main_caps": sum(manga.get("main_caps", 0) for manga in mangas),
        "side_stories": sum(
            manga.get("side_stories_found", 0) for manga in mangas
        ),
        "review": sum(
            bool(_actionable_issues(manga) or manga.get("unparsed_files"))
            for manga in mangas
        ),
        "unparsed": sum(
            len(manga.get("unparsed_files", [])) for manga in mangas
        ),
    }


def compare_catalogs(before, after):
    old = {manga["nome"]: manga for manga in before}
    new = {manga["nome"]: manga for manga in after}
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    updated = []
    for name in sorted(set(old) & set(new)):
        changes = {
            field: {"before": old[name].get(field), "after": new[name].get(field)}
            for field in COMPARISON_FIELDS
            if old[name].get(field) != new[name].get(field)
        }
        if changes:
            updated.append({"nome": name, "fields": changes})
    return {"new": added, "updated": updated, "removed": removed}


def public_manga(manga):
    return {
        "nome": manga.get("nome"),
        "alias": manga.get("alias", []),
        "ultimo_lido": manga.get("ultimo_lido", 0),
        "proximo_a_ler": manga.get("proximo_a_ler", 1),
        "main_caps": manga.get("main_caps", 0),
        "tamanho": manga.get("tamanho", "Curto"),
        "chapters_found": manga.get("chapters_found", 0),
        "side_stories_found": manga.get("side_stories_found", 0),
        "count_status": manga.get("count_status", "Revisar"),
        "count_issues": _actionable_issues(manga),
        "unparsed_files": manga.get("unparsed_files", []),
        "mangaupdates_latest_chapter": manga.get(
            "mangaupdates_latest_chapter"
        ),
        "reading_status": manga.get("reading_status"),
        "personal_rank": manga.get("personal_rank"),
        "themes": manga.get("themes", []),
    }


def _actionable_issues(manga):
    ignored = {"lacunas", "somente side stories"}
    issues = [
        issue for issue in manga.get("count_issues", [])
        if issue not in ignored
    ]
    return issues


def _database_manga(record):
    last_read = _number(record.last_read_chapter, default=0)
    latest = _number(record.latest_available_chapter, default=0)
    return {
        "nome": record.title,
        "alias": _split_aliases(record.alternative_title),
        "ultimo_lido": last_read,
        "proximo_a_ler": last_read + 1 if latest else 1,
        "main_caps": latest,
        "tamanho": record.size_label or "Curto",
        "chapters_found": latest,
        "side_stories_found": 0,
        "count_status": record.count_status or "OK",
        "count_issues": [],
        "unparsed_files": [],
        "mangaupdates_latest_chapter": _number(
            record.latest_mangaupdates_chapter,
            default=None,
        ),
        "reading_status": record.reading_status,
        "personal_rank": record.personal_rank,
        "themes": record.themes or [],
    }


def _split_aliases(value):
    if not value:
        return []
    return [item.strip() for item in str(value).split("|") if item.strip()]


def _number(value, default=0):
    if value is None:
        return default
    number = float(value)
    return int(number) if number.is_integer() else number

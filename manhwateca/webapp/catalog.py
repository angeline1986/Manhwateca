import json
from pathlib import Path


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


def load_catalog(project_root):
    path = Path(project_root) / CATALOG_PATH
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def catalog_payload(project_root, latest_changes=None):
    mangas = load_catalog(project_root)
    return {
        "summary": build_summary(mangas),
        "changes": latest_changes or {"new": [], "updated": [], "removed": []},
        "mangas": [public_manga(manga) for manga in mangas],
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
    }


def _actionable_issues(manga):
    ignored = {"lacunas", "somente side stories"}
    issues = [
        issue for issue in manga.get("count_issues", [])
        if issue not in ignored
    ]
    return issues

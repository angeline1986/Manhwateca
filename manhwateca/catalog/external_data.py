import json
from pathlib import Path

from manhwateca.shared.titles import get_canonical_manga_name


MANGAUPDATES_CACHE = Path("data/mangaupdates.json")


def load_mangaupdates_cache(path=MANGAUPDATES_CACHE):
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        get_canonical_manga_name(title).casefold(): metadata
        for title, metadata in data.items()
    }


def apply_external_data(manga: dict, external: dict | None) -> dict:
    if not external:
        return manga

    manga.update({
        "formato": external.get("format"),
        "universo": external.get("universe", []),
        "mangaupdates_id": external.get("series_id"),
        "mangaupdates_url": external.get("url"),
        "mangaupdates_latest_chapter": external.get("latest_chapter"),
        "mangaupdates_status": external.get("status"),
        "mangaupdates_completed": external.get("completed"),
        "mangaupdates_genres": external.get("genres", []),
        "mangaupdates_categories": external.get("categories", []),
    })

    external_chapter = external.get("latest_chapter")
    if external_chapter is not None and external_chapter != manga["main_caps"]:
        manga["count_status"] = "Divergência externa"
        manga["count_issues"] = [
            *manga["count_issues"],
            "MangaUpdates divergente",
        ]

    return manga

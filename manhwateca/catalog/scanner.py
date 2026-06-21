from pathlib import Path

from manhwateca.catalog.discovery import find_manga_folders
from manhwateca.catalog.external_data import load_mangaupdates_cache
from manhwateca.catalog.external_data import apply_external_data
from manhwateca.catalog.editorial_merge import apply_saved_editorial
from manhwateca.database.manga_repository import MangaRepository
from manhwateca.shared.chapters import scan_chapters
from manhwateca.shared.media import get_cover_file
from manhwateca.shared.paths import get_required_path_env
from manhwateca.shared.sizing import classify_manga_size
from manhwateca.shared.titles import get_canonical_manga_name


def build_manga(manga_folder: Path, external_cache: dict) -> dict:
    chapter_data = scan_chapters(manga_folder)
    manga_name = get_canonical_manga_name(manga_folder.name)
    manga = {
        "nome": manga_name,
        "alias": [],
        "status": "Quero ler",
        "nota": "Ok",
        "ultimo_lido": chapter_data["last_read"],
        "proximo_a_ler": chapter_data["next_to_read"],
        "main_caps": chapter_data["main_caps"],
        "tamanho": classify_manga_size(chapter_data["main_caps"]),
        "side_caps": chapter_data["side_caps"],
        "total_caps": chapter_data["total_caps"],
        "chapters_found": chapter_data["chapters_found"],
        "side_stories_found": chapter_data["side_stories_found"],
        "missing_chapters": chapter_data["missing_chapters"],
        "missing_ranges": chapter_data["missing_ranges"],
        "count_status": chapter_data["count_status"],
        "count_issues": chapter_data["count_issues"],
        "unparsed_files": chapter_data["unparsed_files"],
        "chapter_files": chapter_data["chapter_files"],
        "side_files": chapter_data["side_files"],
        "cover": get_cover_file(manga_folder),
        "path": str(manga_folder),
    }
    return apply_external_data(
        manga,
        external_cache.get(manga_name.casefold()),
    )


def scan_mangas(
    manga_root: Path | None = None,
    external_cache: dict | None = None,
) -> list[dict]:
    manga_root = manga_root or get_required_path_env("MANGA_ROOT")
    if not manga_root.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {manga_root}")

    external_cache = (
        load_mangaupdates_cache()
        if external_cache is None
        else external_cache
    )
    mangas = [
        build_manga(folder, external_cache)
        for folder in find_manga_folders(manga_root)
    ]
    return sorted(
        apply_saved_editorial(mangas),
        key=lambda item: item["nome"].lower(),
    )


def save_mangas_to_database(
    mangas: list[dict],
    repository_factory=MangaRepository,
) -> int:
    repository = repository_factory()
    return repository.save_catalog_mangas(mangas)

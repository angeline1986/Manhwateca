
import json
from pathlib import Path

from dotenv import load_dotenv

from utils import (
    classify_manga_size,
    clean_manga_name,
    get_cover_file,
    get_canonical_manga_name,
    get_required_path_env,
    scan_chapters,
)


load_dotenv()

OUTPUT_FILE = Path("data/mangas.json")
MANGAUPDATES_CACHE = Path("data/mangaupdates.json")

GROUP_FOLDERS = {
    "0-9",
    "A",
    "BC",
    "DE",
    "FG",
    "HIJ",
    "KLM",
    "NO",
    "PQR",
    "ST",
    "UVW",
    "XYZ",
}

IGNORED_FOLDERS = {
    "Topzera",
    "Legalzin",
    "Lendo",
    "Fila_Espera",
    "Longos",
    "Grande",
    "Medio",
    "Médio",
    "Curto",
    "Novos",
    "Finalizado",
    "Despriorizado",
    "Aguardando",
}


def is_group_folder(path: Path) -> bool:
    return path.is_dir() and path.name in GROUP_FOLDERS


def is_ignored_folder(path: Path) -> bool:
    return path.is_dir() and path.name in IGNORED_FOLDERS


def is_manga_folder(path: Path) -> bool:
    if is_ignored_folder(path):
        return False

    chapter_data = scan_chapters(path)

    return (
        chapter_data["chapter_files"] > 0
        or chapter_data["side_files"] > 0
    )


def find_manga_folders(root: Path) -> list[Path]:
    manga_folders = []

    for path in root.rglob("*"):
        if not path.is_dir():
            continue

        if is_group_folder(path):
            continue

        if is_ignored_folder(path):
            continue

        if is_manga_folder(path):
            manga_folders.append(path)

    return manga_folders


def load_mangaupdates_cache(path=MANGAUPDATES_CACHE):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return {
        get_canonical_manga_name(title).casefold(): metadata
        for title, metadata in data.items()
    }


def scan_mangas() -> list[dict]:
    manga_root = get_required_path_env("MANGA_ROOT")

    if not manga_root.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {manga_root}")

    mangas = []
    external_cache = load_mangaupdates_cache()

    manga_folders = find_manga_folders(manga_root)

    for manga_folder in manga_folders:
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
        external = external_cache.get(manga_name.casefold())
        if external:
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
            if (
                external_chapter is not None
                and external_chapter != manga["main_caps"]
            ):
                manga["count_status"] = "Divergência externa"
                manga["count_issues"] = [
                    *manga["count_issues"],
                    "MangaUpdates divergente",
                ]
        mangas.append(manga)

    mangas = sorted(mangas, key=lambda item: item["nome"].lower())

    return mangas


def save_mangas(mangas: list[dict]) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            mangas,
            file,
            ensure_ascii=False,
            indent=2
        )


def main() -> None:
    manga_root = get_required_path_env("MANGA_ROOT")
    mangas = scan_mangas()
    save_mangas(mangas)

    total_main_caps = sum(m["main_caps"] for m in mangas)
    total_side_caps = sum(m["side_caps"] for m in mangas)
    total_chapter_files = sum(m["chapter_files"] for m in mangas)

    print(f"Pasta raiz: {manga_root}")
    print()
    print(f"Total de obras encontradas: {len(mangas)}")
    print(f"Total de capítulos principais: {total_main_caps}")
    print(f"Total de side stories: {total_side_caps}")
    print(f"Total de arquivos de capítulo: {total_chapter_files}")
    print()
    print(f"Arquivo gerado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

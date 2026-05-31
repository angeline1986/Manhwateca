
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from utils import (
    clean_manga_name,
    get_cover_file,
    scan_chapters,
)


load_dotenv()

MANGA_ROOT = Path(os.getenv("MANGA_ROOT", "")).expanduser()
OUTPUT_FILE = Path("data/mangas.json")

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


def scan_mangas() -> list[dict]:
    if not MANGA_ROOT:
        raise ValueError("MANGA_ROOT não foi definido no .env")

    if not MANGA_ROOT.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {MANGA_ROOT}")

    mangas = []

    manga_folders = find_manga_folders(MANGA_ROOT)

    for manga_folder in manga_folders:
        chapter_data = scan_chapters(manga_folder)

        manga_name = clean_manga_name(manga_folder.name)

        mangas.append({
            "nome": manga_name,
            "alias": [],
            "status": "Quero ler",
            "nota": "Ok",
            "ultimo_lido": 0,

            "main_caps": chapter_data["main_caps"],
            "side_caps": chapter_data["side_caps"],
            "total_caps": chapter_data["total_caps"],

            "chapter_files": chapter_data["chapter_files"],
            "side_files": chapter_data["side_files"],

            "cover": get_cover_file(manga_folder),
            "path": str(manga_folder),
        })

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
    mangas = scan_mangas()
    save_mangas(mangas)

    total_main_caps = sum(m["main_caps"] for m in mangas)
    total_side_caps = sum(m["side_caps"] for m in mangas)
    total_chapter_files = sum(m["chapter_files"] for m in mangas)

    print(f"Pasta raiz: {MANGA_ROOT}")
    print()
    print(f"Total de obras encontradas: {len(mangas)}")
    print(f"Total de capítulos principais: {total_main_caps}")
    print(f"Total de side stories: {total_side_caps}")
    print(f"Total de arquivos de capítulo: {total_chapter_files}")
    print()
    print(f"Arquivo gerado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

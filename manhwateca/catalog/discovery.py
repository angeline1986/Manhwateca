from pathlib import Path

from manhwateca.shared.chapters import scan_chapters


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


GROUP_FOLDERS = {
    "0-9", "A", "BC", "DE", "FG", "HIJ",
    "KLM", "NO", "PQR", "ST", "UVW", "XYZ",
}

IGNORED_FOLDERS = {
    "Topzera", "Legalzin", "Lendo", "Fila_Espera",
    "Longos", "Grande", "Medio", "Médio", "Curto",
    "Novos", "Finalizado", "Despriorizado", "Aguardando",
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
        or any(
            file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS
            for file in path.iterdir()
        )
    )


def find_manga_folders(root: Path) -> list[Path]:
    manga_folders = []

    for path in root.rglob("*"):
        if not path.is_dir():
            continue
        if is_group_folder(path) or is_ignored_folder(path):
            continue
        if is_manga_folder(path):
            manga_folders.append(path)

    return manga_folders

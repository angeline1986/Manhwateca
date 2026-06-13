from pathlib import Path


MEDIA_EXTENSIONS = {
    ".pdf",
    ".cbz",
    ".jpg",
    ".jpeg",
    ".png",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
PREFERRED_COVER_NAMES = [
    "cover.jpg",
    "cover.jpeg",
    "cover.png",
    "folder.jpg",
    "folder.png",
]


def get_cover_file(manga_path: Path):
    for name in PREFERRED_COVER_NAMES:
        file_path = manga_path / name
        if file_path.exists():
            return str(file_path)

    for file in manga_path.iterdir():
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS:
            return str(file)

    return None

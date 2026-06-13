from manhwateca.shared.chapters import scan_chapters
from manhwateca.shared.media import MEDIA_EXTENSIONS


IGNORED_FILES = {".DS_Store", "Thumbs.db"}


def is_manga_folder(path, is_group_folder, is_legacy_container):
    if is_group_folder(path.name) or is_legacy_container(path):
        return False

    chapter_data = scan_chapters(path)
    if chapter_data["chapter_files"] > 0 or chapter_data["side_files"] > 0:
        return True

    entries = [
        entry for entry in path.iterdir() if entry.name not in IGNORED_FILES
    ]
    media_files = [
        entry
        for entry in entries
        if entry.is_file() and entry.suffix.lower() in MEDIA_EXTENSIONS
    ]
    return bool(media_files)


def find_empty_legacy_folders(root, is_legacy_container):
    empty_folders = []
    for path in root.rglob("*"):
        if not path.is_dir() or not is_legacy_container(path.parent):
            continue
        entries = [
            entry for entry in path.iterdir() if entry.name not in IGNORED_FILES
        ]
        if not entries:
            empty_folders.append(path)
    return empty_folders


def find_manga_folders(root, is_group_folder, manga_detector):
    manga_folders = []
    for path in root.rglob("*"):
        if not path.is_dir() or is_group_folder(path.name):
            continue
        if manga_detector(path):
            manga_folders.append(path)
    return manga_folders

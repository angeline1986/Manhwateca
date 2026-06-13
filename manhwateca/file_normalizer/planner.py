import unicodedata
from collections import defaultdict

from manhwateca.file_normalizer.grouping import get_group
from manhwateca.file_normalizer.naming import normalize_chapter_name


CHAPTER_EXTENSIONS = {".pdf", ".cbz"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def build_plan(root, canonical_name):
    plan = defaultdict(lambda: defaultdict(list))
    images_by_folder = defaultdict(list)

    for file in root.rglob("*"):
        if not file.is_file():
            continue
        if file.suffix.lower() in IMAGE_EXTENSIONS:
            images_by_folder[file.parent].append(file)
        elif file.suffix.lower() in CHAPTER_EXTENSIONS:
            _plan_chapter(plan, file, canonical_name)

    for manga_folder, images in images_by_folder.items():
        _plan_covers(plan, manga_folder, images, canonical_name)
    return plan


def _plan_chapter(plan, file, canonical_name):
    manga_name = canonical_name(file.parent.name)
    new_name = normalize_chapter_name(file.name, manga_name)
    if unicodedata.normalize("NFC", new_name) == unicodedata.normalize(
        "NFC", file.name
    ):
        return
    plan[get_group(manga_name)][manga_name].append({
        "old_name": file.name,
        "new_name": new_name,
        "old_path": str(file),
        "new_path": str(file.with_name(new_name)),
        "kind": "chapter",
    })


def _plan_covers(plan, manga_folder, images, canonical_name):
    manga_name = canonical_name(manga_folder.name)
    for image in images:
        new_name = f"cover{image.suffix.lower()}"
        if image.name.casefold() == new_name.casefold():
            continue
        plan[get_group(manga_name)][manga_name].append({
            "old_name": image.name,
            "new_name": new_name,
            "old_path": str(image),
            "new_path": str(image.with_name(new_name)),
            "kind": "cover",
            "multiple_images": len(images) > 1,
        })

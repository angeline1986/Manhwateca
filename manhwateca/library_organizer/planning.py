import unicodedata
from collections import defaultdict
from pathlib import Path

from manhwateca.shared.chapters import scan_chapters
from manhwateca.shared.titles import get_canonical_manga_name


def build_plan(manga_folders, manga_root, get_group, get_current_group):
    plan = []
    for manga_folder in manga_folders:
        clean_name = get_canonical_manga_name(manga_folder.name)
        group = get_group(clean_name)
        destination = manga_root / group / clean_name
        chapter_data = scan_chapters(manga_folder)
        plan.append({
            "name": clean_name,
            "source": manga_folder,
            "destination": destination,
            "group": group,
            "current_group": get_current_group(manga_folder),
            "exists": destination.exists(),
            "is_correct": _same_structural_path(manga_folder, destination),
            "main_caps": chapter_data["main_caps"],
            "side_caps": chapter_data["side_caps"],
            "total_caps": chapter_data["total_caps"],
        })
    return plan


def _same_structural_path(source, destination):
    return _normalized_path(source) == _normalized_path(destination)


def _normalized_path(path):
    return unicodedata.normalize("NFC", str(Path(path)))


def detect_conflicts(plan):
    conflicts = []
    destination_map = defaultdict(list)
    for item in plan:
        destination_map[str(item["destination"])].append(item)

    for destination, items in destination_map.items():
        destination_path = Path(destination)
        conflicting = [
            item
            for item in items
            if _destination_conflicts(item["source"], destination_path)
        ]
        duplicated = len(items) > 1
        if conflicting and duplicated:
            reason = "both"
            conflict_items = items
        elif conflicting:
            reason = "destino_existente"
            conflict_items = conflicting
        elif duplicated:
            reason = "destino_duplicado"
            conflict_items = items
        else:
            continue
        conflicts.append({
            "destination": destination,
            "items": conflict_items,
            "reason": reason,
        })
    return conflicts


def _destination_conflicts(source, destination):
    if not destination.exists():
        return False
    try:
        return not source.samefile(destination)
    except FileNotFoundError:
        return True


def determine_status(item, conflicts, duplicates):
    if item["is_correct"]:
        return "Já está correto"
    if any(item in conflict["items"] for conflict in conflicts):
        return "Conflito"
    if any(
        item["name"] in [entry["original"] for entry in duplicate["entries"]]
        for duplicate in duplicates
    ):
        return "Duplicado suspeito"
    return "Será movido"

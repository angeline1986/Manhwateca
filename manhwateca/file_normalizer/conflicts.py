import re
import unicodedata
from collections import defaultdict
from pathlib import Path


def detect_conflicts(plan):
    conflicts = []
    for group, mangas in plan.items():
        for manga_name, files in mangas.items():
            new_names = {}
            for item in files:
                _append_item_conflicts(
                    conflicts, new_names, group, manga_name, item
                )
    return conflicts


def _append_item_conflicts(conflicts, new_names, group, manga_name, item):
    new_name = item["new_name"]
    old_path = Path(item["old_path"])
    new_path = Path(item["new_path"])
    base = {"group": group, "manga": manga_name}

    if item.get("multiple_images"):
        conflicts.append({
            **base,
            "files": [item],
            "conflict_name": new_name,
            "reason": "multiplas_imagens",
        })
    if new_path.exists() and not old_path.samefile(new_path):
        conflicts.append({
            **base,
            "files": [item],
            "conflict_name": new_name,
            "reason": "destino_existente",
        })
    if new_name in new_names:
        conflicts.append({
            **base,
            "files": [new_names[new_name], item],
            "conflict_name": new_name,
        })
    else:
        new_names[new_name] = item


def detect_duplicates(plan):
    duplicates = []
    name_map = defaultdict(list)
    for group, mangas in plan.items():
        for manga_name, files in mangas.items():
            name_map[normalize_for_duplicate_detection(manga_name)].append({
                "original": manga_name,
                "group": group,
                "files": files,
            })
    for normalized, entries in name_map.items():
        originals = {entry["original"] for entry in entries}
        if len(entries) > 1 and len(originals) > 1:
            duplicates.append({"normalized": normalized, "entries": entries})
    return duplicates


def normalize_for_duplicate_detection(name):
    name = name.strip()
    lowered = name.lower()
    for article in ("a ", "o ", "os ", "as ", "the "):
        if lowered.startswith(article):
            name = name[len(article):].strip()
            break
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    return re.sub(r"\s+", " ", name).strip().lower()

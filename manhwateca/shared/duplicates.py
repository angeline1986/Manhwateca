import re
import unicodedata
from collections import defaultdict


def normalize_for_duplicate_detection(name):
    name = name.strip()
    articles = ["a ", "o ", "os ", "as ", "the "]
    name_lower = name.lower()

    for article in articles:
        if name_lower.startswith(article):
            name = name[len(article):].strip()
            break

    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    return re.sub(r"\s+", " ", name).strip().lower()


def detect_duplicates_organize(plan):
    duplicates = []
    name_map = defaultdict(list)

    for item in plan:
        normalized = normalize_for_duplicate_detection(item["name"])
        name_map[normalized].append({
            "original": item["name"],
            "source": str(item["source"]),
            "destination": str(item["destination"]),
            "group": item["group"],
        })

    for normalized, entries in name_map.items():
        if len(entries) > 1:
            duplicates.append({
                "normalized": normalized,
                "entries": entries,
            })

    return duplicates

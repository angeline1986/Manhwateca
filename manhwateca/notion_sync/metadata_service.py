from manhwateca.notion_sync.csv_properties import build_properties, split_values
from manhwateca.notion_sync.matching import csv_equivalent_names
from manhwateca.notion_sync.pages import load_existing_pages
from manhwateca.notion_sync.repositories import load_metadata


def update_from_csv(notion, database_id, rows, apply=False, metadata=None):
    existing = load_existing_pages(notion, database_id)
    metadata = {} if metadata is None else metadata
    summary = {
        "updated": 0,
        "updates": [],
        "missing": [],
        "duplicates": [],
    }
    for row in rows:
        name = row.get("Nome", "").strip()
        matches = _find_matches(row, metadata, existing)
        if not matches:
            summary["missing"].append(name)
            print(f"[AUSENTE NO NOTION] {name}")
        elif len(matches) > 1:
            summary["duplicates"].append(name)
            print(f"[DUPLICADO NO NOTION] {name}")
        else:
            summary["updated"] += 1
            properties = build_properties(row)
            summary["updates"].append({
                "name": name,
                "properties": sorted(properties),
            })
            print(f"[ATUALIZAR] {name}")
            if apply:
                notion.pages.update(
                    page_id=matches[0]["id"],
                    properties=properties,
                )
    return summary


def _find_matches(row, metadata, existing):
    matches = {}
    for candidate in csv_equivalent_names(row, metadata, split_values):
        for page in existing.get(candidate, []):
            matches[page["id"]] = page
    return list(matches.values())

import csv
import json
import re
import unicodedata


CONFIRMED_STATUSES = {
    "Confirmado automaticamente",
    "Confirmado manualmente",
}


def normalize_title(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = value.encode("ascii", "ignore").decode().casefold()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def load_json_object(path):
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, dict) else {}


def count_confirmed_without_details(items, cache_path):
    cache = load_json_object(cache_path)
    return sum(
        1
        for item in items
        if item.get("Status") in CONFIRMED_STATUSES
        and item.get("ID")
        and str(item["ID"]) not in cache
    )


def consolidate_review_items(items, csv_path=None, metadata_path=None):
    review_items = [
        item for item in items
        if item.get("Status") == "Revisar" and item.get("IDs")
    ]
    if not csv_path or not csv_path.exists():
        return review_items

    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    row_index = _build_row_index(rows)
    _add_metadata_names(row_index, metadata_path)
    confirmed_positions = _confirmed_positions(items, row_index)
    return _group_review_items(
        review_items,
        rows,
        row_index,
        confirmed_positions,
    )


def _build_row_index(rows):
    row_index = {}
    for position, row in enumerate(rows):
        for value in (row.get("Nome"), row.get("Alias")):
            for title in str(value or "").split("|"):
                if title.strip():
                    row_index.setdefault(normalize_title(title), position)
    return row_index


def _add_metadata_names(row_index, metadata_path):
    metadata = load_json_object(metadata_path)
    for local_title, values in metadata.items():
        names = [values.get("nome_oficial"), values.get("alias"), local_title]
        position = next(
            (
                row_index[normalize_title(name)]
                for name in names
                if name and normalize_title(name) in row_index
            ),
            None,
        )
        if position is not None:
            for name in names:
                if name:
                    row_index.setdefault(normalize_title(name), position)


def _confirmed_positions(items, row_index):
    return {
        row_index[normalize_title(item.get("Nome"))]
        for item in items
        if item.get("Status") in CONFIRMED_STATUSES
        and item.get("ID")
        and normalize_title(item.get("Nome")) in row_index
    }


def _group_review_items(review_items, rows, row_index, confirmed_positions):
    grouped = {}
    for item in review_items:
        position = row_index.get(normalize_title(item.get("Nome")))
        if (
            position is None
            or position in confirmed_positions
            or str(rows[position].get("ID da obra") or "").strip()
        ):
            continue
        group = grouped.setdefault(position, {
            "Nome": rows[position].get("Nome") or item.get("Nome"),
            "Nome decisão": item.get("Nome"),
            "Nomes relacionados": [],
            "Status": "Revisar",
            "IDs": [],
        })
        group["Nomes relacionados"].append(item.get("Nome"))
        known_ids = {candidate.get("id") for candidate in group["IDs"]}
        group["IDs"].extend(
            candidate
            for candidate in item.get("IDs", [])
            if candidate.get("id") not in known_ids
        )
        group["IDs"].sort(
            key=lambda candidate: (
                -float(candidate.get("pontuacao") or 0),
                candidate.get("posicao") or 999,
            )
        )
    return list(grouped.values())

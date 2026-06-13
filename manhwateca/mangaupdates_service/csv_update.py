import csv

from manhwateca.mangaupdates_service.candidates import (
    CONFIRMED_STATUSES,
    load_id_searches,
)
from manhwateca.mangaupdates_service.csv_export import (
    CSV_COLUMNS,
    join_values,
)
from manhwateca.mangaupdates_service.matching import normalize_title
from manhwateca.mangaupdates_service.repository import load_json_object


def update_csv_from_confirmed_ids(
    ids_path,
    csv_path,
    cache_path,
    metadata_path,
    limit=None,
):
    items = load_id_searches(ids_path)
    confirmed = [
        item
        for item in items
        if item.get("Status") in CONFIRMED_STATUSES and item.get("ID")
    ]
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV não encontrado: {csv_path}. Gere o CSV antes de atualizá-lo."
        )

    rows, fieldnames = _read_csv(csv_path)
    row_index = _build_row_index(rows)
    _add_metadata_names(row_index, metadata_path)

    cache = load_json_object(cache_path)
    processed = 0
    updated = 0
    uncached = []
    missing_from_csv = []
    handled_ids = set()

    for item in confirmed:
        if limit is not None and processed >= limit:
            break
        series_id = item["ID"]
        if series_id in handled_ids:
            continue
        handled_ids.add(series_id)

        name = item["Nome"].strip()
        position = row_index.get(normalize_title(name))
        if position is None:
            missing_from_csv.append(name)
            continue

        summary = cache.get(str(series_id))
        if not summary:
            uncached.append(name)
            continue

        row = rows[position]
        values = _external_values(item, row, summary, series_id)
        changed = any(
            str(row.get(field, "")) != str(value)
            for field, value in values.items()
        )
        row.update(values)
        processed += 1
        updated += int(changed)

    _write_csv(csv_path, rows, fieldnames)
    return updated, processed, uncached, missing_from_csv


def _read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader), reader.fieldnames or CSV_COLUMNS


def _build_row_index(rows):
    row_index = {}
    for position, row in enumerate(rows):
        for value in (row.get("Nome"), row.get("Alias")):
            if not value:
                continue
            for title in value.split("|"):
                row_index.setdefault(normalize_title(title.strip()), position)
    return row_index


def _add_metadata_names(row_index, metadata_path):
    metadata = load_json_object(metadata_path)
    for local_title, values in metadata.items():
        candidates = [values.get("nome_oficial"), values.get("alias")]
        position = next(
            (
                row_index.get(normalize_title(candidate))
                for candidate in candidates
                if candidate
                and row_index.get(normalize_title(candidate)) is not None
            ),
            None,
        )
        if position is not None:
            row_index.setdefault(normalize_title(local_title), position)


def _external_values(item, row, summary, series_id):
    return {
        "ID da obra": summary.get("series_id", series_id),
        "Capítulo MangaUpdates": summary.get("latest_chapter") or "",
        "MangaUpdates": summary.get("url") or "",
        "Temática": join_values(summary.get("genres", [])),
        "Formato": summary.get("format") or row.get("Formato", ""),
        "Universo": join_values(summary.get("universe", [])),
        "Correspondência API": (
            "ID confirmado manualmente"
            if item["Status"] == "Confirmado manualmente"
            else "ID confirmado automaticamente"
        ),
    }


def _write_csv(path, rows, fieldnames):
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)

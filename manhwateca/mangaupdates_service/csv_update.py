import csv

from manhwateca.database import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    MangaRepository,
)
from manhwateca.mangaupdates_service.candidates import (
    CONFIRMED_STATUSES,
    load_catalog,
    load_id_searches,
)
from manhwateca.mangaupdates_service.csv_export import (
    CSV_COLUMNS,
    build_csv_row,
    join_values,
)
from manhwateca.mangaupdates_service.matching import normalize_title
from manhwateca.mangaupdates_service.repository import load_json_object


ORPHAN_STATUS = "Fora do catálogo local"


def update_csv_from_confirmed_ids(
    ids_path,
    csv_path,
    cache_path,
    metadata_path,
    catalog_path=None,
    limit=None,
    database_repository=None,
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
    fieldnames = _complete_fieldnames(fieldnames)
    row_index = _build_row_index(rows)
    metadata = load_json_object(metadata_path)
    _add_metadata_names(row_index, metadata)

    cache = load_json_object(cache_path)
    catalog = _build_catalog_index(catalog_path, metadata)
    processed = 0
    updated = 0
    uncached = []
    missing_from_csv = []
    handled_ids = set()
    active_names = {normalize_title(item["Nome"]) for item in confirmed}
    database = database_repository or _optional_database_repository()

    for item in confirmed:
        if limit is not None and processed >= limit:
            break
        series_id = item["ID"]
        if series_id in handled_ids:
            continue
        handled_ids.add(series_id)

        name = item["Nome"].strip()
        position = row_index.get(normalize_title(name))
        summary = cache.get(str(series_id))
        if position is None:
            manga = catalog.get(normalize_title(name))
            if manga and summary:
                row = _new_row_from_catalog(item, manga, summary, metadata)
                rows.append(_normalize_row(row, fieldnames))
                position = len(rows) - 1
                _index_row(row_index, rows[position], position)
                _update_database(database, name, item, summary)
                processed += 1
                updated += 1
                continue
            if manga and not summary:
                uncached.append(name)
                continue
            missing_from_csv.append(name)
            continue

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
        _update_database(database, name, item, summary)
        processed += 1
        updated += int(changed)

    updated += _mark_orphan_rows(rows, catalog, active_names)
    _write_csv(csv_path, rows, fieldnames)
    return updated, processed, uncached, missing_from_csv


def _read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader), reader.fieldnames or CSV_COLUMNS


def _build_row_index(rows):
    row_index = {}
    for position, row in enumerate(rows):
        _index_row(row_index, row, position)
    return row_index


def _index_row(row_index, row, position):
    for value in (row.get("Nome"), row.get("Alias")):
        if not value:
            continue
        for title in value.split("|"):
            row_index.setdefault(normalize_title(title.strip()), position)


def _add_metadata_names(row_index, metadata):
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


def _build_catalog_index(catalog_path, metadata):
    if not catalog_path or not catalog_path.exists():
        return {}
    index = {}
    for manga in load_catalog(catalog_path):
        names = {manga.get("nome", "")}
        names.update(manga.get("alias", []))
        configured = metadata.get(manga.get("nome", ""), {})
        names.update(
            value
            for value in (
                configured.get("nome_oficial"),
                configured.get("alias"),
            )
            if value
        )
        for name in names:
            if name:
                index.setdefault(normalize_title(name), manga)
    return index


def _mark_orphan_rows(rows, catalog, active_names):
    if not catalog:
        return 0
    changed = 0
    for row in rows:
        if _row_in_catalog(row, catalog):
            continue
        if _row_in_names(row, active_names):
            continue
        if row.get("Correspondência API") == ORPHAN_STATUS:
            continue
        row["Correspondência API"] = ORPHAN_STATUS
        changed += 1
    return changed


def _row_in_catalog(row, catalog):
    return _row_in_names(row, catalog)


def _row_in_names(row, names):
    for value in (row.get("Nome"), row.get("Alias")):
        if not value:
            continue
        for title in value.split("|"):
            if normalize_title(title.strip()) in names:
                return True
    return False


def _new_row_from_catalog(item, manga, summary, metadata):
    configured = metadata.get(manga.get("nome", ""), {})
    row = build_csv_row(
        manga,
        external=summary,
        progress={"match_status": _match_status(item)},
        metadata=configured,
    )
    row.update(_external_values(item, row, summary, item["ID"]))
    return row


def _match_status(item):
    return (
        "ID confirmado manualmente"
        if item["Status"] == "Confirmado manualmente"
        else "ID confirmado automaticamente"
    )


def _complete_fieldnames(fieldnames):
    completed = list(fieldnames or [])
    for field in CSV_COLUMNS:
        if field not in completed:
            completed.append(field)
    return completed


def _normalize_row(row, fieldnames):
    return {field: row.get(field, "") for field in fieldnames}


def _external_values(item, row, summary, series_id):
    return {
        "ID da obra": summary.get("series_id", series_id),
        "Capítulo MangaUpdates": summary.get("latest_chapter") or "",
        "MangaUpdates": summary.get("url") or "",
        "Temática": join_values(summary.get("genres", [])),
        "Formato": summary.get("format") or row.get("Formato", ""),
        "Universo": join_values(summary.get("universe", [])),
        "Correspondência API": _match_status(item),
    }


def _write_csv(path, rows, fieldnames):
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _optional_database_repository():
    try:
        return MangaRepository()
    except Exception:
        return None


def _update_database(repository, name, item, summary):
    if repository is None:
        return False
    try:
        return repository.update_mangaupdates_fields(
            name,
            item.get("ID"),
            summary,
        )
    except (DatabaseConfigurationError, DatabaseConnectionError, Exception):
        return False

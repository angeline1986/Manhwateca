import csv
import json
from pathlib import Path

from manhwateca.notion_sync.matching import normalize_title


CSV_PATH = Path("reports/integrations/manhwateca_import.csv")
METADATA_PATH = Path("config/catalog_metadata.json")


def apply_saved_editorial(mangas, csv_path=CSV_PATH, metadata_path=METADATA_PATH):
    if not csv_path.is_file():
        return mangas
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    metadata = _load_metadata(metadata_path)
    row_index = _row_index(rows, metadata)
    for manga in mangas:
        row = row_index.get(normalize_title(manga["nome"]))
        if row:
            _merge(manga, row)
    return mangas


def _row_index(rows, metadata):
    result = {}
    for row in rows:
        names = {row.get("Nome"), row.get("Alias")}
        for local_name, values in metadata.items():
            configured = {
                local_name, values.get("nome_oficial"), values.get("alias")
            }
            if {normalize_title(name) for name in names if name} & {
                normalize_title(name) for name in configured if name
            }:
                names.update(configured)
        for name in names:
            if name:
                result[normalize_title(name)] = row
    return result


def _merge(manga, row):
    scalar = {
        "Status": "status", "Nota": "nota", "Interesse": "interesse",
        "Picância": "nivel_picancia",
    }
    for source, target in scalar.items():
        if row.get(source):
            manga[target] = row[source]
    for source, target in {"Temática": "tematica", "Universo": "universo",
                           "Alias": "alias"}.items():
        if row.get(source):
            manga[target] = [
                value.strip() for value in row[source].split("|")
                if value.strip()
            ]


def _load_metadata(path):
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}

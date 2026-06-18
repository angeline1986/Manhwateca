import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from notion_client import Client

from manhwateca.notion_sync import csv_properties, matching, pages
from manhwateca.notion_sync.metadata_service import (
    update_from_csv as update_metadata,
)
from manhwateca.notion_sync.repositories import (
    load_mangas,
    load_csv_rows,
    load_metadata as read_metadata,
)
from manhwateca.notion_sync.csv_status import write_csv_status
from manhwateca.notion_sync.sync_state import (
    build_state_records,
    write_sync_state,
)


load_dotenv()

CSV_FILE = Path("reports/integrations/manhwateca_import.csv")
CATALOG_FILE = Path("data/mangas.json")
METADATA_FILE = Path("config/catalog_metadata.json")
STATUS_FILE = Path("reports/integrations/notion_csv_status.json")
SYNC_STATE_FILE = Path("reports/integrations/sync_state.json")
MULTI_VALUE_SEPARATOR = "|"

normalize_title = matching.normalize_title
split_values = csv_properties.split_values
optional_number = csv_properties.optional_number
build_properties = csv_properties.build_properties
build_metadata_properties = csv_properties.build_metadata_properties
build_progress_properties = csv_properties.build_progress_properties
load_existing_pages = pages.load_existing_pages


def load_rows(path=CSV_FILE):
    return load_csv_rows(path)


def load_metadata(path=METADATA_FILE):
    return read_metadata(path)


def equivalent_names(row, metadata):
    return matching.csv_equivalent_names(row, metadata, split_values)


def update_from_csv(
    notion,
    database_id,
    rows,
    apply=False,
    metadata=None,
    property_builder=None,
):
    if metadata is None:
        metadata = load_metadata()
    if property_builder is None:
        property_builder = build_metadata_properties
    return update_metadata(
        notion,
        database_id,
        rows,
        apply=apply,
        metadata=metadata,
        property_builder=property_builder,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Atualiza páginas existentes do Notion usando o CSV."
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--csv", type=Path, default=CSV_FILE)
    return parser.parse_args()


def main():
    args = parse_args()
    token = os.getenv("NOTION_TOKEN", "").strip()
    database_id = os.getenv("NOTION_DATABASE_ID", "").strip()
    if not token or not database_id:
        raise SystemExit("NOTION_TOKEN e NOTION_DATABASE_ID são obrigatórios.")
    rows = load_rows(args.csv)
    metadata = load_metadata()
    summary = update_from_csv(
        Client(auth=token),
        database_id,
        rows,
        apply=args.apply,
        metadata=metadata,
    )
    write_csv_status(summary, args.apply, STATUS_FILE)
    write_sync_state(
        build_state_records(
            summary,
            rows,
            catalog=_catalog_index(metadata),
            applied=args.apply,
        ),
        SYNC_STATE_FILE,
    )
    print()
    print(f"Modo: {'APLICAÇÃO' if args.apply else 'SIMULAÇÃO'}")
    print(f"Atualizações: {summary['updated']}")
    print(f"Sem alteração: {len(summary.get('unchanged', []))}")
    print(f"Ausentes no Notion: {len(summary['missing'])}")
    print(f"Duplicados bloqueados: {len(summary['duplicates'])}")
    print(f"Log da atualização: {STATUS_FILE}")
    print(f"Estado de sincronização: {SYNC_STATE_FILE}")
    if summary["duplicates"]:
        raise SystemExit("Existem títulos duplicados no Notion.")


def _catalog_index(metadata):
    if not CATALOG_FILE.exists():
        return {}
    index = {}
    for manga in load_mangas(CATALOG_FILE):
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

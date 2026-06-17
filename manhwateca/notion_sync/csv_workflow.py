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
    load_csv_rows,
    load_metadata as read_metadata,
)
from manhwateca.notion_sync.csv_status import write_csv_status


load_dotenv()

CSV_FILE = Path("reports/integrations/manhwateca_import.csv")
METADATA_FILE = Path("config/catalog_metadata.json")
STATUS_FILE = Path("reports/integrations/notion_csv_status.json")
MULTI_VALUE_SEPARATOR = "|"

normalize_title = matching.normalize_title
split_values = csv_properties.split_values
optional_number = csv_properties.optional_number
build_properties = csv_properties.build_properties
load_existing_pages = pages.load_existing_pages


def load_rows(path=CSV_FILE):
    return load_csv_rows(path)


def load_metadata(path=METADATA_FILE):
    return read_metadata(path)


def equivalent_names(row, metadata):
    return matching.csv_equivalent_names(row, metadata, split_values)


def update_from_csv(notion, database_id, rows, apply=False, metadata=None):
    if metadata is None:
        metadata = load_metadata()
    return update_metadata(
        notion, database_id, rows, apply=apply, metadata=metadata
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
    summary = update_from_csv(
        Client(auth=token),
        database_id,
        load_rows(args.csv),
        apply=args.apply,
    )
    write_csv_status(summary, args.apply, STATUS_FILE)
    print()
    print(f"Modo: {'APLICAÇÃO' if args.apply else 'SIMULAÇÃO'}")
    print(f"Atualizações: {summary['updated']}")
    print(f"Sem alteração: {len(summary.get('unchanged', []))}")
    print(f"Ausentes no Notion: {len(summary['missing'])}")
    print(f"Duplicados bloqueados: {len(summary['duplicates'])}")
    print(f"Log da atualização: {STATUS_FILE}")
    if summary["duplicates"]:
        raise SystemExit("Existem títulos duplicados no Notion.")

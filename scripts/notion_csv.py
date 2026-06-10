import argparse
import csv
import os
import re
import unicodedata
from pathlib import Path

from dotenv import load_dotenv
from notion_client import Client


load_dotenv()

CSV_FILE = Path("reports/integrations/manhwateca_import.csv")
MULTI_VALUE_SEPARATOR = "|"


def normalize_title(value):
    value = unicodedata.normalize("NFD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.casefold().replace("_", " ")
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


def split_values(value):
    return [
        item.strip()
        for item in (value or "").split(MULTI_VALUE_SEPARATOR)
        if item.strip()
    ]


def optional_number(value):
    value = (value or "").strip()
    if not value:
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def build_properties(row):
    properties = {
        "Alias": {
            "rich_text": [{
                "text": {"content": ", ".join(split_values(row.get("Alias")))}
            }]
        },
        "Último capítulo disponível": {
            "number": optional_number(row.get("Último capítulo disponível"))
        },
        "Capítulos encontrados": {
            "number": optional_number(row.get("Capítulos encontrados"))
        },
        "Side stories": {
            "number": optional_number(row.get("Side stories"))
        },
        "Lacunas": {
            "rich_text": [{
                "text": {"content": row.get("Lacunas", "-") or "-"}
            }]
        },
        "Status da contagem": {
            "select": (
                {"name": row["Status da contagem"]}
                if row.get("Status da contagem")
                else None
            )
        },
        "Capítulo MangaUpdates": {
            "number": optional_number(row.get("Capítulo MangaUpdates"))
        },
        "MangaUpdates": {"url": row.get("MangaUpdates") or None},
        "ID da obra": {
            "number": optional_number(row.get("ID da obra"))
        },
    }
    if row.get("Temática"):
        properties["Temática"] = {
            "multi_select": [
                {"name": value} for value in split_values(row["Temática"])
            ]
        }
    if row.get("Formato"):
        properties["Formato"] = {"select": {"name": row["Formato"]}}
    if row.get("Universo"):
        properties["Universo"] = {
            "multi_select": [
                {"name": value} for value in split_values(row["Universo"])
            ]
        }
    if row.get("Picância"):
        properties["Picância"] = {"select": {"name": row["Picância"]}}
    if row.get("Interesse"):
        properties["Interesse"] = {"select": {"name": row["Interesse"]}}
    return properties


def load_rows(path=CSV_FILE):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_existing_pages(notion, database_id):
    pages = {}
    cursor = None
    while True:
        request = {"database_id": database_id, "page_size": 100}
        if cursor:
            request["start_cursor"] = cursor
        response = notion.databases.query(**request)
        for page in response.get("results", []):
            title = "".join(
                item.get("plain_text", "")
                for item in page["properties"]["Nome"]["title"]
            ).strip()
            if title:
                pages.setdefault(normalize_title(title), []).append(page)
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return pages


def update_from_csv(notion, database_id, rows, apply=False):
    existing = load_existing_pages(notion, database_id)
    summary = {"updated": 0, "missing": [], "duplicates": []}
    for row in rows:
        name = row.get("Nome", "").strip()
        candidates = {normalize_title(name)}
        candidates.update(
            normalize_title(alias)
            for alias in split_values(row.get("Alias"))
        )
        matches_by_id = {}
        for candidate in candidates:
            for page in existing.get(candidate, []):
                matches_by_id[page["id"]] = page
        matches = list(matches_by_id.values())
        if not matches:
            summary["missing"].append(name)
            print(f"[AUSENTE NO NOTION] {name}")
            continue
        if len(matches) > 1:
            summary["duplicates"].append(name)
            print(f"[DUPLICADO NO NOTION] {name}")
            continue
        summary["updated"] += 1
        print(f"[ATUALIZAR] {name}")
        if apply:
            notion.pages.update(
                page_id=matches[0]["id"],
                properties=build_properties(row),
            )
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Atualiza páginas existentes do Notion usando o CSV."
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--csv", type=Path, default=CSV_FILE)
    args = parser.parse_args()

    token = os.getenv("NOTION_TOKEN", "").strip()
    database_id = os.getenv("NOTION_DATABASE_ID", "").strip()
    if not token or not database_id:
        raise SystemExit("NOTION_TOKEN e NOTION_DATABASE_ID são obrigatórios.")

    rows = load_rows(args.csv)
    notion = Client(auth=token)
    summary = update_from_csv(
        notion,
        database_id,
        rows,
        apply=args.apply,
    )
    print()
    print(f"Modo: {'APLICAÇÃO' if args.apply else 'SIMULAÇÃO'}")
    print(f"Atualizações: {summary['updated']}")
    print(f"Ausentes no Notion: {len(summary['missing'])}")
    print(f"Duplicados bloqueados: {len(summary['duplicates'])}")
    if summary["duplicates"]:
        raise SystemExit("Existem títulos duplicados no Notion.")


if __name__ == "__main__":
    main()

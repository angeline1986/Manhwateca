import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from notion_client import Client


load_dotenv()

DATA_FILE = Path("data/mangas.json")
TITLE_PROPERTY = "Nome"


def require_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} não foi definido no .env")
    return value


def load_mangas(path=DATA_FILE):
    if not path.exists():
        raise FileNotFoundError(
            f"Catálogo não encontrado: {path}. Execute scripts/scan.py primeiro."
        )

    with path.open("r", encoding="utf-8") as file:
        mangas = json.load(file)

    if not isinstance(mangas, list):
        raise ValueError(f"Formato inválido em {path}: era esperada uma lista.")

    return mangas


def build_properties(manga):
    return {
        "Nome": {"title": [{"text": {"content": manga["nome"]}}]},
        "Alias": {
            "rich_text": [
                {"text": {"content": ", ".join(manga.get("alias", []))}}
            ],
        },
        "Status": {"select": {"name": manga["status"]}},
        "Nota": {"select": {"name": manga["nota"]}},
        "Último lido": {"number": manga["ultimo_lido"]},
        "Total caps": {"number": manga["total_caps"]},
        "Path": {"url": Path(manga["path"]).expanduser().resolve().as_uri()},
    }


def extract_title(page):
    title_items = page.get("properties", {}).get(TITLE_PROPERTY, {}).get("title", [])
    return "".join(item.get("plain_text", "") for item in title_items).strip()


def load_existing_pages(notion, database_id):
    pages_by_name = {}
    cursor = None

    while True:
        request = {"database_id": database_id, "page_size": 100}
        if cursor:
            request["start_cursor"] = cursor

        response = notion.databases.query(**request)

        for page in response.get("results", []):
            name = extract_title(page)
            if name:
                pages_by_name.setdefault(name.casefold(), []).append(page)

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return pages_by_name


def sync(notion, database_id, mangas, apply=False):
    existing = load_existing_pages(notion, database_id)
    summary = {"created": 0, "updated": 0, "duplicates": 0}

    for manga in mangas:
        name = manga["nome"].strip()
        matches = existing.get(name.casefold(), [])
        properties = build_properties(manga)

        if len(matches) > 1:
            summary["duplicates"] += 1
            print(f"[DUPLICADO] {name}: {len(matches)} páginas no Notion")
            continue

        if matches:
            summary["updated"] += 1
            print(f"[ATUALIZAR] {name}")
            if apply:
                notion.pages.update(
                    page_id=matches[0]["id"],
                    properties=properties,
                )
        else:
            summary["created"] += 1
            print(f"[CRIAR] {name}")
            if apply:
                notion.pages.create(
                    parent={"database_id": database_id},
                    properties=properties,
                )

    return summary


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sincroniza data/mangas.json com o banco do Notion."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica as criações e atualizações. Sem esta opção, apenas simula.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    token = require_env("NOTION_TOKEN")
    database_id = require_env("NOTION_DATABASE_ID")
    mangas = load_mangas()
    notion = Client(auth=token)
    summary = sync(notion, database_id, mangas, apply=args.apply)

    print()
    print(f"Modo: {'APLICAÇÃO' if args.apply else 'SIMULAÇÃO'}")
    print(f"Criações: {summary['created']}")
    print(f"Atualizações: {summary['updated']}")
    print(f"Duplicados bloqueados: {summary['duplicates']}")

    if summary["duplicates"]:
        raise SystemExit(
            "Existem nomes duplicados no Notion. Corrija-os antes de sincronizar."
        )


if __name__ == "__main__":
    main()

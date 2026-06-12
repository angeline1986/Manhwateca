import argparse
import json
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from notion_client import Client
from utils import load_title_aliases


load_dotenv()

DATA_FILE = Path("data/mangas.json")
STATUS_FILE = Path("reports/integrations/notion_import_status.json")
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
    properties = {
        "Nome": {"title": [{"text": {"content": manga["nome"]}}]},
        "Status": {"select": {"name": manga["status"]}},
        "Nota": {"select": {"name": manga["nota"]}},
        "Último cap disponível": {"number": manga.get("main_caps", 0)},
        "Tamanho": {"select": {"name": manga["tamanho"]}},
        "Caps encontrados": {"number": manga.get("chapters_found", 0)},
        "Side stories": {"number": manga.get("side_stories_found", 0)},
        "Status da contagem": {
            "select": {"name": manga.get("count_status", "Revisar")}
        },
    }

    if manga.get("alias"):
        properties["Alias"] = {
            "rich_text": [
                {"text": {"content": ", ".join(manga["alias"])}}
            ],
        }

    if manga.get("ultimo_lido", 0) > 0:
        properties["Último lido"] = {"number": manga["ultimo_lido"]}

    if manga.get("mangaupdates_latest_chapter") is not None:
        properties["Cap MangaUpdates"] = {
            "number": manga["mangaupdates_latest_chapter"]
        }
    if manga.get("mangaupdates_url"):
        properties["MangaUpdates"] = {"url": manga["mangaupdates_url"]}

    if "tematica" in manga:
        properties["Temática"] = {
            "multi_select": [
                {"name": value}
                for value in manga.get("tematica", [])
            ],
        }
    if "formato" in manga:
        properties["Formato"] = {
            "select": (
                {"name": manga["formato"]}
                if manga.get("formato")
                else None
            ),
        }
    if "universo" in manga:
        properties["Universo"] = {
            "multi_select": [
                {"name": value}
                for value in manga.get("universo", [])
            ],
        }
    if "nivel_picancia" in manga:
        properties["Picância"] = {
            "select": (
                {"name": manga["nivel_picancia"]}
                if manga.get("nivel_picancia")
                else None
            ),
        }

    return properties


def extract_title(page):
    title_items = page.get("properties", {}).get(TITLE_PROPERTY, {}).get("title", [])
    return "".join(item.get("plain_text", "") for item in title_items).strip()


def normalize_title(value):
    value = unicodedata.normalize("NFD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.casefold().replace("_", " ")
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


def build_title_candidates(manga, title_aliases):
    name = manga["nome"].strip()
    candidates = {normalize_title(name)}

    for alias in manga.get("alias", []):
        if alias.strip():
            candidates.add(normalize_title(alias))

    normalized_name = normalize_title(name)
    for old_name, new_name in title_aliases.items():
        if normalize_title(new_name) == normalized_name:
            candidates.add(normalize_title(old_name))

    return candidates


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
                pages_by_name.setdefault(normalize_title(name), []).append(page)

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return pages_by_name


def write_import_status(summary, mode, applied=False, path=STATUS_FILE):
    created_titles = summary["created_titles"] if applied else []
    pending_titles = list(summary["pending_titles"])
    if not applied:
        pending_titles.extend(summary["created_titles"])
    pending_titles = sorted(set(pending_titles), key=normalize_title)
    imported = sorted(
        set(summary["matched_titles"] + created_titles),
        key=normalize_title,
    )
    payload = {
        "atualizado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "modo": mode,
        "resumo": {
            "total_catalogo": summary["catalog_total"],
            "total_importadas": len(imported),
            "importadas_neste_lote": len(created_titles),
            "total_pendentes": len(pending_titles),
            "total_duplicadas": len(summary["duplicate_titles"]),
        },
        "importadas_neste_lote": created_titles,
        "importadas": imported,
        "pendentes": pending_titles,
        "duplicadas": summary["duplicate_titles"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def sync(
    notion,
    database_id,
    mangas,
    apply=False,
    title_aliases=None,
    create_limit=None,
    update_existing=True,
    print_actions=True,
):
    existing = load_existing_pages(notion, database_id)
    title_aliases = title_aliases or {}
    existing_page_ids = {
        page["id"]
        for pages in existing.values()
        for page in pages
    }
    summary = {
        "catalog_total": len(mangas),
        "existing": len(existing_page_ids),
        "created": 0,
        "updated": 0,
        "pending": 0,
        "duplicates": 0,
        "matched_titles": [],
        "created_titles": [],
        "pending_titles": [],
        "duplicate_titles": [],
    }

    ordered_mangas = sorted(
        mangas,
        key=lambda manga: normalize_title(manga["nome"]),
    )
    for manga in ordered_mangas:
        name = manga["nome"].strip()
        matches_by_id = {}
        for candidate in build_title_candidates(manga, title_aliases):
            for page in existing.get(candidate, []):
                matches_by_id[page["id"]] = page
        matches = list(matches_by_id.values())
        properties = build_properties(manga)

        if len(matches) > 1:
            summary["duplicates"] += 1
            summary["duplicate_titles"].append(name)
            if print_actions:
                print(f"[DUPLICADO] {name}: {len(matches)} páginas no Notion")
            continue

        if matches:
            summary["matched_titles"].append(name)
            if update_existing:
                summary["updated"] += 1
                if print_actions:
                    print(f"[ATUALIZAR] {name}")
            if apply and update_existing:
                notion.pages.update(
                    page_id=matches[0]["id"],
                    properties=properties,
                )
        else:
            can_create = create_limit is None or summary["created"] < create_limit
            if can_create:
                summary["created"] += 1
                summary["created_titles"].append(name)
                if print_actions:
                    print(f"[CRIAR] {name}")
            else:
                summary["pending"] += 1
                summary["pending_titles"].append(name)

            if apply and can_create:
                notion.pages.create(
                    parent={"database_id": database_id},
                    properties=properties,
                )

    return summary


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sincroniza data/mangas.json com o banco do Notion."
    )
    apply_group = parser.add_mutually_exclusive_group()
    apply_group.add_argument(
        "--apply",
        action="store_true",
        help="Aplica as criações e atualizações. Sem esta opção, apenas simula.",
    )
    apply_group.add_argument(
        "--apply-batch",
        action="store_true",
        help="Atualiza páginas existentes e cria o próximo lote de obras ausentes.",
    )
    apply_group.add_argument(
        "--update-existing",
        action="store_true",
        help="Atualiza somente páginas já existentes, sem criar novas obras.",
    )
    parser.add_argument(
        "--simulate-batch",
        action="store_true",
        help="Simula somente o próximo lote de obras ausentes.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Quantidade de obras novas por lote (padrão: 25).",
    )
    parser.add_argument(
        "--allow-mass-create",
        action="store_true",
        help="Permite aplicar quando mais de 25%% do catálogo seria criado.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.batch_size < 1:
        raise SystemExit("--batch-size deve ser maior que zero.")

    token = require_env("NOTION_TOKEN")
    database_id = require_env("NOTION_DATABASE_ID")
    mangas = load_mangas()
    notion = Client(auth=token)
    title_aliases = load_title_aliases()
    full_summary = sync(
        notion,
        database_id,
        mangas,
        apply=False,
        title_aliases=title_aliases,
        print_actions=False,
    )

    creation_ratio = full_summary["created"] / len(mangas) if mangas else 0
    applying = args.apply or args.apply_batch or args.update_existing
    if applying and full_summary["duplicates"]:
        raise SystemExit(
            "Aplicação bloqueada: existem nomes duplicados no Notion. "
            "Corrija-os antes de sincronizar."
        )

    if args.apply and creation_ratio > 0.25 and not args.allow_mass_create:
        raise SystemExit(
            f"Aplicação bloqueada: {full_summary['created']} de {len(mangas)} obras "
            f"({creation_ratio:.0%}) seriam criadas. "
            "Revise a simulação e use --allow-mass-create somente se isso "
            "for realmente esperado."
        )

    if args.apply_batch:
        summary = sync(
            notion,
            database_id,
            mangas,
            apply=True,
            title_aliases=title_aliases,
            create_limit=args.batch_size,
            update_existing=False,
        )
    elif args.apply:
        summary = sync(
            notion,
            database_id,
            mangas,
            apply=True,
            title_aliases=title_aliases,
        )
    elif args.update_existing:
        summary = sync(
            notion,
            database_id,
            mangas,
            apply=True,
            title_aliases=title_aliases,
            create_limit=0,
            update_existing=True,
        )
    elif args.simulate_batch:
        summary = sync(
            notion,
            database_id,
            mangas,
            apply=False,
            title_aliases=title_aliases,
            create_limit=args.batch_size,
            update_existing=False,
        )
    else:
        summary = sync(
            notion,
            database_id,
            mangas,
            apply=False,
            title_aliases=title_aliases,
        )

    print()
    if args.apply_batch:
        mode = f"APLICAÇÃO EM LOTE ({args.batch_size})"
    elif args.simulate_batch:
        mode = f"SIMULAÇÃO DO PRÓXIMO LOTE ({args.batch_size})"
    elif args.apply:
        mode = "APLICAÇÃO"
    elif args.update_existing:
        mode = "ATUALIZAÇÃO DAS PÁGINAS EXISTENTES"
    else:
        mode = "SIMULAÇÃO"
    write_import_status(summary, mode, applied=applying)
    print(f"Modo: {mode}")
    print(f"Páginas encontradas no Notion: {summary['existing']}")
    print(f"Criações: {summary['created']}")
    print(f"Atualizações: {summary['updated']}")
    if args.apply_batch or args.simulate_batch or args.update_existing:
        print(f"Obras restantes para próximos lotes: {summary['pending']}")
    else:
        print(f"Percentual de criação: {creation_ratio:.0%}")
    print(f"Duplicados bloqueados: {summary['duplicates']}")
    print(f"Log de importação: {STATUS_FILE}")

    if summary["duplicates"]:
        raise SystemExit(
            "Existem nomes duplicados no Notion. Corrija-os antes de sincronizar."
        )


if __name__ == "__main__":
    main()

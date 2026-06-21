import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from notion_client import Client

from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
)
from manhwateca.database.manga_repository import MangaRepository
from manhwateca.notion_sync import catalog_properties, matching, pages
from manhwateca.notion_sync.catalog_service import sync
from manhwateca.notion_sync.repositories import (
    load_mangas as read_mangas,
    load_mangas_from_database as read_mangas_from_database,
)
from manhwateca.notion_sync.status_repository import (
    write_import_status as save_import_status,
)
from manhwateca.shared.titles import load_title_aliases


load_dotenv()

DATA_FILE = Path("data/mangas.json")
STATUS_FILE = Path("reports/integrations/notion_import_status.json")
TITLE_PROPERTY = "Nome"

normalize_title = matching.normalize_title
build_properties = catalog_properties.build_properties
build_progress_properties = catalog_properties.build_progress_properties
extract_title = pages.extract_title
load_existing_pages = pages.load_existing_pages


def require_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} não foi definido no .env")
    return value


def load_mangas(path=DATA_FILE):
    return read_mangas(path)


def load_mangas_from_database(repository=None):
    return read_mangas_from_database(repository)


def build_title_candidates(manga, title_aliases):
    return matching.catalog_title_candidates(manga, title_aliases)


def write_import_status(summary, mode, applied=False, path=STATUS_FILE):
    return save_import_status(summary, mode, applied=applied, path=path)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Sincroniza o catálogo com o banco do Notion. Por padrão tenta "
            "PostgreSQL e usa data/mangas.json somente como fallback legado."
        )
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--apply",
        action="store_true",
        help="Aplica as criações e atualizações. Sem esta opção, apenas simula.",
    )
    group.add_argument(
        "--apply-batch",
        action="store_true",
        help="Atualiza páginas existentes e cria o próximo lote de obras ausentes.",
    )
    group.add_argument(
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
    parser.add_argument(
        "--catalog-source",
        choices=("auto", "json", "postgresql"),
        default=os.getenv("MANHWATECA_CATALOG_SOURCE", "auto"),
        help=(
            "Fonte do catálogo para o sync. auto tenta PostgreSQL e cai para "
            "JSON legado quando o banco não está disponível; postgresql força "
            "vw_mangas; json força o fluxo legado."
        ),
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()
    if args.batch_size < 1:
        raise SystemExit("--batch-size deve ser maior que zero.")
    database_id = require_env("NOTION_DATABASE_ID")
    repository = _repository_for(args.catalog_source)
    mangas = _load_catalog(args.catalog_source, repository)
    notion = Client(auth=require_env("NOTION_TOKEN"))
    aliases = load_title_aliases()
    full = sync(
        notion, database_id, mangas, title_aliases=aliases, print_actions=False
    )
    ratio = full["created"] / len(mangas) if mangas else 0
    applying = args.apply or args.apply_batch or args.update_existing
    _validate_application(args, full, mangas, ratio, applying)
    summary = _run_selected_mode(
        args,
        notion,
        database_id,
        mangas,
        aliases,
        result_repository=repository if applying else None,
    )
    mode = _mode_label(args)
    write_import_status(summary, mode, applied=applying)
    _print_summary(args, summary, mode, ratio)
    if summary["duplicates"]:
        raise SystemExit(
            "Existem nomes duplicados no Notion. Corrija-os antes de sincronizar."
        )


def _validate_application(args, summary, mangas, ratio, applying):
    if applying and summary["duplicates"]:
        raise SystemExit(
            "Aplicação bloqueada: existem nomes duplicados no Notion. "
            "Corrija-os antes de sincronizar."
        )
    if args.apply and ratio > 0.25 and not args.allow_mass_create:
        raise SystemExit(
            f"Aplicação bloqueada: {summary['created']} de {len(mangas)} obras "
            f"({ratio:.0%}) seriam criadas. Revise a simulação e use "
            "--allow-mass-create somente se isso for realmente esperado."
        )


def _repository_for(source):
    if source in {"auto", "postgresql"}:
        return MangaRepository()
    return None


def _load_catalog(source, repository=None):
    if source == "postgresql":
        return load_mangas_from_database(repository)
    if source == "auto":
        try:
            return load_mangas_from_database(repository)
        except (DatabaseConfigurationError, DatabaseConnectionError) as error:
            print(
                "PostgreSQL indisponível para o sync; usando "
                f"{DATA_FILE} como fallback legado. Motivo: {error}"
            )
    return load_mangas(DATA_FILE)


def _run_selected_mode(
    args,
    notion,
    database_id,
    mangas,
    aliases,
    result_repository=None,
):
    options = {"title_aliases": aliases}
    if args.apply_batch:
        options.update(apply=True, create_limit=args.batch_size, update_existing=False)
    elif args.apply:
        options["apply"] = True
    elif args.update_existing:
        options.update(
            apply=True,
            create_limit=0,
            update_existing=True,
            property_builder=build_progress_properties,
        )
    elif args.simulate_batch:
        options.update(create_limit=args.batch_size, update_existing=False)
    if result_repository is not None:
        options["result_repository"] = result_repository
    return sync(notion, database_id, mangas, **options)


def _mode_label(args):
    if args.apply_batch:
        return f"APLICAÇÃO EM LOTE ({args.batch_size})"
    if args.simulate_batch:
        return f"SIMULAÇÃO DO PRÓXIMO LOTE ({args.batch_size})"
    if args.apply:
        return "APLICAÇÃO"
    if args.update_existing:
        return "ATUALIZAÇÃO DAS PÁGINAS EXISTENTES"
    return "SIMULAÇÃO"


def _print_summary(args, summary, mode, ratio):
    print()
    print(f"Modo: {mode}")
    print(f"Páginas encontradas no Notion: {summary['existing']}")
    print(f"Criações: {summary['created']}")
    print(f"Atualizações: {summary['updated']}")
    if args.apply_batch or args.simulate_batch or args.update_existing:
        print(f"Obras restantes para próximos lotes: {summary['pending']}")
    else:
        print(f"Percentual de criação: {ratio:.0%}")
    print(f"Duplicados bloqueados: {summary['duplicates']}")
    print(f"Log de importação: {STATUS_FILE}")

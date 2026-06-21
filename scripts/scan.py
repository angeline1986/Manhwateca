import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from manhwateca.catalog.discovery import (
    GROUP_FOLDERS,
    IGNORED_FOLDERS,
    find_manga_folders,
    is_group_folder,
    is_ignored_folder,
    is_manga_folder,
)
from manhwateca.catalog.external_data import (
    MANGAUPDATES_CACHE,
    load_mangaupdates_cache,
)
from manhwateca.catalog.repository import OUTPUT_FILE, save_mangas
from manhwateca.catalog.scanner import scan_mangas, save_mangas_to_database
from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
)
from manhwateca.shared.paths import get_required_path_env


load_dotenv()


def main() -> None:
    manga_root = get_required_path_env("MANGA_ROOT")
    mangas = scan_mangas(manga_root=manga_root)
    save_mangas(mangas)
    database_message = _save_database_if_available(mangas)

    total_main_caps = sum(manga["main_caps"] for manga in mangas)
    total_side_caps = sum(manga["side_caps"] for manga in mangas)
    total_chapter_files = sum(manga["chapter_files"] for manga in mangas)

    print(f"Pasta raiz: {manga_root}")
    print()
    print(f"Total de obras encontradas: {len(mangas)}")
    print(f"Total de capítulos principais: {total_main_caps}")
    print(f"Total de side stories: {total_side_caps}")
    print(f"Total de arquivos de capítulo: {total_chapter_files}")
    print()
    print(f"Arquivo gerado: {OUTPUT_FILE}")
    print(database_message)


def _save_database_if_available(mangas):
    try:
        saved = save_mangas_to_database(mangas)
    except DatabaseConfigurationError:
        return "PostgreSQL: não configurado (JSON legado mantido)."
    except DatabaseConnectionError as error:
        return f"PostgreSQL: não atualizado ({error})."
    return f"PostgreSQL: {saved} obra(s) atualizada(s)."


if __name__ == "__main__":
    main()

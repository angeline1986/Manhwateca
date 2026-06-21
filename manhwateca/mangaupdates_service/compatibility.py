import time
import urllib.error
from pathlib import Path


from manhwateca.mangaupdates_service.client import (
    API_BASE,
    get_series,
    request_json,
    search_series,
)
from manhwateca.mangaupdates_service.csv_export import (
    CSV_COLUMNS,
    build_csv_row,
    join_values,
    write_csv as _write_csv,
)
from manhwateca.mangaupdates_service.csv_update import (
    update_csv_from_confirmed_ids as _update_csv,
)
from manhwateca.mangaupdates_service.candidates import (
    add_catalog_titles_to_id_searches as _add_catalog_titles,
    load_catalog as _load_catalog,
    load_id_searches,
    matches_initial_filter,
    normalize_initial_filter,
    search_candidates_for_item as _search_candidates,
    search_terms_for_item,
)
from manhwateca.mangaupdates_service.cache import (
    enrich_catalog as _enrich_catalog,
    fetch_confirmed_details as _fetch_confirmed_details,
    refresh_cache as _refresh_cache,
)
from manhwateca.mangaupdates_service.candidate_workflows import (
    fill_ids_file as _fill_ids_file,
    refresh_incomplete_candidates as _refresh_candidates,
)
from manhwateca.mangaupdates_service.details import infer_format, summarize_series
from manhwateca.mangaupdates_service.matching import (
    BL_GENRES,
    SUPPORTED_TYPES,
    choose_search_result,
    filter_relevant_candidates,
    normalize_title,
    rank_search_results,
    select_ranked_candidate,
    title_similarity,
    title_tokens,
    truncate_text,
)
from manhwateca.mangaupdates_service.cli import run_cli
from manhwateca.mangaupdates_service.parser import build_parser
from manhwateca.mangaupdates_service.repository import (
    load_json_object,
    save_json,
)


MAPPINGS_FILE = Path("config/mangaupdates.json")
CACHE_FILE = Path("data/mangaupdates.json")
CATALOG_FILE = Path("data/mangas.json")
CSV_FILE = Path("reports/integrations/manhwateca_import.csv")
STATE_FILE = Path("reports/integrations/mangaupdates_state.json")
PROGRESS_FILE = Path("data/mangaupdates_progress.json")
METADATA_FILE = Path("config/catalog_metadata.json")
def add_catalog_titles_to_id_searches(items, catalog_path=CATALOG_FILE):
    return _add_catalog_titles(items, catalog_path)


def load_catalog(path=CATALOG_FILE):
    return _load_catalog(path)


def search_candidates_for_item(item, metadata, per_page=10):
    return _search_candidates(
        item,
        metadata,
        search_function=search_series,
        per_page=per_page,
    )


def fill_ids_file(
    path,
    delay=3.0,
    limit=None,
    per_page=10,
    retry_review=False,
    catalog_path=CATALOG_FILE,
    initials="",
):
    metadata = load_json_object(METADATA_FILE)
    return _fill_ids_file(
        path,
        metadata=metadata,
        search_candidates=search_candidates_for_item,
        save_function=save_json,
        wait_function=wait_between_requests,
        delay=delay,
        limit=limit,
        per_page=per_page,
        retry_review=retry_review,
        catalog_path=catalog_path,
        initials=initials,
    )


def refresh_incomplete_candidates(
    path,
    delay=3.0,
    limit=10,
    per_page=10,
):
    metadata = load_json_object(METADATA_FILE)
    return _refresh_candidates(
        path,
        metadata=metadata,
        search_candidates=search_candidates_for_item,
        save_function=save_json,
        wait_function=wait_between_requests,
        delay=delay,
        limit=limit,
        per_page=per_page,
    )


def wait_between_requests(delay):
    if delay > 0:
        time.sleep(delay)


def enrich_catalog(
    mangas,
    delay=3.0,
    limit=None,
    progress_path=PROGRESS_FILE,
    cache_path=CACHE_FILE,
):
    return _enrich_catalog(
        mangas,
        search_function=search_series,
        detail_function=get_series,
        choose_function=choose_search_result,
        summarize_function=summarize_series,
        wait_function=wait_between_requests,
        delay=delay,
        limit=limit,
        progress_path=progress_path,
        cache_path=cache_path,
    )


def write_csv(
    mangas,
    cache,
    progress,
    path=CSV_FILE,
    metadata_path=METADATA_FILE,
):
    return _write_csv(mangas, cache, progress, path, metadata_path)


def update_csv_from_confirmed_ids(
    ids_path,
    csv_path=CSV_FILE,
    delay=3.0,
    limit=None,
    cache_path=CACHE_FILE,
    catalog_path=CATALOG_FILE,
    database_repository=None,
):
    return _update_csv(
        ids_path,
        csv_path=csv_path,
        cache_path=cache_path,
        metadata_path=METADATA_FILE,
        catalog_path=catalog_path,
        limit=limit,
        database_repository=database_repository,
    )


def fetch_confirmed_details(
    ids_path,
    delay=3.0,
    limit=None,
    cache_path=CACHE_FILE,
    state_path=STATE_FILE,
    ttl_days=30,
    force_refresh=False,
):
    return _fetch_confirmed_details(
        ids_path,
        detail_function=get_series,
        summarize_function=summarize_series,
        wait_function=wait_between_requests,
        delay=delay,
        limit=limit,
        cache_path=cache_path,
        state_path=state_path,
        ttl_days=ttl_days,
        force_refresh=force_refresh,
    )


def refresh_cache(mappings_path=MAPPINGS_FILE, cache_path=CACHE_FILE):
    return _refresh_cache(
        mappings_path,
        cache_path,
        detail_function=get_series,
        summarize_function=summarize_series,
    )


def main():
    args = build_parser().parse_args()
    operations = {
        "search_series": search_series,
        "fill_ids": fill_ids_file,
        "refresh_candidates": refresh_incomplete_candidates,
        "update_csv": update_csv_from_confirmed_ids,
        "fetch_details": fetch_confirmed_details,
        "load_catalog": load_catalog,
        "enrich_catalog": enrich_catalog,
        "write_csv": write_csv,
        "refresh_cache": refresh_cache,
    }
    paths = {"cache": CACHE_FILE, "csv": CSV_FILE}
    try:
        run_cli(args, operations, paths)
    except urllib.error.URLError as error:
        raise SystemExit(f"Falha ao consultar MangaUpdates: {error}") from error

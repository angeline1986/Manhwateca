import time
import urllib.error
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*_args, **_kwargs):
        return False


from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
)
from manhwateca.database.manga_repository import MangaRepository
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


@dataclass(frozen=True)
class ConfirmedDetailsResult:
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    selected_work_ids: tuple[int, ...] = ()
    attempted_work_ids: tuple[int, ...] = ()
    processed_work_ids: tuple[int, ...] = ()
    failed_work_ids: tuple[int, ...] = ()
    skipped_work_ids: tuple[int, ...] = ()

    def legacy_counts(self):
        return self.updated, self.skipped

    def metrics(self):
        return {
            "selected_work_ids": list(self.selected_work_ids),
            "attempted_work_ids": list(self.attempted_work_ids),
            "processed_work_ids": list(self.processed_work_ids),
            "failed_work_ids": list(self.failed_work_ids),
            "skipped_work_ids": list(self.skipped_work_ids),
        }
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
        decision_repository=_optional_decision_repository(),
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
        decision_repository=_optional_decision_repository(),
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
    selected_ids=None,
):
    result = fetch_confirmed_details_result(
        ids_path,
        delay=delay,
        limit=limit,
        cache_path=cache_path,
        state_path=state_path,
        ttl_days=ttl_days,
        force_refresh=force_refresh,
        selected_ids=selected_ids,
    )
    return result.legacy_counts()


def fetch_confirmed_details_result(
    ids_path,
    delay=3.0,
    limit=None,
    cache_path=CACHE_FILE,
    state_path=STATE_FILE,
    ttl_days=30,
    force_refresh=False,
    selected_ids=None,
):
    repository = _optional_decision_repository()
    if repository is not None:
        try:
            return _fetch_database_confirmed_details(
                repository,
                detail_function=get_series,
                summarize_function=summarize_series,
                wait_function=wait_between_requests,
                delay=delay,
                limit=limit,
                force_refresh=force_refresh,
                selected_ids=selected_ids,
            )
        except (DatabaseConfigurationError, DatabaseConnectionError):
            pass

    updated, skipped = _fetch_confirmed_details(
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
    return ConfirmedDetailsResult(updated=updated, skipped=skipped)


def _fetch_database_confirmed_details(
    repository,
    detail_function,
    summarize_function,
    wait_function,
    delay=3.0,
    limit=None,
    force_refresh=False,
    selected_ids=None,
):
    selected_ids = _normalize_selected_ids(selected_ids)
    selected_work_ids = _ordered_ids(selected_ids or ())
    confirmed = [
        manga for manga in repository.list_mangas()
        if getattr(manga, "work_code", None)
        and (
            selected_ids is None
            or int(getattr(manga, "id", 0) or 0) in selected_ids
        )
    ]
    confirmed_ids = _ordered_ids(
        int(getattr(manga, "id", 0) or 0)
        for manga in confirmed
    )
    skipped_ids = []
    if selected_ids is not None:
        confirmed_set = set(confirmed_ids)
        skipped_ids.extend(
            work_id for work_id in selected_work_ids
            if work_id not in confirmed_set
        )
    
    pending = []
    for manga in confirmed:
        # Verifica se falta URL ou Capa (trata None e String Vazia)
        m_url = getattr(manga, "mangaupdates_url", None)
        m_cover = getattr(manga, "cover_url", None)
        
        needs_update = (
            force_refresh or 
            not m_url or str(m_url).strip() == "" or
            not m_cover or str(m_cover).strip() == ""
        )
        
        if needs_update:
            pending.append(manga)

    selected = pending[:limit] if limit is not None else pending
    attempted_ids = _ordered_ids(
        int(getattr(manga, "id", 0) or 0)
        for manga in selected
    )

    success_count = 0
    failed_ids = []
    for manga in selected:
        series_id = manga.work_code
        manga_id = int(getattr(manga, "id", 0) or 0)
        try:
            print(f"[SINCronizando] {manga.title} (ID: {series_id})...")
            # Busca na API
            raw_data = detail_function(series_id)
            if not raw_data:
                print(f"[ERRO] API não retornou dados para {series_id}")
                continue
                
            summary = summarize_function(raw_data)
            
            # Grava no Banco
            updated = repository.update_mangaupdates_fields(
                manga.title,
                series_id,
                summary,
            )
            if updated:
                success_count += 1
                print(f"[OK] {manga.title} atualizado.")
            else:
                print(f"[AVISO] Repositório não encontrou registro para {manga.title}")
                failed_ids.append(manga_id)
                
        except Exception as e:
            print(f"[ERRO] Falha ao processar {manga.title}: {e}")
            failed_ids.append(manga_id)
            
        wait_function(delay)

    failed_ids = _ordered_ids(failed_ids)
    failed_set = set(failed_ids)
    processed_ids = _ordered_ids(
        work_id for work_id in confirmed_ids
        if work_id not in failed_set
    )
    return ConfirmedDetailsResult(
        updated=success_count,
        skipped=(len(pending) - success_count) + len(skipped_ids),
        failed=len(failed_ids),
        selected_work_ids=tuple(selected_work_ids),
        attempted_work_ids=tuple(attempted_ids),
        processed_work_ids=tuple(processed_ids),
        failed_work_ids=tuple(failed_ids),
        skipped_work_ids=tuple(_ordered_ids(skipped_ids)),
    )


def refresh_cache(mappings_path=MAPPINGS_FILE, cache_path=CACHE_FILE):
    return _refresh_cache(
        mappings_path,
        cache_path,
        detail_function=get_series,
        summarize_function=summarize_series,
    )


def _optional_decision_repository():
    try:
        return MangaRepository()
    except (DatabaseConfigurationError, DatabaseConnectionError):
        return None


def _normalize_selected_ids(selected_ids):
    if not selected_ids:
        return None
    normalized = set()
    for value in selected_ids:
        try:
            normalized.add(int(value))
        except (TypeError, ValueError):
            continue
    return normalized or None


def _ordered_ids(values):
    ordered = []
    seen = set()
    for value in values:
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number <= 0 or number in seen:
            continue
        ordered.append(number)
        seen.add(number)
    return ordered


def main():
    load_dotenv()
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

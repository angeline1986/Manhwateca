from manhwateca.mangaupdates_service.candidates import (
    CONFIRMED_STATUSES,
    load_id_searches,
)
from manhwateca.mangaupdates_service.repository import (
    load_json_object,
    save_json,
)
from manhwateca.mangaupdates_service.state import (
    load_mangaupdates_state,
    mark_series_checked,
    save_mangaupdates_state,
    should_fetch_series,
)


def enrich_catalog(
    mangas,
    search_function,
    detail_function,
    choose_function,
    summarize_function,
    wait_function,
    delay=3.0,
    limit=None,
    progress_path=None,
    cache_path=None,
):
    progress = load_json_object(progress_path)
    cache = load_json_object(cache_path)
    processed = 0

    for manga in mangas:
        title = manga["nome"]
        if title in progress:
            continue
        if limit is not None and processed >= limit:
            break
        if title in cache:
            progress[title] = {
                "match_status": "Cache confirmado",
                **cache[title],
            }
            save_json(progress_path, progress)
            processed += 1
            continue

        print(f"[BUSCAR] {title}")
        search = search_function(title)
        record, match_status = choose_function(title, search)
        entry = {"match_status": match_status}
        wait_function(delay)

        if record:
            series_id = record["series_id"]
            print(f"[DETALHAR] {title} ({series_id})")
            summary = summarize_function(detail_function(series_id))
            cache[title] = summary
            entry.update(summary)
            wait_function(delay)

        progress[title] = entry
        save_json(progress_path, progress)
        save_json(cache_path, cache)
        processed += 1

    return progress, cache


def fetch_confirmed_details(
    ids_path,
    detail_function,
    summarize_function,
    wait_function,
    delay=3.0,
    limit=None,
    cache_path=None,
    state_path=None,
    ttl_days=30,
    force_refresh=False,
):
    items = load_id_searches(ids_path)
    confirmed = [
        item
        for item in items
        if item.get("Status") in CONFIRMED_STATUSES and item.get("ID")
    ]
    cache = load_json_object(cache_path)
    state = load_mangaupdates_state(state_path) if state_path else {}
    pending = [
        item for item in confirmed
        if force_refresh
        or should_fetch_series(item["ID"], cache, state, ttl_days=ttl_days)
    ]
    selected = pending[:limit] if limit is not None else pending

    for item in selected:
        series_id = item["ID"]
        print(f"[DETALHAR] {item['Nome']} ({series_id})")
        cache[str(series_id)] = summarize_function(
            detail_function(series_id)
        )
        save_json(cache_path, cache)
        if state_path:
            mark_series_checked(state, series_id)
            save_mangaupdates_state(state_path, state)
        wait_function(delay)

    return len(selected), len(pending) - len(selected)


def refresh_cache(
    mappings_path,
    cache_path,
    detail_function,
    summarize_function,
):
    mappings = load_json_object(mappings_path)
    cache = load_json_object(cache_path)
    for title, series_id in mappings.items():
        print(f"[CONSULTAR] {title} ({series_id})")
        cache[title] = summarize_function(detail_function(series_id))
    save_json(cache_path, cache)
    return cache

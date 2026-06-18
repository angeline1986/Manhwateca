from pathlib import Path

from manhwateca.mangaupdates_service.candidates import (
    CONFIRMED_STATUSES,
    load_id_searches,
)
from manhwateca.mangaupdates_service.repository import load_json_object
from manhwateca.mangaupdates_service.state import should_fetch_series


IDS_PATH = Path("reports/integrations/buscaIds.json")
CACHE_PATH = Path("data/mangaupdates.json")
STATE_PATH = Path("reports/integrations/mangaupdates_state.json")


def mangaupdates_status(project_root, *, ttl_days=30, batch_size=10):
    root = Path(project_root)
    items = _load_items(root / IDS_PATH)
    cache = _load_object(root / CACHE_PATH)
    state = _load_object(root / STATE_PATH)
    confirmed = [
        item for item in items
        if item.get("Status") in CONFIRMED_STATUSES and item.get("ID")
    ]
    calls = [
        _public_item(item)
        for item in confirmed
        if should_fetch_series(item["ID"], cache, state, ttl_days=ttl_days)
    ]
    forced_calls = [_public_item(item) for item in confirmed]
    return {
        "summary": {
            "confirmed_ids": len(confirmed),
            "cached_ids": sum(
                1 for item in confirmed if str(item["ID"]) in cache
            ),
            "calls_needed": len(calls),
            "next_batch": len(calls[:batch_size]),
            "force_refresh_calls": len(forced_calls),
            "force_refresh_batch": len(forced_calls[:batch_size]),
            "batch_size": batch_size,
            "ttl_days": ttl_days,
        },
        "next_batch": calls[:batch_size],
        "force_refresh_batch": forced_calls[:batch_size],
    }


def _load_items(path):
    if not path.is_file():
        return []
    try:
        return load_id_searches(path)
    except (OSError, ValueError):
        return []


def _load_object(path):
    if not path.is_file():
        return {}
    try:
        return load_json_object(path)
    except (OSError, ValueError):
        return {}


def _public_item(item):
    return {
        "name": item.get("Nome"),
        "id": item.get("ID"),
        "title": item.get("Nome encontrado") or item.get("Nome"),
    }

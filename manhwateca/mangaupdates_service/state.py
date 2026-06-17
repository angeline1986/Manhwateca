from datetime import datetime, timedelta, timezone

from manhwateca.mangaupdates_service.repository import load_json_object, save_json


DEFAULT_CACHE_TTL_DAYS = 30


def should_fetch_series(
    series_id,
    cache,
    state,
    *,
    now=None,
    ttl_days=DEFAULT_CACHE_TTL_DAYS,
):
    series_key = str(series_id)
    if series_key not in cache:
        return True

    entry = state.get("series", {}).get(series_key, {})
    if entry.get("force_refresh"):
        return True
    checked_at = _parse_datetime(entry.get("last_checked_at"))
    if checked_at is None:
        return False

    now = now or datetime.now(timezone.utc)
    return checked_at + timedelta(days=ttl_days) < now


def mark_series_checked(state, series_id, *, cache_hash=None, now=None):
    now = now or datetime.now(timezone.utc)
    state.setdefault("series", {})[str(series_id)] = {
        "last_checked_at": now.isoformat(),
        "cache_hash": cache_hash,
        "status": "cache_valido",
    }
    return state


def load_mangaupdates_state(path):
    return load_json_object(path)


def save_mangaupdates_state(path, state):
    save_json(path, state)


def _parse_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed

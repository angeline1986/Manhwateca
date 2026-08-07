from datetime import date, datetime

from manhwateca.release_monitor.models import ExternalRelease


def parse_external_releases_with_stats(payload):
    rows = _rows(payload)
    releases = []
    stats = {
        "releases_received": len(rows),
        "releases_parsed": 0,
        "releases_with_series_metadata": 0,
        "releases_missing_series_metadata": 0,
        "releases_invalid": 0,
    }
    for item in rows:
        if not isinstance(item, dict):
            stats["releases_invalid"] += 1
            continue
        release, reason = _parse_release_item(item)
        if release:
            releases.append(release)
            stats["releases_parsed"] += 1
            stats["releases_with_series_metadata"] += 1
        elif reason == "missing_series_metadata":
            stats["releases_missing_series_metadata"] += 1
        else:
            stats["releases_invalid"] += 1
    return releases, stats


def parse_external_releases(payload) -> list[ExternalRelease]:
    releases, _stats = parse_external_releases_with_stats(payload)
    return releases


def has_more_pages(payload, page: int) -> bool:
    if not isinstance(payload, dict):
        return False
    total_pages = payload.get("total_pages") or payload.get("totalPages")
    if total_pages is not None:
        try:
            return page < int(total_pages)
        except (TypeError, ValueError):
            return False
    if payload.get("has_more") is not None:
        return bool(payload.get("has_more"))
    if payload.get("next_page") or payload.get("nextPage"):
        return True
    total_hits = payload.get("total_hits") or payload.get("totalHits")
    per_page = payload.get("per_page") or payload.get("perPage")
    if total_hits is not None and per_page:
        try:
            return page * int(per_page) < int(total_hits)
        except (TypeError, ValueError):
            return False
    rows = _rows(payload)
    return bool(rows)


def _parse_release_item(item: dict):
    record = item.get("record") if isinstance(item.get("record"), dict) else item
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    series = metadata.get("series") if isinstance(metadata.get("series"), dict) else {}

    series_id = _series_id(record, series)
    chapter = _first_text(record, "chapter", "chapter_number", "chapterNumber", "chap")
    release_date = _date_value(
        record.get("release_date")
        or record.get("releaseDate")
        or record.get("date")
        or record.get("timestamp")
    )
    if series_id is None:
        return None, "missing_series_metadata"
    if not chapter or release_date is None:
        return None, "invalid"
    return ExternalRelease(
        series_id=series_id,
        chapter=chapter,
        release_date=release_date,
        volume=_first_text(record, "volume", "vol"),
        group_name=_group_name(record),
        external_release_id=_first_text(record, "id", "release_id", "releaseId"),
        source_url=_first_text(series, "url") or _first_text(record, "url", "source_url", "sourceUrl"),
        raw_payload=item,
    ), None


def _rows(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("results", "releases", "items", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _series_id(record, series=None):
    series = series or {}
    value = (
        series.get("series_id")
        or series.get("seriesId")
        or series.get("id")
        or record.get("series_id")
        or record.get("seriesId")
    )
    record_series = record.get("series")
    if value is None and isinstance(record_series, dict):
        value = record_series.get("id") or record_series.get("series_id")
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _group_name(row):
    value = _first_text(row, "group_name", "groupName", "release_group")
    group = row.get("group") or row.get("groups")
    if value:
        return value
    if isinstance(group, dict):
        return _first_text(group, "name", "title")
    if isinstance(group, list) and group:
        names = []
        for item in group:
            name = _first_text(item, "name", "title") if isinstance(item, dict) else str(item).strip()
            if name:
                names.append(name)
        return ", ".join(sorted(set(names), key=str.casefold)) if names else None
    return None


def _first_text(row, *keys):
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _date_value(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None

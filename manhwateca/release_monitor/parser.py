from datetime import date, datetime

from manhwateca.release_monitor.models import ExternalRelease


def parse_external_releases(payload) -> list[ExternalRelease]:
    rows = _rows(payload)
    releases = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if isinstance(row.get("record"), dict):
            row = row["record"]
        release = _parse_release(row)
        if release:
            releases.append(release)
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
    rows = _rows(payload)
    return bool(rows)


def _parse_release(row: dict) -> ExternalRelease | None:
    series_id = _series_id(row)
    chapter = _first_text(row, "chapter", "chapter_number", "chapterNumber", "chap")
    release_date = _date_value(
        row.get("release_date")
        or row.get("releaseDate")
        or row.get("date")
        or row.get("timestamp")
    )
    if series_id is None or not chapter or release_date is None:
        return None
    return ExternalRelease(
        series_id=series_id,
        chapter=chapter,
        release_date=release_date,
        volume=_first_text(row, "volume", "vol"),
        group_name=_group_name(row),
        external_release_id=_first_text(row, "id", "release_id", "releaseId"),
        source_url=_first_text(row, "url", "source_url", "sourceUrl"),
        raw_payload=row,
    )


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


def _series_id(row):
    value = row.get("series_id") or row.get("seriesId")
    series = row.get("series")
    if value is None and isinstance(series, dict):
        value = series.get("id") or series.get("series_id")
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
        first = group[0]
        return _first_text(first, "name", "title") if isinstance(first, dict) else str(first)
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

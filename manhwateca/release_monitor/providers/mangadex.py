from datetime import date, datetime

from manhwateca.mangadex_service.search import iter_manga_feed
from manhwateca.release_monitor.models import ExternalRelease
from manhwateca.release_monitor.providers.mangaupdates import ReleaseProviderPage


class MangaDexReleaseProvider:
    name = "mangadex"

    def __init__(self, feed_iter_func=None):
        self.feed_iter_func = feed_iter_func or iter_manga_feed

    def fetch_manga(self, manga_id: str, **feed_options) -> ReleaseProviderPage:
        releases, stats = normalize_mangadex_feed(
            manga_id,
            self.feed_iter_func(manga_id, **feed_options),
        )
        return ReleaseProviderPage(
            releases=releases,
            stats=stats,
            has_results_collection=bool(releases) or stats["releases_received"] > 0,
            has_next_page=False,
        )


def normalize_mangadex_feed(manga_id: str, items):
    releases = []
    stats = _empty_stats()
    for item in items:
        stats["releases_received"] += 1
        release = external_release_from_feed_item(manga_id, item)
        if release is None:
            stats["releases_invalid"] += 1
            continue
        releases.append(release)
        stats["releases_parsed"] += 1
        stats["releases_with_series_metadata"] += 1
    return releases, stats


def external_release_from_feed_item(manga_id: str, item) -> ExternalRelease | None:
    external_series_id = str(manga_id or "").strip()
    release_date = _date_value(getattr(item, "publish_at", None))
    chapter = _text_or_none(getattr(item, "chapter", None))
    release_id = _text_or_none(getattr(item, "id", None))
    if not external_series_id or not release_id or not chapter or release_date is None:
        return None
    return ExternalRelease(
        provider="mangadex",
        external_series_id=external_series_id,
        external_release_id=release_id,
        chapter=chapter,
        release_date=release_date,
        volume=_text_or_none(getattr(item, "volume", None)),
        language=_text_or_none(getattr(item, "translated_language", None)),
        title=_text_or_none(getattr(item, "title", None)),
        raw_payload=getattr(item, "raw_payload", None),
    )


def _empty_stats():
    return {
        "releases_received": 0,
        "releases_parsed": 0,
        "releases_with_series_metadata": 0,
        "releases_missing_series_metadata": 0,
        "releases_invalid": 0,
    }


def _text_or_none(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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
        return None

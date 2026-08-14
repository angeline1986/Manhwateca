from dataclasses import dataclass
from datetime import datetime, timezone

from manhwateca.database.manga_repository import MangaRepository
from manhwateca.mangadex_service.search import iter_manga_feed
from manhwateca.release_monitor.providers.mangadex import external_release_from_feed_item
from manhwateca.release_monitor.repository import ReleaseMonitorRepository


PROVIDER = "mangadex"
STATE_KEY = "release_monitor"


@dataclass(frozen=True)
class MangaDexExecutionResult:
    manga_id: int
    external_series_id: str
    status: str
    works_consulted: int = 1
    feed_calls: int = 0
    pages_requested: int = 0
    items_received: int = 0
    releases_normalized: int = 0
    releases_ignored: int = 0
    releases_inserted: int = 0
    releases_already_known: int = 0
    failures: int = 0
    stop_reason: str | None = None
    previous_latest_release_published_at: str | None = None
    latest_release_published_at: str | None = None
    last_checked_at: str | None = None
    error_message: str | None = None


class MangaDexExecutionStateRepository:
    def __init__(self, manga_repository=None):
        self.manga_repository = manga_repository or MangaRepository()

    def get_state(self, manga_id, provider=PROVIDER) -> dict:
        ref = self.manga_repository.get_external_ref(manga_id, provider)
        metadata = ref.metadata if ref and isinstance(ref.metadata, dict) else {}
        state = metadata.get(STATE_KEY)
        return dict(state) if isinstance(state, dict) else {}

    def mark_success(
        self,
        manga_id,
        provider,
        external_id,
        *,
        checked_at: str,
        latest_release_published_at: str | None,
    ):
        ref = self.manga_repository.get_external_ref(manga_id, provider)
        metadata = dict(ref.metadata or {}) if ref and isinstance(ref.metadata, dict) else {}
        monitor_state = dict(metadata.get(STATE_KEY) or {})
        monitor_state["last_checked_at"] = checked_at
        monitor_state["latest_release_published_at"] = latest_release_published_at
        metadata[STATE_KEY] = monitor_state
        return self.manga_repository.upsert_external_ref(
            manga_id,
            provider,
            external_id,
            external_url=ref.external_url if ref else None,
            external_title=ref.external_title if ref else None,
            metadata=metadata,
        )


def process_manga(
    manga_id,
    mangadex_id,
    *,
    limit: int = 100,
    offset: int = 0,
    order: str = "desc",
    max_pages: int = 100,
    feed_iter_func=None,
    release_repository=None,
    state_repository=None,
    now_func=None,
    **request_options,
) -> MangaDexExecutionResult:
    normalized_manga_id = _int_or_none(manga_id)
    external_series_id = _text_or_none(mangadex_id)
    if normalized_manga_id is None or external_series_id is None:
        return MangaDexExecutionResult(
            manga_id=normalized_manga_id or 0,
            external_series_id=external_series_id or "",
            status="failed",
            works_consulted=0,
            failures=1,
            stop_reason="invalid_reference",
            error_message="manga_id e mangadex_id são obrigatórios.",
        )

    release_repository = release_repository or ReleaseMonitorRepository()
    state_repository = state_repository or MangaDexExecutionStateRepository()
    now_func = now_func or _utc_now
    state = state_repository.get_state(normalized_manga_id, PROVIDER)
    previous_latest_text = _text_or_none(state.get("latest_release_published_at"))
    previous_latest_dt = _datetime_value(previous_latest_text)
    latest_text = previous_latest_text
    latest_dt = previous_latest_dt
    feed_stats = {"pages_requested": 0}
    stop_reason = None

    if feed_iter_func is not None:
        item_iter = feed_iter_func(
            external_series_id,
            limit=limit,
            offset=offset,
            order=order,
            max_pages=max_pages,
            **request_options,
        )
    else:
        feed_func = request_options.pop("feed_func", None)

        def counted_feed_func(*args, **kwargs):
            feed_stats["pages_requested"] += 1
            if feed_func:
                return feed_func(*args, **kwargs)
            from manhwateca.mangadex_service.search import get_manga_feed

            return get_manga_feed(*args, **kwargs)

        item_iter = iter_manga_feed(
            external_series_id,
            limit=limit,
            offset=offset,
            order=order,
            max_pages=max_pages,
            feed_func=counted_feed_func,
            **request_options,
        )

    result_kwargs = {
        "manga_id": normalized_manga_id,
        "external_series_id": external_series_id,
        "previous_latest_release_published_at": previous_latest_text,
    }

    try:
        items_received = 0
        releases_normalized = 0
        releases_ignored = 0
        releases_inserted = 0
        releases_already_known = 0
        for item in item_iter:
            items_received += 1
            item_publish_dt = _datetime_value(getattr(item, "publish_at", None))
            if (
                previous_latest_dt is not None
                and item_publish_dt is not None
                and item_publish_dt <= previous_latest_dt
            ):
                releases_ignored += 1
                stop_reason = "known_release_reached"
                break

            if item_publish_dt is not None and (
                latest_dt is None or item_publish_dt > latest_dt
            ):
                latest_dt = item_publish_dt
                latest_text = _text_or_none(getattr(item, "publish_at", None))

            release = external_release_from_feed_item(external_series_id, item)
            if release is None:
                releases_ignored += 1
                continue
            releases_normalized += 1
            if release_repository.upsert_external_release(release, normalized_manga_id):
                releases_inserted += 1
            else:
                releases_already_known += 1

        checked_at = now_func().isoformat()
        state_repository.mark_success(
            normalized_manga_id,
            PROVIDER,
            external_series_id,
            checked_at=checked_at,
            latest_release_published_at=latest_text,
        )
        if stop_reason is None:
            if items_received == 0:
                stop_reason = "empty_feed"
            elif feed_stats["pages_requested"] >= max_pages:
                stop_reason = "safety_limit"
            else:
                stop_reason = "end_of_feed"
        return MangaDexExecutionResult(
            **result_kwargs,
            status="success",
            feed_calls=feed_stats["pages_requested"],
            pages_requested=feed_stats["pages_requested"],
            items_received=items_received,
            releases_normalized=releases_normalized,
            releases_ignored=releases_ignored,
            releases_inserted=releases_inserted,
            releases_already_known=releases_already_known,
            stop_reason=stop_reason,
            latest_release_published_at=latest_text,
            last_checked_at=checked_at,
        )
    except Exception as exc:
        return MangaDexExecutionResult(
            **result_kwargs,
            status="failed",
            feed_calls=feed_stats["pages_requested"],
            pages_requested=feed_stats["pages_requested"],
            failures=1,
            stop_reason="error",
            latest_release_published_at=latest_text,
            error_message=str(exc),
        )


def _utc_now():
    return datetime.now(timezone.utc)


def _text_or_none(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _datetime_value(value):
    text = _text_or_none(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None

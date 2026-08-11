from dataclasses import dataclass

from manhwateca.mangaupdates_service.client import list_releases_by_day
from manhwateca.release_monitor.models import ExternalRelease
from manhwateca.release_monitor.parser import (
    has_more_pages,
    parse_external_releases_with_stats,
)


@dataclass(frozen=True)
class ReleaseProviderPage:
    releases: list[ExternalRelease]
    stats: dict
    has_results_collection: bool
    has_next_page: bool


class MangaUpdatesReleaseProvider:
    name = "mangaupdates"

    def __init__(self, client_func=None):
        self.client_func = client_func or list_releases_by_day

    def fetch_page(self, page: int) -> ReleaseProviderPage:
        payload = self.client_func(page=page, include_metadata=True)
        has_results_collection = _has_results_key(payload)
        releases, stats = (
            parse_external_releases_with_stats(payload)
            if has_results_collection
            else ([], _empty_stats())
        )
        return ReleaseProviderPage(
            releases=releases,
            stats=stats,
            has_results_collection=has_results_collection,
            has_next_page=has_more_pages(payload, page),
        )


def _has_results_key(payload):
    if isinstance(payload, list):
        return bool(payload)
    if not isinstance(payload, dict):
        return False
    return any(key in payload for key in ("results", "releases", "items", "data"))


def _empty_stats():
    return {
        "releases_received": 0,
        "releases_parsed": 0,
        "releases_with_series_metadata": 0,
        "releases_missing_series_metadata": 0,
        "releases_invalid": 0,
    }

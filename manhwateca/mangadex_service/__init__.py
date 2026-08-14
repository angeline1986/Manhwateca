"""Serviços de integração com o MangaDex."""

from manhwateca.mangadex_service.client import (
    API_BASE,
    MangaDexError,
    MangaDexHTTPError,
    MangaDexPayloadError,
    MangaDexRateLimitError,
    request_json,
)
from manhwateca.mangadex_service.search import (
    MangaDexMangaDetails,
    MangaDexMangaCandidate,
    get_manga,
    parse_manga_details,
    parse_manga_search,
    search_manga,
)

__all__ = [
    "API_BASE",
    "MangaDexError",
    "MangaDexHTTPError",
    "MangaDexPayloadError",
    "MangaDexRateLimitError",
    "MangaDexMangaDetails",
    "MangaDexMangaCandidate",
    "get_manga",
    "parse_manga_details",
    "parse_manga_search",
    "request_json",
    "search_manga",
]

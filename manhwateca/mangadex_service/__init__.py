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
    MangaDexCoverArt,
    MangaDexMangaDetails,
    MangaDexMangaCandidate,
    build_cover_url,
    cover_art_from_details,
    get_manga_cover_art,
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
    "MangaDexCoverArt",
    "MangaDexMangaDetails",
    "MangaDexMangaCandidate",
    "build_cover_url",
    "cover_art_from_details",
    "get_manga_cover_art",
    "get_manga",
    "parse_manga_details",
    "parse_manga_search",
    "request_json",
    "search_manga",
]

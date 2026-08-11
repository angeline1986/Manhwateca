"""Serviços de integração com o MangaDex."""

from manhwateca.mangadex_service.client import (
    API_BASE,
    MangaDexError,
    MangaDexHTTPError,
    MangaDexPayloadError,
    MangaDexRateLimitError,
    request_json,
)

__all__ = [
    "API_BASE",
    "MangaDexError",
    "MangaDexHTTPError",
    "MangaDexPayloadError",
    "MangaDexRateLimitError",
    "request_json",
]

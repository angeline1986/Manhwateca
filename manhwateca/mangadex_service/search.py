from dataclasses import dataclass

from manhwateca.mangadex_service.client import MangaDexPayloadError, request_json


@dataclass(frozen=True)
class MangaDexMangaCandidate:
    id: str
    title: str | None
    titles: dict
    alt_titles: list[dict]
    original_language: str | None
    status: str | None
    year: int | None
    links: dict
    relationships: list[dict]
    raw_payload: dict


def search_manga(
    title: str,
    limit: int = 10,
    offset: int = 0,
    *,
    request_func=None,
    **request_options,
) -> list[MangaDexMangaCandidate]:
    query = str(title or "").strip()
    if not query:
        return []
    request_func = request_func or request_json
    payload = request_func(
        "/manga",
        {"title": query, "limit": limit, "offset": offset},
        **request_options,
    )
    return parse_manga_search(payload)


def parse_manga_search(payload) -> list[MangaDexMangaCandidate]:
    if not isinstance(payload, dict):
        raise MangaDexPayloadError("Busca MangaDex possui estrutura inválida.")
    data = payload.get("data")
    if data is None:
        return []
    if not isinstance(data, list):
        raise MangaDexPayloadError("Busca MangaDex possui data inválido.")
    candidates = []
    for item in data:
        candidate = _candidate_from_item(item)
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _candidate_from_item(item):
    if not isinstance(item, dict):
        return None
    manga_id = str(item.get("id") or "").strip()
    if not manga_id:
        return None
    attributes = item.get("attributes") or {}
    if not isinstance(attributes, dict):
        attributes = {}
    titles = _dict_or_empty(attributes.get("title"))
    alt_titles = _alt_titles(attributes.get("altTitles"))
    return MangaDexMangaCandidate(
        id=manga_id,
        title=_display_title(titles, alt_titles),
        titles=titles,
        alt_titles=alt_titles,
        original_language=_string_or_none(attributes.get("originalLanguage")),
        status=_string_or_none(attributes.get("status")),
        year=_int_or_none(attributes.get("year")),
        links=_dict_or_empty(attributes.get("links")),
        relationships=_relationships(item.get("relationships")),
        raw_payload=item,
    )


def _display_title(titles, alt_titles):
    for key in ("en", "pt-br", "ja-ro", "ko-ro", "zh-ro"):
        value = _string_or_none(titles.get(key))
        if value:
            return value
    for value in titles.values():
        text = _string_or_none(value)
        if text:
            return text
    for alt_title in alt_titles:
        for value in alt_title.values():
            text = _string_or_none(value)
            if text:
                return text
    return None


def _dict_or_empty(value):
    return value if isinstance(value, dict) else {}


def _alt_titles(value):
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _relationships(value):
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_or_none(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

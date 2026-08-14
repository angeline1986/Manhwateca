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


@dataclass(frozen=True)
class MangaDexMangaDetails:
    id: str
    title: str | None
    titles: dict
    alt_titles: list[dict]
    description: dict
    original_language: str | None
    status: str | None
    year: int | None
    links: dict
    latest_uploaded_chapter: str | None
    relationships: list[dict]
    raw_payload: dict


@dataclass(frozen=True)
class MangaDexCoverArt:
    manga_id: str
    file_name: str
    url: str
    url_256: str
    url_512: str
    raw_payload: dict


@dataclass(frozen=True)
class MangaDexFeedItem:
    id: str
    volume: str | None
    chapter: str | None
    title: str | None
    translated_language: str | None
    publish_at: str | None
    readable_at: str | None
    created_at: str | None
    updated_at: str | None
    relationships: list[dict]
    raw_payload: dict


@dataclass(frozen=True)
class MangaDexFeedPage:
    items: list[MangaDexFeedItem]
    limit: int
    offset: int
    total: int
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


def get_manga_feed(
    manga_id: str,
    limit: int = 100,
    offset: int = 0,
    order: str = "desc",
    *,
    request_func=None,
    **request_options,
) -> MangaDexFeedPage | None:
    uuid = str(manga_id or "").strip()
    if not uuid:
        return None
    request_func = request_func or request_json
    payload = request_func(
        f"/manga/{uuid}/feed",
        {
            "limit": limit,
            "offset": offset,
            "order[publishAt]": order,
        },
        **request_options,
    )
    return parse_manga_feed(payload)


def iter_manga_feed(
    manga_id: str,
    limit: int = 100,
    offset: int = 0,
    order: str = "desc",
    *,
    max_pages: int = 100,
    feed_func=None,
    **request_options,
):
    if max_pages < 1:
        return
    feed_func = feed_func or get_manga_feed
    current_offset = offset
    for _page_number in range(max_pages):
        page = feed_func(
            manga_id,
            limit=limit,
            offset=current_offset,
            order=order,
            **request_options,
        )
        if page is None or not page.items:
            break
        received = len(page.items)
        for item in page.items:
            yield item
        next_offset = current_offset + received
        if next_offset <= current_offset:
            break
        if next_offset >= page.total:
            break
        current_offset = next_offset


def get_manga(
    manga_id: str,
    include_cover_art: bool = False,
    *,
    request_func=None,
    **request_options,
) -> MangaDexMangaDetails | None:
    uuid = str(manga_id or "").strip()
    if not uuid:
        return None
    request_func = request_func or request_json
    params = {"includes[]": ["cover_art"]} if include_cover_art else None
    payload = request_func(f"/manga/{uuid}", params, **request_options)
    return parse_manga_details(payload)


def parse_manga_feed(payload) -> MangaDexFeedPage:
    if not isinstance(payload, dict):
        raise MangaDexPayloadError("Feed MangaDex possui estrutura inválida.")
    data = payload.get("data")
    if data is None:
        data = []
    if not isinstance(data, list):
        raise MangaDexPayloadError("Feed MangaDex possui data inválido.")
    items = []
    for item in data:
        feed_item = _feed_item_from_item(item)
        if feed_item is not None:
            items.append(feed_item)
    return MangaDexFeedPage(
        items=items,
        limit=_int_or_default(payload.get("limit"), 0),
        offset=_int_or_default(payload.get("offset"), 0),
        total=_int_or_default(payload.get("total"), len(items)),
        raw_payload=payload,
    )


def get_manga_cover_art(
    manga_id: str,
    *,
    request_func=None,
    **request_options,
) -> MangaDexCoverArt | None:
    details = get_manga(
        manga_id,
        include_cover_art=True,
        request_func=request_func,
        **request_options,
    )
    if details is None:
        return None
    return cover_art_from_details(details)


def cover_art_from_details(details: MangaDexMangaDetails) -> MangaDexCoverArt | None:
    for relationship in details.relationships:
        if relationship.get("type") != "cover_art":
            continue
        attributes = relationship.get("attributes") or {}
        if not isinstance(attributes, dict):
            continue
        file_name = _string_or_none(attributes.get("fileName"))
        if not file_name:
            continue
        return MangaDexCoverArt(
            manga_id=details.id,
            file_name=file_name,
            url=build_cover_url(details.id, file_name),
            url_256=build_cover_url(details.id, file_name, 256),
            url_512=build_cover_url(details.id, file_name, 512),
            raw_payload=relationship,
        )
    return None


def build_cover_url(manga_id: str, file_name: str, size: int | None = None) -> str:
    uuid = str(manga_id or "").strip()
    name = str(file_name or "").strip()
    if not uuid:
        raise ValueError("UUID da obra MangaDex é obrigatório.")
    if not name:
        raise ValueError("Nome do arquivo da capa MangaDex é obrigatório.")
    if size not in (None, 256, 512):
        raise ValueError("Tamanho de capa MangaDex deve ser None, 256 ou 512.")
    suffix = "" if size is None else f".{size}.jpg"
    return f"https://uploads.mangadex.org/covers/{uuid}/{name}{suffix}"


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


def parse_manga_details(payload) -> MangaDexMangaDetails | None:
    if not isinstance(payload, dict):
        raise MangaDexPayloadError("Detalhe MangaDex possui estrutura inválida.")
    data = payload.get("data")
    if data is None:
        return None
    if not isinstance(data, dict):
        raise MangaDexPayloadError("Detalhe MangaDex possui data inválido.")
    return _details_from_item(data)


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


def _feed_item_from_item(item):
    if not isinstance(item, dict):
        return None
    feed_id = str(item.get("id") or "").strip()
    if not feed_id:
        return None
    attributes = item.get("attributes") or {}
    if not isinstance(attributes, dict):
        attributes = {}
    return MangaDexFeedItem(
        id=feed_id,
        volume=_string_or_none(attributes.get("volume")),
        chapter=_string_or_none(attributes.get("chapter")),
        title=_string_or_none(attributes.get("title")),
        translated_language=_string_or_none(attributes.get("translatedLanguage")),
        publish_at=_string_or_none(attributes.get("publishAt")),
        readable_at=_string_or_none(attributes.get("readableAt")),
        created_at=_string_or_none(attributes.get("createdAt")),
        updated_at=_string_or_none(attributes.get("updatedAt")),
        relationships=_relationships(item.get("relationships")),
        raw_payload=item,
    )


def _details_from_item(item):
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
    return MangaDexMangaDetails(
        id=manga_id,
        title=_display_title(titles, alt_titles),
        titles=titles,
        alt_titles=alt_titles,
        description=_dict_or_empty(attributes.get("description")),
        original_language=_string_or_none(attributes.get("originalLanguage")),
        status=_string_or_none(attributes.get("status")),
        year=_int_or_none(attributes.get("year")),
        links=_dict_or_empty(attributes.get("links")),
        latest_uploaded_chapter=_string_or_none(
            attributes.get("latestUploadedChapter")
        ),
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


def _int_or_default(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

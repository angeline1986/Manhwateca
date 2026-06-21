from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MangaRecord:
    id: int | None
    work_code: str | None
    title: str
    alternative_title: str | None = None
    reading_status: str | None = None
    personal_rank: str | None = None
    score: Decimal | None = None
    last_read_chapter: Decimal | None = None
    latest_available_chapter: Decimal | None = None
    size_label: str | None = None
    count_status: str | None = None
    latest_mangaupdates_chapter: Decimal | None = None
    mangaupdates_url: str | None = None
    spice_level: str | None = None
    format: str | None = None
    themes: list[str] | None = None
    notion_page_id: str | None = None
    notion_last_synced_at: str | None = None
    notion_sync_status: str | None = None


def manga_from_row(row: dict) -> MangaRecord:
    return MangaRecord(
        id=row.get("id"),
        work_code=row.get("work_code"),
        title=row.get("title") or row.get("nome") or "",
        alternative_title=row.get("alternative_title"),
        reading_status=row.get("reading_status")
        or row.get("reading_status_v2"),
        personal_rank=row.get("personal_rank"),
        score=row.get("score"),
        last_read_chapter=row.get("last_read_chapter"),
        latest_available_chapter=row.get("latest_available_chapter"),
        size_label=row.get("size_label"),
        count_status=row.get("count_status"),
        latest_mangaupdates_chapter=row.get("latest_mangaupdates_chapter"),
        mangaupdates_url=row.get("mangaupdates_url"),
        spice_level=row.get("spice_level"),
        format=row.get("format"),
        themes=_normalize_themes(row.get("themes")),
        notion_page_id=row.get("notion_page_id"),
        notion_last_synced_at=_string_or_none(row.get("notion_last_synced_at")),
        notion_sync_status=row.get("notion_sync_status"),
    )


def _normalize_themes(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split("|") if item.strip()]
    return [str(value)]


def _string_or_none(value):
    if value is None:
        return None
    return str(value)

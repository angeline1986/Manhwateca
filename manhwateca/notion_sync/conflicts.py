from datetime import datetime

from manhwateca.notion_sync import statuses


TECHNICAL_FIELDS = {
    "work_code",
    "title",
    "alternative_title",
    "latest_available_chapter",
    "size_label",
    "count_status",
    "latest_mangaupdates_chapter",
    "mangaupdates_url",
    "format",
}

EDITORIAL_FIELDS = {
    "reading_status",
    "reading_status_v2",
    "personal_rank",
    "score",
    "spice_level",
    "last_read_chapter",
}


def field_owner(field_name: str) -> str:
    if field_name in TECHNICAL_FIELDS:
        return "postgresql"
    if field_name in EDITORIAL_FIELDS:
        return "notion"
    return "postgresql"


def decide_sync_status(
    local_updated_at,
    notion_updated_at,
    last_synced_at,
):
    local_changed = changed_after(local_updated_at, last_synced_at)
    notion_changed = changed_after(notion_updated_at, last_synced_at)

    if local_changed and notion_changed:
        return statuses.CONFLICT
    if local_changed or notion_changed:
        return statuses.PENDING
    return statuses.SYNCED


def changed_after(updated_at, reference_at) -> bool:
    updated = _parse_datetime(updated_at)
    reference = _parse_datetime(reference_at)
    if updated is None:
        return False
    if reference is None:
        return True
    return updated > reference


def _parse_datetime(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))

from manhwateca.database.manga_repository import MangaRepository
from manhwateca.notion_sync import statuses


def sync_candidates_payload(repository=None):
    repository = repository or MangaRepository()
    records = [
        record for record in repository.list_mangas()
        if _has_work_code(record)
    ]
    items = [_candidate_item(record) for record in records]
    return {
        "items": items,
        "summary": _summary(items),
    }


def _candidate_item(record):
    status = _string_or_none(record.notion_sync_status)
    return {
        "workId": record.id,
        "title": record.title,
        "workCode": record.work_code,
        "mangaupdatesUrl": record.mangaupdates_url,
        "coverUrl": record.cover_url,
        "notionPageId": record.notion_page_id,
        "notionSyncStatus": status,
        "notionLastSyncedAt": record.notion_last_synced_at,
        "displayStatus": _display_status(status, record.notion_last_synced_at),
        "selectable": _selectable(status),
    }


def _summary(items):
    result = {
        "total": len(items),
        "neverSynced": 0,
        "synced": 0,
        "pending": 0,
        "error": 0,
        "conflict": 0,
        "ignored": 0,
    }
    for item in items:
        status = item["notionSyncStatus"]
        if status is None and item["notionLastSyncedAt"] is None:
            result["neverSynced"] += 1
        elif status in result:
            result[status] += 1
    return result


def _display_status(status, synced_at):
    if status is None and synced_at is None:
        return "Nunca sincronizada"
    if status == statuses.SYNCED:
        return f"Sincronizada em {_format_datetime(synced_at)}" if synced_at else "Sincronizada"
    if status == statuses.ERROR:
        return "Erro na última sincronização"
    if status == statuses.CONFLICT:
        return "Precisa de revisão"
    if status == statuses.PENDING:
        return "Pendente"
    if status == statuses.IGNORED:
        return "Ignorada"
    return "Estado local não informado"


def _selectable(status):
    return status not in {statuses.CONFLICT, statuses.IGNORED}


def _has_work_code(record):
    return bool(_string_or_none(record.work_code))


def _string_or_none(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _format_datetime(value):
    if value is None:
        return ""
    text = str(value)
    return text[:16].replace("T", " ")

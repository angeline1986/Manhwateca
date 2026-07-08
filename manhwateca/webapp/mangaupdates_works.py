from math import ceil
from urllib.parse import parse_qs

from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    connect,
)
from manhwateca.notion_sync.matching import normalize_title


VALID_STATUS = {
    "WITHOUT_ID",
    "CONFIRMED",
    "METADATA_PENDING",  # Adicionado para suportar a nova tela
    "READY_TO_SEARCH",
    "CANDIDATES_FOUND",
    "PENDING_REVIEW",
    "MANUAL_ID_REQUIRED",
    "ERROR",
}


def works_payload(query_string="", *, connection_factory=connect):
    params = _params(query_string)
    page = _positive_int(params.get("page"), 1)
    page_size = min(_positive_int(params.get("pageSize"), 25), 100)
    status = (params.get("status") or "WITHOUT_ID").upper()
    search = (params.get("search") or "").strip()
    only_failed = _truthy(params.get("onlyFailed"))
    sort = params.get("sort") or "title"

    try:
        connection = connection_factory()
    except (DatabaseConfigurationError, DatabaseConnectionError) as error:
        return {
            "success": False,
            "data": None,
            "error": str(error),
        }

    try:
        rows = _fetch_rows(connection)
    finally:
        connection.close()

    items = [_row_to_item(row) for row in rows]
    kpis = _kpis(items)
    filtered = _filter_items(items, status, search, only_failed)
    filtered = _sort_items(filtered, sort)
    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start:start + page_size]
    return {
        "success": True,
        "data": {
            "kpis": kpis,
            "items": page_items,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "pages": ceil(total / page_size) if total else 0,
            },
        },
    }


def _params(query_string):
    parsed = parse_qs(query_string or "")
    return {key: values[-1] for key, values in parsed.items() if values}


def _fetch_rows(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH latest_candidates AS (
                SELECT DISTINCT ON (work_id)
                    work_id,
                    status,
                    searched_title,
                    created_at AS last_search_at
                FROM manhwateca.flow_id_candidates
                WHERE work_id IS NOT NULL
                ORDER BY work_id, created_at DESC, id DESC
            ),
            candidate_counts AS (
                SELECT
                    work_id,
                    COUNT(*) FILTER (WHERE status = 'pending_review') AS pending_count,
                    COUNT(*) FILTER (WHERE status = 'not_found') AS not_found_count,
                    COUNT(*) FILTER (WHERE status = 'error') AS error_count,
                    COUNT(*) FILTER (WHERE candidate_external_id IS NOT NULL) AS candidates_count
                FROM manhwateca.flow_id_candidates
                WHERE work_id IS NOT NULL
                GROUP BY work_id
            )
            SELECT
                m.id,
                m.title,
                m.alternative_title,
                m.work_code,
                m.mangaupdates_url,
                m.cover_url,                -- ADICIONADO: m.cover_url
                m.created_at,
                m.updated_at,
                lc.status AS latest_candidate_status,
                lc.searched_title,
                lc.last_search_at,
                COALESCE(cc.pending_count, 0) AS pending_count,
                COALESCE(cc.not_found_count, 0) AS not_found_count,
                COALESCE(cc.error_count, 0) AS error_count,
                COALESCE(cc.candidates_count, 0) AS candidates_count
            FROM manhwateca.vw_mangas m
            LEFT JOIN latest_candidates lc ON lc.work_id = m.id
            LEFT JOIN candidate_counts cc ON cc.work_id = m.id
            ORDER BY m.title
            """
        )
        return list(cursor.fetchall())


def _pending_metadata(row):
    """Calcula quais campos obrigatórios estão ausentes para obras com ID confirmado."""
    pending = []
    # Só faz sentido falar em metadados se a obra já tem um ID (work_code)
    if row.get("work_code"):
        if not row.get("mangaupdates_url"):
            pending.append("mangaupdatesUrl")
        if not row.get("cover_url"):
            pending.append("cover")
    return pending


def _row_to_item(row):
    decision_status = _decision_status(row)
    candidates_count = int(row.get("candidates_count") or 0)
    pending_metadata = _pending_metadata(row)
    
    return {
        "id": f"manga_{row['id']}",
        "mangaId": row["id"],
        "localTitle": row.get("title") or "",
        "normalizedTitle": normalize_title(row.get("title") or ""),
        "alternativeTitles": _aliases(row.get("alternative_title")),
        "folderPath": None,
        "mangaupdatesId": row.get("work_code"),
        "mangaupdatesUrl": row.get("mangaupdates_url"),
        "coverUrl": row.get("cover_url"),             # ADICIONADO
        "pendingMetadata": pending_metadata,          # ADICIONADO
        "metadataStatus": "PENDING" if pending_metadata else "UP_TO_DATE", # ADICIONADO
        "decisionStatus": decision_status,
        "detailsStatus": "PENDING" if row.get("work_code") else "NOT_REQUIRED",
        "matchConfidence": None,
        "candidatesCount": candidates_count,
        "latestChapter": None,
        "detailsSyncedAt": None,
        "lastSearchAt": _string_or_none(row.get("last_search_at")),
        "createdAt": _string_or_none(row.get("created_at")),
        "updatedAt": _string_or_none(row.get("updated_at")),
        "nextAction": _next_action(decision_status),
    }


def _decision_status(row):
    if row.get("work_code"):
        return "CONFIRMED"
    if int(row.get("error_count") or 0):
        return "ERROR"
    if int(row.get("not_found_count") or 0):
        return "MANUAL_ID_REQUIRED"
    if int(row.get("pending_count") or 0):
        return "PENDING_REVIEW"
    if int(row.get("candidates_count") or 0):
        return "CANDIDATES_FOUND"
    return "READY_TO_SEARCH"


def _next_action(status):
    return {
        "WITHOUT_ID": "SEARCH_API",
        "READY_TO_SEARCH": "SEARCH_API",
        "CANDIDATES_FOUND": "REVIEW_CANDIDATES",
        "PENDING_REVIEW": "REVIEW_CANDIDATES",
        "MANUAL_ID_REQUIRED": "MANUAL_SEARCH",
        "ERROR": "RETRY_FAILED",
    }.get(status, "SEARCH_API")


def _kpis(items):
    return {
        "withoutId": sum(1 for item in items if not item["mangaupdatesId"]),
        "readyToSearch": sum(1 for item in items if item["decisionStatus"] == "READY_TO_SEARCH"),
        "candidatesFound": sum(1 for item in items if item["decisionStatus"] in {"CANDIDATES_FOUND", "PENDING_REVIEW"}),
        "noResult": sum(1 for item in items if item["decisionStatus"] == "MANUAL_ID_REQUIRED"),
        "apiErrors": sum(1 for item in items if item["decisionStatus"] == "ERROR"),
    }


def _filter_items(items, status, search, only_failed):
    filtered = items
    if status in VALID_STATUS:
        if status == "WITHOUT_ID":
            filtered = [item for item in filtered if not item["mangaupdatesId"]]
        elif status == "CONFIRMED":
            filtered = [item for item in filtered if item["decisionStatus"] == "CONFIRMED"]
        elif status == "METADATA_PENDING":
            # Nova regra: Obras confirmadas que possuem pelo menos um campo pendente
            filtered = [
                item for item in filtered 
                if item["mangaupdatesId"] and len(item.get("pendingMetadata", [])) > 0
            ]
        else:
            filtered = [item for item in filtered if item["decisionStatus"] == status]
    
    if only_failed:
        filtered = [item for item in filtered if item["decisionStatus"] == "ERROR"]
    
    if search:
        normalized = normalize_title(search)
        filtered = [
            item for item in filtered
            if normalized in item["normalizedTitle"]
            or any(normalized in normalize_title(alias) for alias in item["alternativeTitles"])
        ]
    return filtered


def _sort_items(items, sort):
    if sort == "updatedAt":
        return sorted(items, key=lambda item: item["updatedAt"] or "", reverse=True)
    if sort == "lastSearchAt":
        return sorted(items, key=lambda item: item["lastSearchAt"] or "")
    return sorted(items, key=lambda item: item["localTitle"].casefold())


def _aliases(value):
    return [item.strip() for item in str(value or "").split("|") if item.strip()]


def _positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _truthy(value):
    return str(value or "").lower() in {"1", "true", "yes", "sim"}


def _string_or_none(value):
    return str(value) if value is not None else None


import json

from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    connect,
)
from manhwateca.webapp.candidate_filters import ranked_unique_candidates


def flow_candidates_review_payload(connection_factory=connect):
    try:
        connection = connection_factory()
    except (DatabaseConfigurationError, DatabaseConnectionError):
        return None
    try:
        rows = _fetch_rows(connection)
    finally:
        connection.close()
    items = _rows_to_items(rows)
    pending = [item for item in items if item["decisionStatus"] == "PENDING_REVIEW"]
    manual = [item for item in items if item["decisionStatus"] == "MANUAL_ID_REQUIRED"]
    return {
        "source": {
            "kind": "postgresql",
            "label": "PostgreSQL",
            "detail": "flow_id_candidates",
            "role": "fila oficial de revisão de IDs",
        },
        "summary": {
            "total": len(items),
            "review": len(pending),
            "confirmed": 0,
            "pending": len(manual),
            "pendingReview": len(pending),
            "manualIdRequired": len(manual),
            "selectedButNotApplied": 0,
        },
        "items": items,
    }


def _fetch_rows(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                c.id, c.work_id, c.searched_title,
                c.candidate_external_id, c.candidate_title,
                c.confidence, c.status, c.details, c.created_at,
                m.title AS local_title,
                m.alternative_title
            FROM manhwateca.flow_id_candidates c
            LEFT JOIN manhwateca.vw_mangas m ON m.id = c.work_id
            WHERE c.status IN ('pending_review', 'not_found')
              AND NOT EXISTS (
                  SELECT 1 FROM manhwateca.vw_mangas confirmed
                  WHERE confirmed.id = c.work_id
                    AND confirmed.work_code IS NOT NULL
              )
            ORDER BY
              CASE WHEN c.status = 'pending_review' THEN 1 ELSE 2 END,
              c.confidence DESC NULLS LAST,
              c.created_at DESC,
              c.searched_title ASC
            """
        )
        return list(cursor.fetchall())


def _rows_to_items(rows):
    grouped = {}
    for row in rows:
        key = row.get("work_id") or row.get("searched_title")
        item = grouped.setdefault(key, _item(row))
        if row.get("status") == "pending_review":
            item["candidates"].append(_candidate(row))
    for item in grouped.values():
        item["candidates"] = ranked_unique_candidates(
            item["candidates"],
            title_key="title",
            score_key="confidence",
        )
    return list(grouped.values())


def _item(row):
    status = "PENDING_REVIEW" if row.get("status") == "pending_review" else "MANUAL_ID_REQUIRED"
    title = row.get("local_title") or row.get("searched_title") or ""
    return {
        "queueId": f"flow_{row.get('work_id') or row.get('id')}",
        "mangaId": row.get("work_id"),
        "localTitle": title,
        "normalizedTitle": row.get("searched_title") or "",
        "alternativeTitles": _aliases(row.get("alternative_title")),
        "selectedCandidateId": None,
        "manualMangaupdatesId": None,
        "decisionStatus": status,
        "confidence": _float_or_none(row.get("confidence")),
        "reason": "NO_RESULT" if status == "MANUAL_ID_REQUIRED" else "AMBIGUOUS",
        "updatedAt": _string_or_none(row.get("created_at")),
        "nome": title,
        "nome_decisao": title,
        "candidates": [],
    }


def _candidate(row):
    details = _payload_dict(row.get("details"))
    candidate = details.get("candidate") if isinstance(details.get("candidate"), dict) else {}
    confidence = _float_or_none(row.get("confidence"))
    title = row.get("candidate_title") or candidate.get("titulo") or ""
    return {
        "id": row.get("candidate_external_id"),
        "title": title,
        "titulo": title,
        "url": candidate.get("url"),
        "confidence": confidence,
        "pontuacao": confidence,
        "isRecommended": bool(confidence is not None and confidence >= 0.85),
        "tipo": candidate.get("tipo"),
        "ano": candidate.get("ano"),
        "descricao": candidate.get("descricao"),
        "bl": candidate.get("bl"),
    }


def _payload_dict(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            data = json.loads(value)
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}
    return {}


def _float_or_none(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_or_none(value):
    return str(value) if value is not None else None


def _aliases(value):
    if not value:
        return []
    cleaned = str(value)
    for separator in ("\n", ","):
        cleaned = cleaned.replace(separator, "|")
    return [
        item.strip()
        for item in cleaned.split("|")
        if item.strip()
    ]

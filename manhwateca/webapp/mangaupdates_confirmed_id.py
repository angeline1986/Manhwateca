from manhwateca.database import MangaRepository
from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
)
from manhwateca.mangaupdates_service.client import get_series
from manhwateca.mangaupdates_service.details import summarize_series


def confirmed_id_candidates_payload(query_string="", *, repository=None):
    params = _query_params(query_string)
    search = str(params.get("search") or "").strip()
    try:
        limit = min(max(int(params.get("limit") or 10), 1), 25)
    except (TypeError, ValueError):
        limit = 10

    try:
        repository = repository or MangaRepository()
        records = repository.list_mangas()
    except (DatabaseConfigurationError, DatabaseConnectionError) as error:
        return {"success": False, "error": str(error), "items": []}, 503

    items = [
        _confirmed_candidate_payload(record)
        for record in records
        if _safe_work_code(getattr(record, "work_code", None))
    ]
    if search:
        normalized = _normalize_search(search)
        items = [
            item for item in items
            if normalized in _normalize_search(item["title"])
            or normalized in str(item["id"])
            or normalized in str(item["current_work_code"])
        ]
    return {
        "success": True,
        "items": items[:limit],
        "total": len(items),
    }, 200


def confirmed_id_preview_payload(
    payload,
    *,
    repository=None,
    detail_function=get_series,
    summarize_function=summarize_series,
):
    try:
        work_id = _positive_int(payload.get("work_id"))
        new_work_code = _work_code(payload.get("new_work_code"))
    except ValueError as error:
        return {"error": str(error)}, 400

    try:
        repository = repository or MangaRepository()
        work = repository.find_by_id(work_id)
    except (DatabaseConfigurationError, DatabaseConnectionError) as error:
        return {"error": str(error)}, 503

    if work is None:
        return {"error": "Obra não encontrada no PostgreSQL."}, 404
    current_work_code = _work_code(getattr(work, "work_code", None))
    if not current_work_code:
        return {"error": "A obra ainda não possui ID MangaUpdates confirmado."}, 409
    if new_work_code == current_work_code:
        return {
            "work": _work_payload(work),
            "current": {"work_code": current_work_code},
            "proposed": {"work_code": new_work_code},
            "can_apply": False,
            "blockers": [{
                "code": "same_id",
                "message": "O novo ID informado já é o ID confirmado desta obra.",
            }],
        }, 409

    existing = repository.find_by_work_code(new_work_code)
    if existing is not None and int(existing.id) != int(work.id):
        return {
            "work": _work_payload(work),
            "current": {"work_code": current_work_code},
            "proposed": {"work_code": new_work_code},
            "can_apply": False,
            "blockers": [{
                "code": "external_id_already_assigned",
                "message": "ID MangaUpdates já associado a outra obra.",
                "existing_work_id": int(existing.id),
                "existing_title": existing.title,
            }],
        }, 409

    try:
        proposed_raw = detail_function(new_work_code)
    except Exception:
        return {"error": "Não foi possível validar o novo ID no MangaUpdates."}, 502
    if not proposed_raw:
        return {"error": "ID MangaUpdates não encontrado."}, 404

    proposed = summarize_function(proposed_raw)
    current = _current_summary(current_work_code, detail_function, summarize_function)
    return {
        "work": _work_payload(work),
        "current": current,
        "proposed": _summary_payload(new_work_code, proposed),
        "can_apply": True,
        "blockers": [],
    }, 200


def apply_confirmed_id_correction_payload(
    payload,
    *,
    repository=None,
    detail_function=get_series,
    summarize_function=summarize_series,
):
    if not payload.get("confirmed"):
        return {"error": "Confirme a correção antes de aplicar."}, 400
    expected_current_work_code = _safe_work_code(payload.get("expected_current_work_code"))
    if not expected_current_work_code:
        return {"error": "Faça uma nova validação antes de aplicar."}, 400

    try:
        repository = repository or MangaRepository()
        work = repository.find_by_id(_positive_int(payload.get("work_id")))
    except (DatabaseConfigurationError, DatabaseConnectionError) as error:
        return {"error": str(error)}, 503
    except ValueError as error:
        return {"error": str(error)}, 400
    if work is None:
        return {"error": "Obra não encontrada no PostgreSQL."}, 404
    actual_current_work_code = _safe_work_code(getattr(work, "work_code", None))
    if actual_current_work_code != expected_current_work_code:
        return _stale_preview_payload(
            expected_current_work_code,
            actual_current_work_code,
        ), 409

    preview, status = confirmed_id_preview_payload(
        payload,
        repository=repository,
        detail_function=detail_function,
        summarize_function=summarize_function,
    )
    if status != 200:
        return preview, status

    result = repository.correct_confirmed_mangaupdates_id(
        preview["work"]["id"],
        preview["proposed"]["work_code"],
        expected_current_work_code=expected_current_work_code,
        event_payload={
            "current": preview.get("current"),
            "proposed": preview.get("proposed"),
            "source": "Corrigir ID confirmado",
        },
    )
    if not result:
        if result.status == "stale_preview":
            return _stale_preview_payload(
                result.expected_current_work_code,
                result.actual_current_work_code,
            ), 409
        if result.status == "external_id_already_assigned":
            return {
                "applied": False,
                "can_apply": False,
                "blockers": [{
                    "code": "external_id_already_assigned",
                    "message": result.message,
                    "existing_work_id": result.existing_work_id,
                    "existing_title": result.existing_title,
                }],
            }, 409
        return {
            "error": result.message or "Não foi possível aplicar a correção.",
            "status": result.status,
        }, 409

    return {
        "applied": True,
        "work_id": result.work_id,
        "old_work_code": result.old_series_id,
        "new_work_code": result.new_series_id,
        "invalidated_fields": list(result.invalidated_fields),
        "metadata_status": "pending",
        "notion_sync_status": result.notion_sync_status,
    }, 200


def _stale_preview_payload(expected_current_work_code, actual_current_work_code):
    return {
        "applied": False,
        "can_apply": False,
        "blockers": [{
            "code": "stale_preview",
            "message": (
                "O ID confirmado desta obra foi alterado após o preview. "
                "Faça uma nova validação antes de aplicar."
            ),
        }],
        "expected_current_work_code": expected_current_work_code,
        "actual_current_work_code": actual_current_work_code,
    }


def _current_summary(work_code, detail_function, summarize_function):
    try:
        raw = detail_function(work_code)
    except Exception:
        return {"work_code": work_code, "available": False}
    if not raw:
        return {"work_code": work_code, "available": False}
    return {"available": True, **_summary_payload(work_code, summarize_function(raw))}


def _summary_payload(work_code, summary):
    return {
        "work_code": str(work_code),
        "title": summary.get("title"),
        "url": summary.get("url"),
        "cover_url": summary.get("cover_url"),
        "format": summary.get("format"),
        "latest_chapter": summary.get("latest_chapter"),
        "aliases": summary.get("associated_titles") or [],
    }


def _work_payload(work):
    return {
        "id": int(work.id),
        "title": work.title,
        "current_work_code": _work_code(work.work_code),
        "mangaupdates_url": getattr(work, "mangaupdates_url", None),
        "cover_url": getattr(work, "cover_url", None),
        "alternative_title": getattr(work, "alternative_title", None),
        "notion_sync_status": getattr(work, "notion_sync_status", None),
    }


def _confirmed_candidate_payload(work):
    return {
        "id": int(work.id),
        "title": work.title,
        "current_work_code": _safe_work_code(work.work_code),
        "mangaupdates_url": getattr(work, "mangaupdates_url", None),
        "alternative_title": getattr(work, "alternative_title", None),
        "notion_sync_status": getattr(work, "notion_sync_status", None),
    }


def _query_params(query_string):
    from urllib.parse import parse_qs

    parsed = parse_qs(query_string or "")
    return {key: values[-1] for key, values in parsed.items() if values}


def _normalize_search(value):
    import unicodedata

    normalized = unicodedata.normalize("NFD", str(value or ""))
    return "".join(
        char for char in normalized
        if unicodedata.category(char) != "Mn"
    ).casefold().strip()


def _safe_work_code(value):
    try:
        return _work_code(value)
    except ValueError:
        return None


def _positive_int(value):
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ValueError("Informe uma obra válida.")
    if result <= 0:
        raise ValueError("Informe uma obra válida.")
    return result


def _work_code(value):
    result = str(value or "").strip()
    if not result:
        raise ValueError("Informe um ID MangaUpdates válido.")
    if not result.isdigit():
        raise ValueError("Informe um ID MangaUpdates válido.")
    return result

from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
)
from manhwateca.webapp.catalog_pending import (
    catalog_single_work,
    reconcile_catalog_aliases,
)
from manhwateca.webapp.editorial import update_editorial
from manhwateca.webapp.mangaupdates import (
    MangaUpdatesReviewUnavailable,
    apply_review_decisions,
)
from manhwateca.webapp.mangaupdates_decisions import (
    apply_decisions_payload,
    validate_decisions_payload,
)
from manhwateca.webapp.mangaupdates_confirmed_id import (
    apply_confirmed_id_correction_payload,
    confirmed_id_preview_payload,
)
from manhwateca.webapp.mangaupdates_search import search_payload
from manhwateca.webapp.notion_pages import create_missing_page_payload
from manhwateca.webapp.reviews import save_review_note
from manhwateca.webapp.translation import translate_to_portuguese


def handle_direct_post(path, payload, project_root, workflow_manager=None):
    if path == "/api/review-notes":
        note = str(payload.get("note", "")).strip()
        if not note:
            return {"error": "Informe uma observação."}, 400
        save_review_note(project_root, note)
        return {"saved": True}, 201
    if path in {
        "/api/mangaupdates/decisions",
        "/api/mangaupdates/decisions/validate",
        "/api/mangaupdates/decisions/apply",
    }:
        decisions = payload.get("decisions")
        queue_ids = payload.get("queueIds")
        has_decisions = isinstance(decisions, list) and bool(decisions)
        has_queue_ids = isinstance(queue_ids, list) and bool(queue_ids)
        if not has_decisions and not has_queue_ids:
            return {"error": "Informe ao menos uma decisão."}, 400
        if path == "/api/mangaupdates/decisions/validate":
            return validate_decisions_payload(decisions or queue_ids), 200
        if path == "/api/mangaupdates/decisions/apply":
            try:
                return apply_decisions_payload(
                    project_root,
                    decisions or queue_ids,
                    apply_review_decisions,
                )
            except MangaUpdatesReviewUnavailable as error:
                return {"error": str(error)}, 503
        try:
            applied, rejected, backup = apply_review_decisions(
                project_root, decisions
            )
        except MangaUpdatesReviewUnavailable as error:
            return {"error": str(error)}, 503
        result = {
            "applied": applied,
            "rejected": rejected,
            "backup": str(backup.relative_to(project_root)) if backup else None,
        }
        return result, 200 if not rejected else 422
    if path == "/api/mangaupdates/search":
        try:
            return search_payload(payload.get("query")), 200
        except ValueError as error:
            return {"error": str(error)}, 400
        except OSError:
            return {"error": "Não foi possível consultar o MangaUpdates."}, 502
    if path == "/api/mangaupdates/confirmed-id/preview":
        return confirmed_id_preview_payload(payload)
    if path == "/api/mangaupdates/confirmed-id/apply":
        return apply_confirmed_id_correction_payload(payload)
    if path == "/api/translate":
        try:
            translated = translate_to_portuguese(payload.get("text"))
        except ValueError as error:
            return {"error": str(error)}, 400
        except (ImportError, OSError, RuntimeError):
            return {
                "error": (
                    "Não foi possível traduzir. Verifique a instalação do "
                    "googletrans e a conexão com a internet."
                )
            }, 502
        return {"translation": translated}, 200
    if path == "/api/editorial":
        return _save_editorial(payload, project_root)
    if path == "/api/catalog/catalog-one":
        return _catalog_one(payload)
    if path == "/api/catalog/reconcile-aliases":
        return _reconcile_catalog_aliases(project_root)
    if path == "/api/notion/pages/create":
        return create_missing_page_payload(payload)
    if path == "/api/workflow":
        return _start_workflow(payload, workflow_manager)
    if path == "/api/workflow/continue":
        return _continue_workflow(payload, workflow_manager)
    return None


def _save_editorial(payload, project_root):
    name = str(payload.get("name", "")).strip()
    changes = payload.get("changes")
    if not name or not isinstance(changes, dict):
        return {"error": "Informe a obra e os campos alterados."}, 400
    try:
        work = update_editorial(project_root, name, changes)
    except KeyError:
        return {"error": "Obra não encontrada."}, 404
    except ValueError as error:
        return {"error": str(error)}, 400
    return {"saved": True, "work": work}, 200


def _catalog_one(payload):
    name = str(payload.get("name", "")).strip()
    try:
        result = catalog_single_work(name)
    except ValueError as error:
        return {"error": str(error)}, 400
    except KeyError:
        return {"error": "Obra não encontrada no Drive."}, 404
    except (DatabaseConfigurationError, DatabaseConnectionError) as error:
        return {"error": str(error)}, 503
    except RuntimeError as error:
        return {"error": str(error)}, 409
    return result, 200


def _reconcile_catalog_aliases(project_root):
    try:
        result = reconcile_catalog_aliases(project_root)
    except (DatabaseConfigurationError, DatabaseConnectionError) as error:
        return {"error": str(error)}, 503
    except RuntimeError as error:
        return {"error": str(error)}, 409
    return result, 200


def _start_workflow(payload, manager):
    try:
        result = manager.start(
            selected=payload.get("selected"),
            resume=bool(payload.get("resume")),
        )
    except ValueError as error:
        return {"error": str(error)}, 400
    except RuntimeError as error:
        return {"error": str(error)}, 409
    return result, 202


def _continue_workflow(payload, manager):
    try:
        result = manager.complete_manual(str(payload.get("step", "")))
    except ValueError as error:
        return {"error": str(error)}, 400
    except RuntimeError as error:
        return {"error": str(error)}, 409
    return result, 202

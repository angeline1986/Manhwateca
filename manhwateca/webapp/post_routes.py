from manhwateca.webapp.editorial import update_editorial
from manhwateca.webapp.mangaupdates import apply_review_decisions
from manhwateca.webapp.reviews import save_review_note


def handle_direct_post(path, payload, project_root, workflow_manager=None):
    if path == "/api/review-notes":
        note = str(payload.get("note", "")).strip()
        if not note:
            return {"error": "Informe uma observação."}, 400
        save_review_note(project_root, note)
        return {"saved": True}, 201
    if path == "/api/mangaupdates/decisions":
        decisions = payload.get("decisions")
        if not isinstance(decisions, list) or not decisions:
            return {"error": "Informe ao menos uma decisão."}, 400
        applied, rejected, backup = apply_review_decisions(
            project_root, decisions
        )
        result = {
            "applied": applied,
            "rejected": rejected,
            "backup": str(backup.relative_to(project_root)) if backup else None,
        }
        return result, 200 if not rejected else 422
    if path == "/api/editorial":
        return _save_editorial(payload, project_root)
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

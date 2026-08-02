import os

from manhwateca.database import MangaRepository
from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
)
from manhwateca.notion_sync.official_applier import OfficialNotionSyncApplier
from manhwateca.notion_sync.official_planner import OfficialNotionSyncPlanner
from manhwateca.notion_sync.sync_plan import SyncStatus


def create_missing_page_payload(payload, *, notion=None, database_id=None, repository=None):
    work_id = _work_id(payload)
    if work_id is None:
        return {"error": "Informe uma obra válida."}, 400

    try:
        repository = repository or MangaRepository()
        record = repository.find_by_id(work_id)
    except (DatabaseConfigurationError, DatabaseConnectionError) as error:
        return {"error": str(error)}, 503
    if record is None:
        return {"error": "Obra não encontrada no PostgreSQL."}, 404
    if not str(getattr(record, "work_code", "") or "").strip():
        return {"error": "Obra sem ID MangaUpdates para sincronização."}, 409

    notion, database_id, error = _notion_client(notion, database_id)
    if error:
        return {"error": error}, 503

    planner = OfficialNotionSyncPlanner(notion, database_id, repository=repository)
    plan = planner.plan_metadata_sync_for_ids([work_id])
    if not _has_missing_page_blocker(plan, work_id):
        return {
            "error": _plan_error_message(plan),
            "sync": _result_payload(plan.result),
        }, 409

    result = OfficialNotionSyncApplier(notion, repository).create_missing_page(
        record,
        database_id,
    )
    status = 201 if result.status == SyncStatus.SYNCED else 409
    if result.status == SyncStatus.ERROR:
        status = 502
    return {"sync": _apply_payload(result)}, status


def _work_id(payload):
    try:
        work_id = int(payload.get("work_id"))
    except (AttributeError, TypeError, ValueError):
        return None
    return work_id if work_id > 0 else None


def _notion_client(notion, database_id):
    if notion is not None and database_id:
        return notion, database_id, None
    token = os.environ.get("NOTION_TOKEN", "").strip()
    database_id = database_id or os.environ.get("NOTION_DATABASE_ID", "").strip()
    if not token or not database_id:
        return None, None, "Integração com Notion indisponível."
    try:
        from notion_client import Client
    except ImportError:
        return None, None, "Cliente Notion não instalado."
    return Client(auth=token), database_id, None


def _has_missing_page_blocker(plan, work_id):
    return any(
        blocker.code == "missing_page"
        and int(blocker.work_id or 0) == int(work_id)
        for blocker in plan.result.blockers
    )


def _plan_error_message(plan):
    blockers = plan.result.blockers
    if not blockers and plan.result.status == SyncStatus.SYNCED:
        return "A página já existe ou não há bloqueio de página ausente."
    return "A página não pode ser criada enquanto houver outro bloqueio."


def _result_payload(result):
    return {
        "status": result.status.value,
        "next_action": result.next_action.value,
        "created_count": result.created_count,
        "updated_count": result.updated_count,
        "missing_count": result.missing_count,
        "duplicate_count": result.duplicate_count,
        "unchanged_count": result.unchanged_count,
        "blockers": _blockers_payload(result.blockers),
    }


def _apply_payload(result):
    return {
        "status": result.status.value,
        "next_action": result.next_action.value,
        "applied_count": result.applied_count,
        "unchanged_count": result.unchanged_count,
        "failed_count": result.failed_count,
        "blockers": _blockers_payload(result.blockers),
    }


def _blockers_payload(blockers):
    return [
        {
            "code": blocker.code,
            "work_id": blocker.work_id,
            "work_title": blocker.work_title,
            "message": blocker.message,
            "severity": blocker.severity.value,
            "next_action": blocker.next_action.value,
        }
        for blocker in blockers
    ]

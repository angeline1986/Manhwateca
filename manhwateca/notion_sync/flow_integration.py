from manhwateca.database import MangaRepository
from manhwateca.flows.domain import FlowError
from manhwateca.flows.integrations import (
    IntegrationCheck,
    IntegrationStatus,
    IntegrationValidation,
    NotionSyncResult as FlowNotionSyncResult,
)
from manhwateca.notion_sync.official_applier import (
    NotionApplyResult,
    OfficialNotionSyncApplier,
)
from manhwateca.notion_sync.official_planner import OfficialNotionSyncPlanner
from manhwateca.notion_sync.sync_plan import NotionBlocker, SyncStatus


class OfficialNotionFlowIntegration:
    """Coordena o planner e o applier oficiais para o workflow."""

    def __init__(
        self,
        notion,
        database_id,
        repository=None,
        planner=None,
        applier=None,
    ):
        self.notion = notion
        self.database_id = database_id
        self.repository = repository or MangaRepository()
        self.planner = planner or OfficialNotionSyncPlanner(
            notion,
            database_id,
            repository=self.repository,
        )
        self.applier = applier or OfficialNotionSyncApplier(notion, self.repository)

    def check_status(self):
        validation = self.validate()
        if validation.valid:
            return IntegrationCheck(
                "Notion",
                IntegrationStatus.OPERATIONAL,
                message="Integração oficial com Notion disponível.",
            )
        return IntegrationCheck(
            "Notion",
            IntegrationStatus.UNAVAILABLE,
            message="Integração com Notion indisponível.",
            errors=validation.errors,
        )

    def validate(self, stage=None):
        if not self.notion or not self.database_id:
            return IntegrationValidation(
                stage=stage,
                valid=False,
                errors=(
                    FlowError(
                        "Integração com Notion indisponível.",
                        code="NOTION_UNAVAILABLE",
                    ),
                ),
            )
        return IntegrationValidation(stage=stage, valid=True)

    def sync_page(self, work_ids=None):
        work_ids = _normalize_work_ids(work_ids)
        if not work_ids:
            return FlowNotionSyncResult(
                metrics={
                    "status": SyncStatus.BLOCKED.value,
                    "message": "Nenhuma obra processada nesta jornada está disponível para sincronização.",
                    "scope": "incremental",
                    "scope_missing": True,
                    "work_ids": [],
                    "applied_count": 0,
                    "failed_count": 0,
                    "blocker_count": 0,
                },
            )
        scope_result = _validate_scope(self.repository, work_ids)
        if scope_result:
            return scope_result
        plan = self.planner.plan_metadata_sync_for_ids(work_ids)
        if plan.result.status == SyncStatus.BLOCKED:
            return _blocked_result(plan)
        if plan.result.status == SyncStatus.ERROR:
            return _planning_error_result(plan)
        if not plan.updates:
            return _no_changes_result(plan)
        apply_result = self.applier.apply(plan)
        return _apply_result(plan, apply_result)


def _blocked_result(plan):
    blocker_count = len(plan.result.blockers)
    return FlowNotionSyncResult(
        skipped=blocker_count,
        metrics={
            **_result_metrics(plan),
            "status": SyncStatus.BLOCKED.value,
            "message": f"Sincronização pausada por {blocker_count} bloqueio(s).",
            "blocker_count": blocker_count,
        },
    )


def _validate_scope(repository, work_ids):
    if not hasattr(repository, "list_mangas_by_ids"):
        return None
    records = repository.list_mangas_by_ids(work_ids)
    by_id = {int(record.id): record for record in records}
    blockers = []
    for work_id in work_ids:
        record = by_id.get(int(work_id))
        if record is None:
            blockers.append(NotionBlocker(
                code="scope_work_missing",
                work_id=int(work_id),
                message="Obra não encontrada no PostgreSQL.",
            ))
            continue
        if not _has_work_code(record):
            blockers.append(NotionBlocker(
                code="scope_work_not_eligible",
                work_id=int(work_id),
                work_title=record.title,
                message="Obra sem ID MangaUpdates local para sincronização.",
            ))
    if not blockers:
        return None
    return FlowNotionSyncResult(
        skipped=len(blockers),
        metrics={
            "status": SyncStatus.BLOCKED.value,
            "message": "Sincronização pausada por escopo inválido.",
            "scope": "incremental",
            "work_ids": work_ids,
            "blocker_count": len(blockers),
            "blockers": _blockers_to_dicts(tuple(blockers)),
        },
    )


def _planning_error_result(plan):
    failed_count = max(1, len(plan.result.blockers))
    return FlowNotionSyncResult(
        failed=failed_count,
        metrics={
            **_result_metrics(plan),
            "status": SyncStatus.ERROR.value,
            "message": "Erro ao planejar sincronização com Notion.",
            "applied_count": 0,
            "failed_count": failed_count,
            "blocker_count": len(plan.result.blockers),
        },
    )


def _no_changes_result(plan):
    return FlowNotionSyncResult(
        metrics={
            **_result_metrics(plan),
            "status": SyncStatus.SYNCED.value,
            "message": "Nenhuma alteração técnica necessária no Notion.",
            "applied_count": 0,
            "failed_count": 0,
        },
    )


def _apply_result(plan, apply_result: NotionApplyResult):
    metrics = {
        **_result_metrics(plan),
        "status": apply_result.status.value,
        "next_action": apply_result.next_action.value,
        "applied_count": apply_result.applied_count,
        "unchanged_count": apply_result.unchanged_count,
        "failed_count": apply_result.failed_count,
        "blocker_count": len(apply_result.blockers),
        "blockers": _blockers_to_dicts(apply_result.blockers),
    }
    if apply_result.status == SyncStatus.SYNCED:
        metrics["message"] = (
            f"{apply_result.applied_count} obra(s) atualizada(s) no Notion."
        )
        return FlowNotionSyncResult(
            updated=apply_result.applied_count,
            metrics=metrics,
        )
    if apply_result.status == SyncStatus.BLOCKED:
        metrics["message"] = (
            f"Sincronização pausada por {len(apply_result.blockers)} bloqueio(s)."
        )
        return FlowNotionSyncResult(
            skipped=len(apply_result.blockers),
            metrics=metrics,
        )
    metrics["message"] = "Erro ao aplicar sincronização com Notion."
    metrics["partial"] = apply_result.applied_count > 0
    return FlowNotionSyncResult(
        updated=apply_result.applied_count,
        failed=max(1, apply_result.failed_count),
        metrics=metrics,
    )


def _result_metrics(plan):
    return {
        "status": plan.result.status.value,
        "next_action": plan.result.next_action.value,
        "updated_count": plan.result.updated_count,
        "unchanged_count": plan.result.unchanged_count,
        "missing_count": plan.result.missing_count,
        "duplicate_count": plan.result.duplicate_count,
        "blocker_count": len(plan.result.blockers),
        "blockers": _blockers_to_dicts(plan.result.blockers),
    }


def _blockers_to_dicts(blockers: tuple[NotionBlocker, ...]):
    return tuple(
        {
            "code": blocker.code,
            "work_id": blocker.work_id,
            "work_title": blocker.work_title,
            "message": blocker.message,
            "severity": blocker.severity.value,
            "next_action": blocker.next_action.value,
        }
        for blocker in blockers
    )


def _normalize_work_ids(values):
    if not values:
        return []
    ordered = []
    seen = set()
    for value in values:
        try:
            work_id = int(value)
        except (TypeError, ValueError):
            continue
        if work_id <= 0 or work_id in seen:
            continue
        ordered.append(work_id)
        seen.add(work_id)
    return ordered


def _has_work_code(record):
    value = getattr(record, "work_code", None)
    return bool(str(value).strip()) if value is not None else False

from pathlib import Path

from manhwateca.flows.domain import (
    FlowError,
    FlowMessage,
    FlowWarning,
    Progress,
    StageExecution,
    StageId,
    StageResult,
    StageStatus,
    WorkflowExecution,
    WorkflowStatus,
)
from manhwateca.webapp.workflow import WorkflowManager


LEGACY_STAGE_GROUPS = {
    StageId.ORGANIZE_LIBRARY: ("previews", "organize"),
    StageId.CATALOG_WORKS: ("catalog",),
    StageId.RESOLVE_IDS: ("ids", "review_ids"),
    StageId.UPDATE_METADATA: ("details",),
    StageId.SYNC_NOTION: (
        "notion_catalog",
        "notion_catalog_apply",
        "notion_metadata",
        "notion_metadata_apply",
    ),
}


class LegacyWorkflowAdapter:
    """Adapter boundary for the current web workflow backend.

    This is the only new Fluxos layer that may know about WorkflowManager and
    its legacy step ids. Domain, Orchestrator and /api/flows must depend on this
    adapter contract, not on the legacy backend directly.
    """

    def __init__(self, project_root, manager=None):
        self.project_root = Path(project_root)
        self.manager = manager or WorkflowManager(self.project_root)

    def status(self) -> WorkflowExecution:
        return self._convert(self.manager.status())

    def start(self, stage: StageId | None = None) -> WorkflowExecution:
        selected = _legacy_steps_for(stage) if stage else None
        return self._convert(self.manager.start(selected=selected))

    def _convert(self, payload: dict) -> WorkflowExecution:
        run = payload.get("run", {})
        return WorkflowExecution(
            execution_id=run.get("execution_id") or run.get("started_at"),
            status=_workflow_status(run.get("status")),
            started_at=run.get("started_at"),
            finished_at=run.get("finished_at"),
            stages=tuple(
                _stage_execution(stage_id, run)
                for stage_id in LEGACY_STAGE_GROUPS
            ),
            warnings=_workflow_warnings(run),
            errors=_workflow_errors(run),
        )


def _legacy_steps_for(stage: StageId) -> list[str]:
    return list(LEGACY_STAGE_GROUPS[stage])


def _workflow_status(status: str | None) -> WorkflowStatus:
    return {
        None: WorkflowStatus.IDLE,
        "idle": WorkflowStatus.IDLE,
        "running": WorkflowStatus.RUNNING,
        "waiting_manual": WorkflowStatus.COMPLETED_WITH_WARNINGS,
        "completed": WorkflowStatus.COMPLETED,
        "failed": WorkflowStatus.FAILED,
        "interrupted": WorkflowStatus.FAILED,
        "cancelled": WorkflowStatus.CANCELLED,
    }.get(status, WorkflowStatus.FAILED)


def _stage_execution(stage_id: StageId, run: dict) -> StageExecution:
    results = run.get("results", {})
    legacy_steps = LEGACY_STAGE_GROUPS[stage_id]
    statuses = [
        results.get(step, {}).get("status")
        for step in legacy_steps
        if results.get(step)
    ]
    status = _stage_status(statuses, run.get("current"), legacy_steps)
    messages = []
    warnings = []
    errors = []
    for step in legacy_steps:
        result = results.get(step, {})
        messages.extend(
            FlowMessage(message=line)
            for line in result.get("messages", [])
            if line
        )
        note = result.get("note")
        if note:
            if result.get("status") == "manual":
                warnings.append(FlowWarning(message=note))
            else:
                messages.append(FlowMessage(message=note))
        if result.get("status") == "failed":
            errors.append(FlowError(message=note or "Etapa legada falhou."))
    return StageExecution(
        stage_id=stage_id,
        status=status,
        progress=_stage_progress(statuses, legacy_steps),
        result=StageResult(
            warnings=tuple(warnings),
            errors=tuple(errors),
        ),
        messages=tuple(messages),
    )


def _stage_status(
    statuses: list[str],
    current: str | None,
    legacy_steps: tuple[str, ...],
) -> StageStatus:
    if current in legacy_steps:
        return StageStatus.RUNNING
    if "failed" in statuses or "interrupted" in statuses:
        return StageStatus.FAILED
    if "manual" in statuses:
        return StageStatus.COMPLETED_WITH_WARNINGS
    if statuses and all(status == "completed" for status in statuses):
        return StageStatus.COMPLETED
    return StageStatus.WAITING


def _stage_progress(statuses: list[str], legacy_steps: tuple[str, ...]) -> Progress:
    finished = sum(
        1 for status in statuses
        if status in {"completed", "manual", "failed", "interrupted"}
    )
    return Progress(current=finished, total=len(legacy_steps))


def _workflow_warnings(run: dict) -> tuple[FlowWarning, ...]:
    if run.get("status") == "waiting_manual" and run.get("notification"):
        return (FlowWarning(message=run["notification"]),)
    return ()


def _workflow_errors(run: dict) -> tuple[FlowError, ...]:
    if run.get("status") in {"failed", "interrupted"}:
        return (FlowError(message=run.get("notification") or "Workflow falhou."),)
    return ()

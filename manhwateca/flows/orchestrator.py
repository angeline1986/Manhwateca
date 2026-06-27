from datetime import datetime
from uuid import uuid4

from manhwateca.flows.domain import (
    OFFICIAL_STAGE_DEFINITIONS,
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
from manhwateca.flows.integrations import FlowIntegrations
from manhwateca.flows.repository import FlowLogRecord
from manhwateca.flows.services import (
    StageService,
    default_stage_services,
)


class WorkflowOrchestrator:
    def __init__(
        self,
        repository,
        integrations: FlowIntegrations,
        stage_services: dict[StageId, StageService] | None = None,
        *,
        id_factory=None,
        clock=None,
    ):
        self.repository = repository
        self.integrations = integrations
        self.stage_services = stage_services or default_stage_services(integrations)
        self.id_factory = id_factory or (lambda: f"wf_{uuid4().hex}")
        self.clock = clock or _now

    def start(self) -> WorkflowExecution:
        active = self.repository.latest_execution()
        if active and active.status in {
            WorkflowStatus.VALIDATING,
            WorkflowStatus.RUNNING,
            WorkflowStatus.CANCELLING,
        }:
            raise RuntimeError("Já existe um Workflow ativo.")
        self._validate_global_dependencies()

        execution = WorkflowExecution(
            execution_id=self.id_factory(),
            status=WorkflowStatus.VALIDATING,
            started_at=self.clock(),
            stages=tuple(
                StageExecution(stage.id)
                for stage in OFFICIAL_STAGE_DEFINITIONS
            ),
        )
        self.repository.save_execution(execution)
        execution = self._with_status(execution, WorkflowStatus.RUNNING)
        self.repository.save_execution(execution)
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            operation="start",
            status=execution.status.value,
        ))

        for stage in OFFICIAL_STAGE_DEFINITIONS:
            execution = self.run_stage(stage.id, execution)
            if execution.status in {WorkflowStatus.FAILED, WorkflowStatus.CANCELLED}:
                return execution

        return self.finish(execution)

    def run_stage(
        self,
        stage_id: StageId,
        execution: WorkflowExecution | None = None,
    ) -> WorkflowExecution:
        execution = execution or self.get_status()
        if execution is None:
            raise RuntimeError("Nenhum Workflow iniciado.")
        service = self.stage_services[stage_id]
        execution = self._replace_stage(
            execution,
            StageExecution(stage_id, status=StageStatus.VALIDATING),
        )
        self.repository.save_execution(execution)

        warnings = service.validate()
        execution = self._replace_stage(
            execution,
            StageExecution(
                stage_id,
                status=StageStatus.RUNNING,
                messages=(FlowMessage("Etapa em processamento."),),
            ),
        )
        self.repository.save_execution(execution)

        try:
            result = service.finalize(service.execute())
        except Exception as error:
            result = StageResult(
                errors=(FlowError(message=str(error), code="FLOW_STAGE_FAILED"),)
            )

        if result.has_errors:
            status = StageStatus.FAILED
            workflow_status = WorkflowStatus.FAILED
        elif result.has_warnings or warnings:
            status = StageStatus.COMPLETED_WITH_WARNINGS
            workflow_status = WorkflowStatus.RUNNING
        else:
            status = StageStatus.COMPLETED
            workflow_status = WorkflowStatus.RUNNING

        merged_result = StageResult(
            processed=result.processed,
            skipped=result.skipped,
            warnings=(*warnings, *result.warnings),
            errors=result.errors,
            metrics=result.metrics,
        )
        execution = self._replace_stage(
            execution,
            StageExecution(
                stage_id,
                status=status,
                progress=Progress(current=1, total=1),
                result=merged_result,
            ),
        )
        execution = self._with_status(execution, workflow_status)
        self.repository.save_execution(execution)
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            stage=stage_id,
            operation="run_stage",
            status=status.value,
            processed=result.processed,
            error_code=(
                result.errors[0].code
                if result.errors and result.errors[0].code
                else None
            ),
        ))
        return execution

    def _validate_global_dependencies(self) -> None:
        validations = (
            self.integrations.database.validate(),
            self.integrations.library.validate(StageId.ORGANIZE_LIBRARY),
        )
        errors = [
            error.message
            for validation in validations
            if not validation.valid
            for error in validation.errors
        ]
        if errors:
            raise RuntimeError("; ".join(errors))

    def cancel(self) -> WorkflowExecution:
        execution = self.get_status()
        if execution is None:
            raise RuntimeError("Nenhum Workflow iniciado.")
        execution = self._with_status(
            execution,
            WorkflowStatus.CANCELLED,
            finished_at=self.clock(),
        )
        self.repository.save_execution(execution)
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            operation="cancel",
            status=execution.status.value,
        ))
        return execution

    def get_status(self) -> WorkflowExecution | None:
        return self.repository.latest_execution()

    def finish(self, execution: WorkflowExecution | None = None) -> WorkflowExecution:
        execution = execution or self.get_status()
        if execution is None:
            raise RuntimeError("Nenhum Workflow iniciado.")
        status = (
            WorkflowStatus.COMPLETED_WITH_WARNINGS
            if execution.has_warnings
            else WorkflowStatus.COMPLETED
        )
        execution = self._with_status(
            execution,
            status,
            finished_at=self.clock(),
        )
        self.repository.save_execution(execution)
        self.repository.save_summary(
            execution.execution_id,
            {
                "stages": len(execution.stages),
                "progressPercent": execution.progress.percent,
            },
            warnings_count=sum(
                len(stage.result.warnings)
                for stage in execution.stages
                if stage.result
            ),
            errors_count=sum(
                len(stage.result.errors)
                for stage in execution.stages
                if stage.result
            ),
        )
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            operation="finish",
            status=execution.status.value,
        ))
        return execution

    def _replace_stage(
        self,
        execution: WorkflowExecution,
        replacement: StageExecution,
    ) -> WorkflowExecution:
        stages = tuple(
            replacement if stage.stage_id == replacement.stage_id else stage
            for stage in execution.stages
        )
        return WorkflowExecution(
            execution_id=execution.execution_id,
            status=execution.status,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            stages=stages,
            warnings=execution.warnings,
            errors=execution.errors,
        )

    def _with_status(
        self,
        execution: WorkflowExecution,
        status: WorkflowStatus,
        *,
        finished_at: str | None = None,
    ) -> WorkflowExecution:
        return WorkflowExecution(
            execution_id=execution.execution_id,
            status=status,
            started_at=execution.started_at,
            finished_at=finished_at or execution.finished_at,
            stages=execution.stages,
            warnings=execution.warnings,
            errors=execution.errors,
        )


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")

from datetime import datetime
import logging
from time import perf_counter
from uuid import uuid4

from manhwateca.audit.models import (
    AuditEvent,
    AuditModule,
    AuditSeverity,
    AuditStatus,
)
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


logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    def __init__(
        self,
        repository,
        integrations: FlowIntegrations,
        stage_services: dict[StageId, StageService] | None = None,
        *,
        id_factory=None,
        clock=None,
        audit_service=None,
        on_started=None,
        on_stage_started=None,
    ):
        self.repository = repository
        self.integrations = integrations
        self.stage_services = stage_services or default_stage_services(integrations)
        self.id_factory = id_factory or (lambda: f"wf_{uuid4().hex}")
        self.clock = clock or _now
        self.audit_service = audit_service
        self.on_started = on_started
        self.on_stage_started = on_stage_started

    def start(self) -> WorkflowExecution:
        active = self.repository.latest_execution()
        if active and active.status in {
            WorkflowStatus.VALIDATING,
            WorkflowStatus.RUNNING,
            WorkflowStatus.CANCELLING,
        }:
            raise RuntimeError("Já existe um Workflow ativo.")
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
        try:
            self._validate_global_dependencies()
        except Exception as error:
            execution = self._with_status(
                WorkflowExecution(
                    execution_id=execution.execution_id,
                    status=execution.status,
                    started_at=execution.started_at,
                    stages=execution.stages,
                    errors=(FlowError(str(error), code="FLOW_VALIDATION_FAILED"),),
                ),
                WorkflowStatus.FAILED,
                finished_at=self.clock(),
            )
            self.repository.save_execution(execution)
            self._persist_final_summary(execution)
            self.repository.append_log(FlowLogRecord(
                execution_id=execution.execution_id,
                operation="start",
                status=execution.status.value,
                error_code="FLOW_VALIDATION_FAILED",
                message="Workflow falhou na validação inicial.",
            ))
            self._audit(
                "workflow.fail",
                execution,
                status=AuditStatus.ERROR.value,
                severity=AuditSeverity.ERROR.value,
                message="Workflow falhou na validação inicial.",
            )
            self._notify_started()
            return execution
        execution = self._with_status(execution, WorkflowStatus.RUNNING)
        self.repository.save_execution(execution)
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            operation="start",
            status=execution.status.value,
            message="Workflow iniciado.",
        ))
        self._audit(
            "workflow.start",
            execution,
            message="Workflow iniciado.",
            details={"current_stage": _current_stage_id(execution)},
        )

        for stage in OFFICIAL_STAGE_DEFINITIONS:
            execution = self.run_stage(stage.id, execution)
            if execution.status in {WorkflowStatus.FAILED, WorkflowStatus.CANCELLED}:
                return execution

        return self.finish(execution)

    def run_stage(
        self,
        stage_id: StageId,
        execution: WorkflowExecution | None = None,
        *,
        finish_after_stage: bool = False,
        payload: dict | None = None,
    ) -> WorkflowExecution:
        execution = execution or self.get_status()
        if execution is None:
            raise RuntimeError("Nenhum Workflow iniciado.")
        service = self.stage_services[stage_id]
        execution = self._replace_stage(
            execution,
            StageExecution(
                stage_id,
                status=StageStatus.VALIDATING,
                started_at=self.clock(),
                messages=(FlowMessage("Etapa em validação."),),
            ),
        )
        self.repository.save_execution(execution)
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            stage=stage_id,
            operation="stage_start",
            status=StageStatus.VALIDATING.value,
            message="Etapa iniciada.",
        ))
        self._audit(
            "workflow.stage.start",
            execution,
            message="Etapa iniciada.",
            details={"stage": stage_id.value},
        )

        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            stage=stage_id,
            operation="stage_validate_start",
            status=StageStatus.VALIDATING.value,
            message="Validação da etapa iniciada.",
        ))
        warnings = service.validate()
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            stage=stage_id,
            operation="stage_validate_finish",
            status=StageStatus.VALIDATING.value,
            message="Validação da etapa concluída.",
            details={"warnings": len(warnings)},
        ))
        stage_started_at = self._stage_started_at(execution, stage_id)
        execution = self._replace_stage(
            execution,
            StageExecution(
                stage_id,
                status=StageStatus.RUNNING,
                started_at=stage_started_at,
                progress=Progress(current=0, total=1),
                messages=(FlowMessage("Etapa em processamento."),),
            ),
        )
        self.repository.save_execution(execution)
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            stage=stage_id,
            operation="stage_running_persisted",
            status=StageStatus.RUNNING.value,
            message="Status running persistido para a etapa.",
        ))
        self._notify_stage_started()

        service_started_at = perf_counter()
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            stage=stage_id,
            operation="stage_execute_start",
            status=StageStatus.RUNNING.value,
            message="Execução do serviço da etapa iniciada.",
            details={"service": service.__class__.__name__},
        ))
        try:
            stage_kwargs = {}
            if stage_id == StageId.UPDATE_METADATA and payload:
                stage_kwargs["selected_ids"] = payload.get("selected_ids")
            result = service.finalize(service.execute(**stage_kwargs))
        except Exception as error:
            result = StageResult(
                errors=(FlowError(message=str(error), code="FLOW_STAGE_FAILED"),)
            )
            self.repository.append_log(FlowLogRecord(
                execution_id=execution.execution_id,
                stage=stage_id,
                operation="stage_execute_error",
                status=StageStatus.FAILED.value,
                duration=perf_counter() - service_started_at,
                error_code="FLOW_STAGE_FAILED",
                message=str(error),
                details={"service": service.__class__.__name__},
            ))
        else:
            self.repository.append_log(FlowLogRecord(
                execution_id=execution.execution_id,
                stage=stage_id,
                operation="stage_execute_finish",
                status=StageStatus.RUNNING.value,
                duration=perf_counter() - service_started_at,
                processed=result.processed,
                message="Execução do serviço da etapa concluída.",
                details={
                    "service": service.__class__.__name__,
                    "warnings": len(result.warnings),
                    "errors": len(result.errors),
                    "metrics": result.metrics,
                },
            ))

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
            inventory=result.inventory,
            metrics=result.metrics,
        )
        if stage_id == StageId.ORGANIZE_LIBRARY and merged_result.inventory:
            self.repository.save_inventory(
                execution.execution_id,
                merged_result.inventory,
            )
        execution = self._replace_stage(
            execution,
            StageExecution(
                stage_id,
                status=status,
                progress=Progress(current=1, total=1),
                result=merged_result,
                started_at=stage_started_at,
                finished_at=self.clock(),
            ),
        )
        if finish_after_stage:
            execution = self._reset_following_stages(execution, stage_id)
        execution = self._with_status(
            execution,
            workflow_status,
            finished_at=(
                self.clock()
                if workflow_status == WorkflowStatus.FAILED
                else None
            ),
        )
        self.repository.save_execution(execution)
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            stage=stage_id,
            operation="stage_result_persisted",
            status=status.value,
            processed=result.processed,
            error_code=(
                result.errors[0].code
                if result.errors and result.errors[0].code
                else None
            ),
            message="Resultado final da etapa persistido.",
        ))
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
            message="Etapa finalizada.",
        ))
        self._audit(
            "workflow.stage.finish",
            execution,
            status=_audit_status_for_workflow(execution.status),
            severity=_audit_severity_for_workflow(execution.status),
            message="Etapa finalizada.",
            details={
                "stage": stage_id.value,
                "stage_status": status.value,
                "processed": result.processed,
            },
        )
        if workflow_status == WorkflowStatus.FAILED:
            self._persist_final_summary(execution)
            self._audit(
                "workflow.fail",
                execution,
                status=AuditStatus.ERROR.value,
                severity=AuditSeverity.ERROR.value,
                message="Workflow falhou.",
                details={"stage": stage_id.value},
            )
        elif finish_after_stage:
            return self.finish(execution)
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
        execution = self._cancel_running_stage(execution)
        execution = self._with_status(
            execution,
            WorkflowStatus.CANCELLED,
            finished_at=self.clock(),
        )
        self.repository.save_execution(execution)
        self._persist_final_summary(execution)
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            operation="cancel",
            status=execution.status.value,
            message="Workflow cancelado.",
        ))
        self._audit(
            "workflow.cancel",
            execution,
            message="Workflow cancelado.",
        )
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
        self._persist_final_summary(execution)
        self.repository.append_log(FlowLogRecord(
            execution_id=execution.execution_id,
            operation="finish",
            status=execution.status.value,
            message="Workflow finalizado.",
        ))
        self._audit(
            "workflow.finish",
            execution,
            status=_audit_status_for_workflow(execution.status),
            severity=_audit_severity_for_workflow(execution.status),
            message="Workflow finalizado.",
            details={"final_status": execution.status.value},
        )
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

    def _reset_following_stages(
        self,
        execution: WorkflowExecution,
        stage_id: StageId,
    ) -> WorkflowExecution:
        seen_current = False
        stages = []
        for stage in execution.stages:
            if stage.stage_id == stage_id:
                seen_current = True
                stages.append(stage)
                continue
            if seen_current:
                stages.append(StageExecution(stage.stage_id))
                continue
            stages.append(stage)
        return WorkflowExecution(
            execution_id=execution.execution_id,
            status=execution.status,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            stages=tuple(stages),
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
        terminal_statuses = {
            WorkflowStatus.CANCELLED,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.COMPLETED_WITH_WARNINGS,
            WorkflowStatus.FAILED,
        }
        final_finished_at = (
            finished_at or execution.finished_at
            if status in terminal_statuses
            else None
        )
        return WorkflowExecution(
            execution_id=execution.execution_id,
            status=status,
            started_at=execution.started_at,
            finished_at=final_finished_at,
            stages=execution.stages,
            warnings=execution.warnings,
            errors=execution.errors,
        )

    def _stage_started_at(
        self,
        execution: WorkflowExecution,
        stage_id: StageId,
    ) -> str | None:
        for stage in execution.stages:
            if stage.stage_id == stage_id:
                return stage.started_at
        return None

    def _cancel_running_stage(
        self,
        execution: WorkflowExecution,
    ) -> WorkflowExecution:
        current_stage = execution.current_stage
        if current_stage is None:
            return execution
        return self._replace_stage(
            execution,
            StageExecution(
                current_stage.stage_id,
                status=StageStatus.CANCELLED,
                progress=current_stage.progress,
                result=current_stage.result,
                current_item=current_stage.current_item,
                messages=(
                    *current_stage.messages,
                    FlowMessage("Etapa cancelada."),
                ),
                started_at=current_stage.started_at,
                finished_at=self.clock(),
            ),
        )

    def _persist_final_summary(self, execution: WorkflowExecution) -> None:
        self.repository.save_summary(
            execution.execution_id,
            {
                "status": execution.status.value,
                "stages": len(execution.stages),
                "finishedStages": execution.progress.current,
                "progressPercent": execution.progress.percent,
            },
            warnings_count=sum(
                len(stage.result.warnings)
                for stage in execution.stages
                if stage.result
            ) + len(execution.warnings),
            errors_count=sum(
                len(stage.result.errors)
                for stage in execution.stages
                if stage.result
            ) + len(execution.errors),
            warnings=[
                _message_dict(warning, stage.stage_id.value)
                for stage in execution.stages
                if stage.result
                for warning in stage.result.warnings
            ] + [_message_dict(warning, None) for warning in execution.warnings],
            errors=[
                _message_dict(error, stage.stage_id.value)
                for stage in execution.stages
                if stage.result
                for error in stage.result.errors
            ] + [_message_dict(error, None) for error in execution.errors],
        )

    def _audit(
        self,
        action: str,
        execution: WorkflowExecution,
        *,
        status: str = AuditStatus.SUCCESS.value,
        severity: str = AuditSeverity.INFO.value,
        message: str | None = None,
        details: dict | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        try:
            self.audit_service.record(AuditEvent(
                module=AuditModule.FLOWS.value,
                action=action,
                entity_type="workflow_execution",
                entity_id=execution.execution_id,
                status=status,
                severity=severity,
                message=message,
                details=details or {},
            ))
        except Exception:
            logger.exception("Falha ao gravar auditoria de Fluxos.")

    def _notify_started(self) -> None:
        if self.on_started:
            self.on_started()

    def _notify_stage_started(self) -> None:
        if self.on_stage_started:
            self.on_stage_started()


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _current_stage_id(execution: WorkflowExecution) -> str | None:
    return (
        execution.current_stage.stage_id.value
        if execution.current_stage else None
    )


def _audit_status_for_workflow(status: WorkflowStatus) -> str:
    if status == WorkflowStatus.FAILED:
        return AuditStatus.ERROR.value
    if status == WorkflowStatus.COMPLETED_WITH_WARNINGS:
        return AuditStatus.WARNING.value
    return AuditStatus.SUCCESS.value


def _audit_severity_for_workflow(status: WorkflowStatus) -> str:
    if status == WorkflowStatus.FAILED:
        return AuditSeverity.ERROR.value
    if status == WorkflowStatus.COMPLETED_WITH_WARNINGS:
        return AuditSeverity.WARNING.value
    return AuditSeverity.INFO.value


def _message_dict(message: FlowMessage, stage: str | None) -> dict:
    return {
        "stage": stage,
        "message": message.message,
        "code": message.code,
        "details": message.details,
    }

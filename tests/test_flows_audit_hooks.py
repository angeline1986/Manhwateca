import logging
import unittest
from contextlib import contextmanager

from manhwateca.flows.api import FlowController
from manhwateca.flows.domain import (
    FlowError,
    StageExecution,
    StageId,
    StageResult,
    StageStatus,
    WorkflowExecution,
    WorkflowStatus,
)
from manhwateca.flows.integrations import (
    FlowIntegrations,
    IntegrationCheck,
    IntegrationStatus,
    IntegrationValidation,
)
from manhwateca.flows.orchestrator import WorkflowOrchestrator


class FlowAuditHookTests(unittest.TestCase):
    def test_post_start_records_requested_event(self):
        audit = FakeAuditService()
        controller = FlowController(FakeBackend(), audit_service=audit)

        controller.handle_post("/api/flows/start", {})

        self.assertEqual(["workflow.start_requested"], audit.actions())

    def test_get_status_does_not_record_audit_event(self):
        audit = FakeAuditService()
        controller = FlowController(FakeBackend(), audit_service=audit)

        controller.handle_get("/api/flows/status")

        self.assertEqual([], audit.events)

    def test_post_stage_run_records_requested_event(self):
        audit = FakeAuditService()
        controller = FlowController(FakeBackend(), audit_service=audit)

        controller.handle_post("/api/flows/stages/resolve_ids/run", {})

        self.assertEqual(["workflow.stage.start_requested"], audit.actions())
        self.assertEqual("resolve_ids", audit.events[0].details["stage"])

    def test_orchestrator_start_records_fact_events(self):
        audit = FakeAuditService()
        orchestrator = WorkflowOrchestrator(
            FakeRepository(),
            fake_integrations(),
            stage_services={
                stage: FakeStageService(processed=1)
                for stage in StageId
            },
            id_factory=lambda: "wf_1",
            audit_service=audit,
        )

        orchestrator.start()

        actions = audit.actions()
        self.assertIn("workflow.start", actions)
        self.assertIn("workflow.stage.start", actions)
        self.assertIn("workflow.stage.finish", actions)
        self.assertIn("workflow.finish", actions)

    def test_orchestrator_run_stage_records_start_and_finish(self):
        audit = FakeAuditService()
        repository = FakeRepository.with_execution()
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            stage_services={StageId.RESOLVE_IDS: FakeStageService(processed=2)},
            audit_service=audit,
        )

        orchestrator.run_stage(StageId.RESOLVE_IDS)

        self.assertEqual(
            ["workflow.stage.start", "workflow.stage.finish"],
            audit.actions(),
        )

    def test_orchestrator_cancel_records_cancel(self):
        audit = FakeAuditService()
        repository = FakeRepository.with_execution(
            running_stage=StageId.CATALOG_WORKS
        )
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            audit_service=audit,
        )

        orchestrator.cancel()

        self.assertEqual(["workflow.cancel"], audit.actions())

    def test_failed_stage_records_error_audit(self):
        audit = FakeAuditService()
        repository = FakeRepository.with_execution()
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            stage_services={
                StageId.RESOLVE_IDS: FakeStageService(
                    error=FlowError("Falha.")
                )
            },
            audit_service=audit,
        )

        orchestrator.run_stage(StageId.RESOLVE_IDS)

        fail = [event for event in audit.events if event.action == "workflow.fail"][0]
        self.assertEqual("error", fail.status)
        self.assertEqual("error", fail.severity)

    def test_audit_failure_does_not_break_controller_operation(self):
        with disabled_logging():
            payload, status = FlowController(
                FakeBackend(),
                audit_service=FailingAuditService(),
            ).handle_post("/api/flows/start", {})

        self.assertEqual(202, status)
        self.assertTrue(payload["success"])

    def test_audit_failure_does_not_break_orchestrator_operation(self):
        orchestrator = WorkflowOrchestrator(
            FakeRepository(),
            fake_integrations(),
            stage_services={
                stage: FakeStageService(processed=1)
                for stage in StageId
            },
            id_factory=lambda: "wf_1",
            audit_service=FailingAuditService(),
        )

        with disabled_logging():
            execution = orchestrator.start()

        self.assertEqual(WorkflowStatus.COMPLETED, execution.status)


class FakeAuditService:
    def __init__(self):
        self.events = []

    def record(self, event):
        self.events.append(event)
        return len(self.events)

    def actions(self):
        return [event.action for event in self.events]


class FailingAuditService:
    def record(self, event):
        raise RuntimeError("audit unavailable")


class FakeBackend:
    def start(self):
        return execution(WorkflowStatus.RUNNING)

    def get_status(self):
        return execution(WorkflowStatus.RUNNING)

    def run_stage(self, stage):
        return execution(WorkflowStatus.RUNNING)


class FakeStageService:
    def __init__(self, processed=0, error=None):
        self.processed = processed
        self.error = error

    def validate(self):
        return ()

    def execute(self):
        if self.error:
            return StageResult(errors=(self.error,))
        return StageResult(processed=self.processed)

    def finalize(self, result):
        return result


class FakeRepository:
    def __init__(self):
        self.execution = None
        self.logs = []
        self.summary = None

    @classmethod
    def with_execution(cls, running_stage=None):
        repository = cls()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=tuple(
                StageExecution(
                    stage,
                    status=(
                        StageStatus.RUNNING
                        if stage == running_stage
                        else StageStatus.WAITING
                    ),
                )
                for stage in StageId
            ),
        ))
        return repository

    def latest_execution(self):
        return self.execution

    def save_execution(self, execution):
        self.execution = execution

    def append_log(self, record):
        self.logs.append(record)

    def save_summary(self, execution_id, metrics, **kwargs):
        self.summary = {
            "execution_id": execution_id,
            "metrics": metrics,
            **kwargs,
        }


class FakeIntegration:
    def check_status(self):
        return IntegrationCheck("fake", IntegrationStatus.OPERATIONAL)

    def validate(self, stage=None):
        return IntegrationValidation(stage=stage, valid=True)


def fake_integrations():
    integration = FakeIntegration()
    return FlowIntegrations(
        database=integration,
        library=integration,
        mangaupdates=integration,
        notion=integration,
    )


def execution(status):
    return WorkflowExecution(
        execution_id="wf_1",
        status=status,
        stages=(
            StageExecution(
                StageId.ORGANIZE_LIBRARY,
                status=StageStatus.RUNNING,
            ),
        ),
    )


@contextmanager
def disabled_logging():
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(previous)


if __name__ == "__main__":
    unittest.main()

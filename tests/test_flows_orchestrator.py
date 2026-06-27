import unittest

from manhwateca.flows.domain import (
    FlowError,
    FlowWarning,
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


class WorkflowOrchestratorTests(unittest.TestCase):
    def test_start_runs_official_stages_and_finishes(self):
        repository = FakeRepository()
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            stage_services={
                stage: FakeStageService(processed=1)
                for stage in StageId
            },
            id_factory=lambda: "wf_1",
            clock=lambda: "2026-06-27T10:00:00-03:00",
        )

        execution = orchestrator.start()

        self.assertEqual(WorkflowStatus.COMPLETED, execution.status)
        self.assertEqual([stage for stage in StageId], [
            stage.stage_id for stage in execution.stages
        ])
        self.assertTrue(all(
            stage.status == StageStatus.COMPLETED
            for stage in execution.stages
        ))
        self.assertEqual(100, execution.progress.percent)
        self.assertEqual("wf_1", repository.summary_execution_id)

    def test_run_stage_records_failure_without_legacy_imports(self):
        repository = FakeRepository()
        execution = WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=tuple(FakeRepository.initial_stages()),
        )
        repository.save_execution(execution)
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            stage_services={
                StageId.RESOLVE_IDS: FakeStageService(
                    error=FlowError("Falha ao comunicar com MangaUpdates.")
                )
            },
        )

        result = orchestrator.run_stage(StageId.RESOLVE_IDS)

        self.assertEqual(WorkflowStatus.FAILED, result.status)
        resolve_ids = [
            stage for stage in result.stages
            if stage.stage_id == StageId.RESOLVE_IDS
        ][0]
        self.assertEqual(StageStatus.FAILED, resolve_ids.status)
        self.assertTrue(resolve_ids.result.has_errors)

    def test_cancel_marks_current_execution_cancelled(self):
        repository = FakeRepository()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=tuple(FakeRepository.initial_stages()),
        ))
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            clock=lambda: "2026-06-27T10:05:00-03:00",
        )

        execution = orchestrator.cancel()

        self.assertEqual(WorkflowStatus.CANCELLED, execution.status)
        self.assertEqual("2026-06-27T10:05:00-03:00", execution.finished_at)

    def test_active_workflow_blocks_new_start(self):
        repository = FakeRepository()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=tuple(FakeRepository.initial_stages()),
        ))
        orchestrator = WorkflowOrchestrator(repository, fake_integrations())

        with self.assertRaises(RuntimeError):
            orchestrator.start()

    def test_invalid_global_dependency_blocks_start(self):
        repository = FakeRepository()
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(valid=False),
        )

        with self.assertRaisesRegex(RuntimeError, "PostgreSQL indisponível"):
            orchestrator.start()
        self.assertIsNone(repository.latest_execution())


class FakeStageService:
    def __init__(self, processed=0, warning=None, error=None):
        self.processed = processed
        self.warning = warning
        self.error = error

    def validate(self):
        return (self.warning,) if self.warning else ()

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
        self.summary_execution_id = None

    @staticmethod
    def initial_stages():
        from manhwateca.flows.domain import StageExecution
        return [StageExecution(stage) for stage in StageId]

    def latest_execution(self):
        return self.execution

    def save_execution(self, execution):
        self.execution = execution

    def append_log(self, record):
        self.logs.append(record)

    def save_summary(self, execution_id, metrics, **_kwargs):
        self.summary_execution_id = execution_id
        self.summary_metrics = metrics


class FakeIntegration:
    def __init__(self, valid=True):
        self.valid = valid

    def check_status(self):
        return IntegrationCheck(
            "fake",
            IntegrationStatus.OPERATIONAL
            if self.valid
            else IntegrationStatus.UNAVAILABLE,
        )

    def validate(self, stage=None):
        return IntegrationValidation(
            stage=stage,
            valid=self.valid,
            errors=() if self.valid else (
                FlowError("PostgreSQL indisponível."),
            ),
        )


def fake_integrations(valid=True):
    fake = FakeIntegration(valid=valid)
    return FlowIntegrations(
        database=fake,
        library=fake,
        mangaupdates=fake,
        notion=fake,
    )


if __name__ == "__main__":
    unittest.main()

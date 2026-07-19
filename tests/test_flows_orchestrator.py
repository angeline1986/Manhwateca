import unittest

from manhwateca.flows.domain import (
    FlowError,
    FlowWarning,
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
    LibraryInventoryItem,
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
        self.assertEqual("completed", repository.summary_metrics["status"])
        self.assertTrue(all(stage.started_at for stage in execution.stages))
        self.assertTrue(all(stage.finished_at for stage in execution.stages))
        self.assertIn("start", [log.operation for log in repository.logs])
        self.assertIn("finish", [log.operation for log in repository.logs])

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
        self.assertEqual("wf_1", repository.summary_execution_id)
        self.assertEqual("failed", repository.summary_metrics["status"])
        self.assertEqual(1, repository.summary_errors_count)
        self.assertIsNotNone(result.finished_at)

    def test_organize_stage_persists_inventory_for_next_stage(self):
        repository = FakeRepository()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=tuple(FakeRepository.initial_stages()),
        ))
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            stage_services={
                StageId.ORGANIZE_LIBRARY: FakeStageService(
                    processed=1,
                    inventory=(
                        LibraryInventoryItem(
                            name="Obra A",
                            source_path="/library/Obra A",
                        ),
                    ),
                )
            },
        )

        orchestrator.run_stage(StageId.ORGANIZE_LIBRARY)

        self.assertEqual("wf_1", repository.inventory_execution_id)
        self.assertEqual("Obra A", repository.inventory[0].name)

    def test_cancel_marks_current_execution_cancelled(self):
        repository = FakeRepository()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=(
                *FakeRepository.initial_stages(
                    running_stage=StageId.CATALOG_WORKS
                ),
            ),
        ))
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            clock=lambda: "2026-06-27T10:05:00-03:00",
        )

        execution = orchestrator.cancel()

        self.assertEqual(WorkflowStatus.CANCELLED, execution.status)
        self.assertEqual("2026-06-27T10:05:00-03:00", execution.finished_at)
        catalog_works = [
            stage for stage in execution.stages
            if stage.stage_id == StageId.CATALOG_WORKS
        ][0]
        self.assertEqual(StageStatus.CANCELLED, catalog_works.status)
        self.assertEqual("2026-06-27T10:05:00-03:00", catalog_works.finished_at)
        self.assertEqual("cancelled", repository.summary_metrics["status"])

    def test_finish_with_warning_generates_completed_with_warnings_summary(self):
        repository = FakeRepository()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=(
                StageExecution(
                    StageId.ORGANIZE_LIBRARY,
                    status=StageStatus.COMPLETED_WITH_WARNINGS,
                    result=StageResult(
                        warnings=(FlowWarning("Inconsistência registrada."),)
                    ),
                ),
            ),
        ))
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            clock=lambda: "2026-06-27T10:05:00-03:00",
        )

        execution = orchestrator.finish()

        self.assertEqual(WorkflowStatus.COMPLETED_WITH_WARNINGS, execution.status)
        self.assertEqual("completed_with_warnings", repository.summary_metrics["status"])
        self.assertEqual(1, repository.summary_warnings_count)

    def test_single_stage_with_warning_finishes_workflow(self):
        repository = FakeRepository()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            finished_at="2026-06-27T09:00:00-03:00",
            stages=tuple(FakeRepository.initial_stages()),
        ))
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            stage_services={
                StageId.RESOLVE_IDS: FakeStageService(
                    processed=1,
                    warning=FlowWarning("Resolução de IDs concluída com pendências."),
                )
            },
            clock=lambda: "2026-06-27T10:05:00-03:00",
        )

        execution = orchestrator.run_stage(
            StageId.RESOLVE_IDS,
            finish_after_stage=True,
        )

        self.assertEqual(WorkflowStatus.COMPLETED_WITH_WARNINGS, execution.status)
        self.assertEqual("2026-06-27T10:05:00-03:00", execution.finished_at)
        self.assertEqual("completed_with_warnings", repository.summary_metrics["status"])
        resolve_ids = [
            stage for stage in execution.stages
            if stage.stage_id == StageId.RESOLVE_IDS
        ][0]
        update_metadata = [
            stage for stage in execution.stages
            if stage.stage_id == StageId.UPDATE_METADATA
        ][0]
        self.assertEqual(StageStatus.COMPLETED_WITH_WARNINGS, resolve_ids.status)
        self.assertEqual(StageStatus.WAITING, update_metadata.status)

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
            id_factory=lambda: "wf_1",
            clock=lambda: "2026-06-27T10:05:00-03:00",
        )

        execution = orchestrator.start()

        self.assertEqual(WorkflowStatus.FAILED, execution.status)
        self.assertEqual("wf_1", repository.latest_execution().execution_id)
        self.assertEqual("2026-06-27T10:05:00-03:00", execution.finished_at)
        self.assertTrue(execution.errors)
        self.assertEqual("failed", repository.summary_metrics["status"])

    def test_sync_notion_receives_scope_from_update_metadata_result(self):
        repository = FakeRepository()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=(
                StageExecution(
                    StageId.UPDATE_METADATA,
                    status=StageStatus.COMPLETED,
                    result=StageResult(metrics={"processed_work_ids": [259, "259", None]}),
                ),
                *[
                    stage for stage in FakeRepository.initial_stages()
                    if stage.stage_id != StageId.UPDATE_METADATA
                ],
            ),
        ))
        sync_service = FakeStageService()
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            stage_services={StageId.SYNC_NOTION: sync_service},
        )

        orchestrator.run_stage(StageId.SYNC_NOTION)

        self.assertEqual({"work_ids": [259]}, sync_service.last_kwargs)

    def test_sync_notion_explicit_work_ids_have_priority_over_journey_scope(self):
        repository = FakeRepository()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=(
                StageExecution(
                    StageId.UPDATE_METADATA,
                    status=StageStatus.COMPLETED,
                    result=StageResult(metrics={"processed_work_ids": [259]}),
                ),
                *[
                    stage for stage in FakeRepository.initial_stages()
                    if stage.stage_id != StageId.UPDATE_METADATA
                ],
            ),
        ))
        sync_service = FakeStageService()
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            stage_services={StageId.SYNC_NOTION: sync_service},
        )

        orchestrator.run_stage(
            StageId.SYNC_NOTION,
            payload={"work_ids": [4, "4", 1]},
        )

        self.assertEqual({"work_ids": [4, 1]}, sync_service.last_kwargs)

    def test_sync_notion_rejects_selected_ids_contract(self):
        repository = FakeRepository()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=tuple(FakeRepository.initial_stages()),
        ))
        sync_service = FakeStageService()
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            stage_services={StageId.SYNC_NOTION: sync_service},
        )

        result = orchestrator.run_stage(
            StageId.SYNC_NOTION,
            payload={"selected_ids": [259]},
        )

        sync_stage = [
            stage for stage in result.stages
            if stage.stage_id == StageId.SYNC_NOTION
        ][0]
        self.assertEqual(StageStatus.FAILED, sync_stage.status)
        self.assertIsNone(sync_service.last_kwargs)
        self.assertIn("work_ids", sync_stage.result.errors[0].message)

    def test_sync_notion_rejects_invalid_work_ids_payload(self):
        repository = FakeRepository()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=tuple(FakeRepository.initial_stages()),
        ))
        sync_service = FakeStageService()
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            stage_services={StageId.SYNC_NOTION: sync_service},
        )

        result = orchestrator.run_stage(
            StageId.SYNC_NOTION,
            payload={"work_ids": "259"},
        )

        sync_stage = [
            stage for stage in result.stages
            if stage.stage_id == StageId.SYNC_NOTION
        ][0]
        self.assertEqual(StageStatus.FAILED, sync_stage.status)
        self.assertIsNone(sync_service.last_kwargs)
        self.assertIn("work_ids deve ser uma lista", sync_stage.result.errors[0].message)

    def test_sync_notion_without_update_metadata_scope_receives_empty_scope(self):
        repository = FakeRepository()
        repository.save_execution(WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            stages=tuple(FakeRepository.initial_stages()),
        ))
        sync_service = FakeStageService()
        orchestrator = WorkflowOrchestrator(
            repository,
            fake_integrations(),
            stage_services={StageId.SYNC_NOTION: sync_service},
        )

        orchestrator.run_stage(StageId.SYNC_NOTION)

        self.assertEqual({"work_ids": []}, sync_service.last_kwargs)


class FakeStageService:
    def __init__(self, processed=0, warning=None, error=None, inventory=()):
        self.processed = processed
        self.warning = warning
        self.error = error
        self.inventory = inventory
        self.last_kwargs = None

    def validate(self):
        return (self.warning,) if self.warning else ()

    def execute(self, **kwargs):
        self.last_kwargs = kwargs
        if self.error:
            return StageResult(errors=(self.error,))
        return StageResult(processed=self.processed, inventory=self.inventory)

    def finalize(self, result):
        return result


class FakeRepository:
    def __init__(self):
        self.execution = None
        self.logs = []
        self.summary_execution_id = None
        self.summary_metrics = {}
        self.summary_warnings_count = 0
        self.summary_errors_count = 0
        self.inventory_execution_id = None
        self.inventory = ()

    @staticmethod
    def initial_stages(running_stage=None):
        from manhwateca.flows.domain import StageExecution
        return [
            StageExecution(
                stage,
                status=(
                    StageStatus.RUNNING
                    if stage == running_stage
                    else StageStatus.WAITING
                ),
                started_at=(
                    "2026-06-27T10:00:00-03:00"
                    if stage == running_stage
                    else None
                ),
            )
            for stage in StageId
        ]

    def latest_execution(self):
        return self.execution

    def save_execution(self, execution):
        self.execution = execution

    def append_log(self, record):
        self.logs.append(record)

    def save_summary(
        self,
        execution_id,
        metrics,
        warnings_count=0,
        errors_count=0,
        warnings=None,
        errors=None,
    ):
        self.summary_execution_id = execution_id
        self.summary_metrics = metrics
        self.summary_warnings_count = warnings_count
        self.summary_errors_count = errors_count

    def save_inventory(self, execution_id, inventory):
        self.inventory_execution_id = execution_id
        self.inventory = inventory


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

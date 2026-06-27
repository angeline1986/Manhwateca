import unittest

from manhwateca.flows.domain import (
    StageExecution,
    StageId,
    StageStatus,
    WorkflowExecution,
    WorkflowStatus,
)
from manhwateca.flows.runtime import OfficialFlowBackend


class OfficialFlowBackendTests(unittest.TestCase):
    def test_get_status_reads_repository_factory(self):
        repository = FakeRepository()
        repository.execution = WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
        )
        backend = OfficialFlowBackend(
            repository_factory=lambda: repository,
            integrations=FakeIntegrations(),
        )

        execution = backend.get_status()

        self.assertEqual("wf_1", execution.execution_id)

    def test_start_returns_persisted_running_execution_from_repository(self):
        repository = FakeRepository()
        backend = OfficialFlowBackend(
            repository_factory=lambda: repository,
            integrations=FakeIntegrations(),
            start_timeout=1,
        )

        execution = backend.start()

        self.assertEqual(WorkflowStatus.RUNNING, execution.status)
        self.assertEqual(StageStatus.RUNNING, execution.current_stage.status)


class FakeRepository:
    def __init__(self):
        self.execution = None

    def latest_execution(self):
        return self.execution

    def list_history(self):
        return [self.execution] if self.execution else []

    def save_execution(self, execution):
        self.execution = execution

    def append_log(self, record):
        pass

    def save_summary(self, execution_id, metrics, **kwargs):
        pass


class FakeIntegrations:
    def __init__(self):
        self.database = FakeIntegration()
        self.library = FakeIntegration()
        self.mangaupdates = FakeIntegration()
        self.notion = FakeIntegration()


class FakeIntegration:
    def validate(self, stage=None):
        from manhwateca.flows.integrations import IntegrationValidation

        return IntegrationValidation(stage=stage, valid=True)

    def scan_library(self):
        from manhwateca.flows.integrations import LibraryScanResult

        return LibraryScanResult(works_found=1)

    def catalog_works(self):
        from manhwateca.flows.integrations import CatalogResult

        import time

        time.sleep(0.2)
        return CatalogResult()

    def search_series(self):
        from manhwateca.flows.integrations import SeriesSearchResult

        return SeriesSearchResult()

    def get_metadata(self):
        from manhwateca.flows.integrations import MetadataUpdateResult

        return MetadataUpdateResult()

    def sync_page(self):
        from manhwateca.flows.integrations import NotionSyncResult

        return NotionSyncResult()


if __name__ == "__main__":
    unittest.main()

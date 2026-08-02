import os
import sys
import types
import unittest
from unittest.mock import patch

from manhwateca.flows.domain import (
    StageExecution,
    StageId,
    WorkflowExecution,
    WorkflowStatus,
)
from manhwateca.flows.runtime import OfficialFlowBackend, default_flow_integrations


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
        self.assertEqual(1, repository.recover_calls)

    def test_get_status_does_not_execute_notion_sync(self):
        repository = FakeRepository()
        integrations = FakeIntegrations()
        repository.execution = WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
        )
        backend = OfficialFlowBackend(
            repository_factory=lambda: repository,
            integrations=integrations,
        )

        backend.get_status()

        self.assertEqual([], integrations.notion.calls)

    def test_start_returns_persisted_running_execution_from_repository(self):
        repository = FakeRepository()
        backend = OfficialFlowBackend(
            repository_factory=lambda: repository,
            integrations=FakeIntegrations(),
            start_timeout=1,
        )

        execution = backend.start()

        self.assertEqual(WorkflowStatus.RUNNING, execution.status)
        self.assertEqual("wf_", execution.execution_id[:3])
        self.assertEqual(set(StageId), {stage.stage_id for stage in execution.stages})

    def test_default_integrations_without_notion_config_keeps_app_available(self):
        with patch.dict(os.environ, {}, clear=True):
            integrations = default_flow_integrations()

        check = integrations.notion.check_status()

        self.assertFalse(check.available)
        self.assertIn("Notion indisponível", check.message)
        self.assertNotIn("NOTION_TOKEN", check.message)

    def test_default_integrations_with_notion_config_uses_official_integration(self):
        fake_module = types.SimpleNamespace(Client=FakeNotionClient)
        with patch.dict(
            os.environ,
            {
                "NOTION_TOKEN": "secret-token",
                "NOTION_DATABASE_ID": "database-id",
            },
            clear=True,
        ):
            with patch.dict(sys.modules, {"notion_client": fake_module}):
                with patch("manhwateca.flows.runtime.MangaRepository", FakeMangaRepository):
                    integrations = default_flow_integrations()

        check = integrations.notion.check_status()

        self.assertEqual("OfficialNotionFlowIntegration", type(integrations.notion).__name__)
        self.assertTrue(check.available)
        self.assertNotIn("secret-token", str(check))


class FakeRepository:
    def __init__(self):
        self.execution = None
        self.recover_calls = 0

    def latest_execution(self):
        return self.execution

    def recover_stale_execution(self, **_kwargs):
        self.recover_calls += 1
        return False

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
    def __init__(self):
        self.calls = []

    def validate(self, stage=None):
        from manhwateca.flows.integrations import IntegrationValidation

        return IntegrationValidation(stage=stage, valid=True)

    def scan_library(self):
        from manhwateca.flows.integrations import LibraryScanResult

        self.calls.append("scan_library")
        return LibraryScanResult(works_found=1)

    def catalog_works(self):
        from manhwateca.flows.integrations import CatalogResult

        import time

        self.calls.append("catalog_works")
        time.sleep(0.2)
        return CatalogResult()

    def search_series(self):
        from manhwateca.flows.integrations import SeriesSearchResult

        self.calls.append("search_series")
        return SeriesSearchResult()

    def get_metadata(self, selected_ids=None):
        from manhwateca.flows.integrations import MetadataUpdateResult

        self.calls.append("get_metadata")
        return MetadataUpdateResult()

    def sync_page(self):
        from manhwateca.flows.integrations import NotionSyncResult

        self.calls.append("sync_page")
        return NotionSyncResult()


class FakeNotionClient:
    def __init__(self, auth=None):
        self.auth = auth


class FakeMangaRepository:
    pass


if __name__ == "__main__":
    unittest.main()

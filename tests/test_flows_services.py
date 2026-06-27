import unittest

from manhwateca.flows.domain import FlowError, StageId
from manhwateca.flows.integrations import (
    CatalogResult,
    FlowIntegrations,
    IntegrationCheck,
    IntegrationStatus,
    IntegrationValidation,
    LibraryScanResult,
    MetadataUpdateResult,
    NotionSyncResult,
    SeriesSearchResult,
)
from manhwateca.flows.services import (
    CatalogWorksService,
    OrganizeLibraryService,
    ResolveIdsService,
    SyncNotionService,
    UpdateMetadataService,
    default_stage_services,
)


class FlowStageServicesTests(unittest.TestCase):
    def test_organize_library_uses_library_scan(self):
        integrations = fake_integrations()
        result = OrganizeLibraryService(integrations).execute()

        self.assertEqual(10, result.processed)
        self.assertEqual(40, result.metrics["chaptersFound"])
        self.assertEqual(["scan_library"], integrations.library.calls)

    def test_catalog_works_reports_pending_as_warning(self):
        integrations = fake_integrations()
        result = CatalogWorksService(integrations).execute()

        self.assertEqual(5, result.processed)
        self.assertTrue(result.has_warnings)
        self.assertEqual(1, result.metrics["pending"])

    def test_resolve_ids_uses_mangaupdates_search(self):
        integrations = fake_integrations()
        result = ResolveIdsService(integrations).execute()

        self.assertEqual(7, result.processed)
        self.assertEqual(2, result.skipped)
        self.assertTrue(result.has_warnings)
        self.assertEqual(["search_series"], integrations.mangaupdates.calls)

    def test_update_metadata_uses_mangaupdates_metadata(self):
        integrations = fake_integrations()
        result = UpdateMetadataService(integrations).execute()

        self.assertEqual(6, result.processed)
        self.assertEqual(1, result.skipped)
        self.assertEqual(["get_metadata"], integrations.mangaupdates.calls)

    def test_sync_notion_uses_notion_sync(self):
        integrations = fake_integrations()
        result = SyncNotionService(integrations).execute()

        self.assertEqual(7, result.processed)
        self.assertEqual(["sync_page"], integrations.notion.calls)

    def test_validate_raises_when_integration_is_invalid(self):
        service = ResolveIdsService(fake_integrations(valid=False))

        with self.assertRaisesRegex(RuntimeError, "Integração indisponível"):
            service.validate()

    def test_default_stage_services_covers_all_official_stages(self):
        services = default_stage_services(fake_integrations())

        self.assertEqual(set(StageId), set(services))


class FakeDatabaseIntegration:
    def __init__(self, valid=True):
        self.valid = valid

    def check_status(self):
        return IntegrationCheck("database", IntegrationStatus.OPERATIONAL)

    def validate(self, stage=None):
        return validation(stage, self.valid)


class FakeLibraryIntegration(FakeDatabaseIntegration):
    def __init__(self, valid=True):
        super().__init__(valid)
        self.calls = []

    def scan_library(self):
        self.calls.append("scan_library")
        return LibraryScanResult(works_found=10, chapters_found=40)

    def catalog_works(self):
        self.calls.append("catalog_works")
        return CatalogResult(created=3, updated=2, pending=1)


class FakeMangaUpdatesIntegration(FakeDatabaseIntegration):
    def __init__(self, valid=True):
        super().__init__(valid)
        self.calls = []

    def search_series(self):
        self.calls.append("search_series")
        return SeriesSearchResult(searched=10, matched=7, pending=1, not_found=2)

    def get_metadata(self):
        self.calls.append("get_metadata")
        return MetadataUpdateResult(updated=6, skipped=1)


class FakeNotionIntegration(FakeDatabaseIntegration):
    def __init__(self, valid=True):
        super().__init__(valid)
        self.calls = []

    def sync_page(self):
        self.calls.append("sync_page")
        return NotionSyncResult(created=4, updated=3)


def fake_integrations(valid=True):
    return FlowIntegrations(
        database=FakeDatabaseIntegration(valid),
        library=FakeLibraryIntegration(valid),
        mangaupdates=FakeMangaUpdatesIntegration(valid),
        notion=FakeNotionIntegration(valid),
    )


def validation(stage, valid):
    return IntegrationValidation(
        stage=stage,
        valid=valid,
        errors=() if valid else (FlowError("Integração indisponível."),),
    )


if __name__ == "__main__":
    unittest.main()

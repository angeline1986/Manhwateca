import unittest

from manhwateca.flows.domain import StageId
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


class FlowIntegrationsTests(unittest.TestCase):
    def test_integration_check_availability(self):
        self.assertTrue(
            IntegrationCheck(
                "database",
                IntegrationStatus.OPERATIONAL,
            ).available
        )
        self.assertTrue(
            IntegrationCheck(
                "mangaupdates",
                IntegrationStatus.WARNING,
            ).available
        )
        self.assertFalse(
            IntegrationCheck(
                "notion",
                IntegrationStatus.UNAVAILABLE,
            ).available
        )

    def test_validation_is_stage_aware(self):
        validation = IntegrationValidation(
            stage=StageId.RESOLVE_IDS,
            valid=True,
        )

        self.assertEqual(StageId.RESOLVE_IDS, validation.stage)
        self.assertTrue(validation.valid)

    def test_result_models_are_metrics_first(self):
        self.assertEqual(4, LibraryScanResult(works_found=4).works_found)
        self.assertEqual(2, CatalogResult(created=2).created)
        self.assertEqual(3, SeriesSearchResult(matched=3).matched)
        self.assertEqual(5, MetadataUpdateResult(updated=5).updated)
        self.assertEqual(6, NotionSyncResult(updated=6).updated)

    def test_flow_integrations_groups_ports_without_implementation(self):
        fake = FakeIntegration()
        integrations = FlowIntegrations(
            database=fake,
            library=fake,
            mangaupdates=fake,
            notion=fake,
        )

        self.assertEqual(IntegrationStatus.OPERATIONAL, integrations.database.check_status().status)
        self.assertEqual(1, integrations.library.scan_library().works_found)
        self.assertEqual(1, integrations.mangaupdates.search_series().matched)
        self.assertEqual(1, integrations.notion.sync_page().updated)


class FakeIntegration:
    def check_status(self):
        return IntegrationCheck("fake", IntegrationStatus.OPERATIONAL)

    def validate(self, stage=None):
        return IntegrationValidation(stage=stage, valid=True)

    def scan_library(self):
        return LibraryScanResult(works_found=1)

    def catalog_works(self):
        return CatalogResult(created=1)

    def search_series(self):
        return SeriesSearchResult(matched=1)

    def get_metadata(self):
        return MetadataUpdateResult(updated=1)

    def sync_page(self):
        return NotionSyncResult(updated=1)


if __name__ == "__main__":
    unittest.main()

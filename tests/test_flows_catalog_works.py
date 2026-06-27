import unittest

from manhwateca.flows.integrations import LibraryInventoryItem
from manhwateca.flows.library import LocalLibraryIntegration


class CatalogWorksIntegrationTests(unittest.TestCase):
    def test_catalog_works_persists_valid_inventory_items(self):
        flow_repository = FakeFlowRepository((
            LibraryInventoryItem(
                name="Obra Nova",
                source_path="/library/Obra Nova",
                main_chapters=12,
                total_chapters=12,
            ),
        ))
        manga_repository = FakeMangaRepository()
        integration = LocalLibraryIntegration(
            flow_repository_factory=lambda: flow_repository,
            manga_repository_factory=lambda: manga_repository,
        )

        result = integration.catalog_works()

        self.assertEqual(1, result.created)
        self.assertEqual(0, result.updated)
        self.assertEqual(0, result.pending)
        self.assertEqual("wf_1", result.metrics["inventoryExecutionId"])
        self.assertEqual("Obra Nova", manga_repository.saved[0]["nome"])

    def test_catalog_works_updates_existing_inventory_items(self):
        flow_repository = FakeFlowRepository((
            LibraryInventoryItem(
                name="Obra Existente",
                source_path="/library/Obra Existente",
                main_chapters=3,
            ),
        ))
        manga_repository = FakeMangaRepository(existing_titles={"Obra Existente"})
        integration = LocalLibraryIntegration(
            flow_repository_factory=lambda: flow_repository,
            manga_repository_factory=lambda: manga_repository,
        )

        result = integration.catalog_works()

        self.assertEqual(0, result.created)
        self.assertEqual(1, result.updated)

    def test_catalog_works_empty_inventory_does_not_fail(self):
        integration = LocalLibraryIntegration(
            flow_repository_factory=lambda: FakeFlowRepository(()),
            manga_repository_factory=FakeMangaRepository,
        )

        result = integration.catalog_works()

        self.assertEqual(0, result.created)
        self.assertEqual(0, result.updated)
        self.assertEqual(0, result.pending)
        self.assertEqual(0, result.metrics["inventoryItems"])

    def test_catalog_works_skips_invalid_inventory_items(self):
        flow_repository = FakeFlowRepository((
            LibraryInventoryItem(
                name="Obra com Conflito",
                source_path="/library/Obra com Conflito",
                is_valid=False,
            ),
        ))
        manga_repository = FakeMangaRepository()
        integration = LocalLibraryIntegration(
            flow_repository_factory=lambda: flow_repository,
            manga_repository_factory=lambda: manga_repository,
        )

        result = integration.catalog_works()

        self.assertEqual(0, result.created)
        self.assertEqual(1, result.pending)
        self.assertEqual([], manga_repository.saved)

    def test_catalog_works_propagates_persistence_failure(self):
        flow_repository = FakeFlowRepository((
            LibraryInventoryItem(
                name="Obra Nova",
                source_path="/library/Obra Nova",
            ),
        ))
        integration = LocalLibraryIntegration(
            flow_repository_factory=lambda: flow_repository,
            manga_repository_factory=lambda: FakeMangaRepository(fail=True),
        )

        with self.assertRaisesRegex(RuntimeError, "falha de persistência"):
            integration.catalog_works()


class FakeFlowRepository:
    def __init__(self, inventory):
        self.inventory = inventory

    def latest_execution(self):
        return FakeExecution("wf_1") if self.inventory is not None else None

    def load_inventory(self, execution_id):
        return self.inventory


class FakeExecution:
    def __init__(self, execution_id):
        self.execution_id = execution_id


class FakeMangaRepository:
    def __init__(self, existing_titles=None, fail=False):
        self.existing_titles = existing_titles or set()
        self.fail = fail
        self.saved = []

    def find_by_normalized_title(self, title):
        return object() if title in self.existing_titles else None

    def save_catalog_manga(self, payload):
        if self.fail:
            raise RuntimeError("falha de persistência")
        self.saved.append(payload)
        return len(self.saved)


if __name__ == "__main__":
    unittest.main()

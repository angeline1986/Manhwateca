import unittest

from manhwateca.flows.mangaupdates import MangaUpdatesFlowIntegration
from manhwateca.flows.repository import CatalogWorkRecord
from manhwateca.flows.services import ResolveIdsService
from manhwateca.flows.integrations import FlowIntegrations


class ResolveIdsFlowTests(unittest.TestCase):
    def test_work_without_id_is_auto_matched(self):
        flow_repository = FakeFlowRepository([
            CatalogWorkRecord(1, "Alpha"),
        ])
        manga_repository = FakeMangaRepository()
        integration = MangaUpdatesFlowIntegration(
            flow_repository_factory=lambda: flow_repository,
            manga_repository_factory=lambda: manga_repository,
            search_function=lambda *_args, **_kwargs: response("Alpha", 101, score_title="Alpha"),
        )

        result = integration.search_series()

        self.assertEqual(1, result.searched)
        self.assertEqual(1, result.matched)
        self.assertEqual([( "Alpha", 101, "Alpha")], manga_repository.confirmed)
        self.assertEqual("auto_matched", flow_repository.candidates[0].status)

    def test_work_with_existing_id_is_ignored(self):
        flow_repository = FakeFlowRepository([
            CatalogWorkRecord(1, "Alpha", work_code="101"),
        ])
        integration = MangaUpdatesFlowIntegration(
            flow_repository_factory=lambda: flow_repository,
            manga_repository_factory=FakeMangaRepository,
            search_function=FailingSearch(),
        )

        result = integration.search_series()

        self.assertEqual(0, result.searched)
        self.assertEqual(1, result.metrics["alreadyResolved"])
        self.assertEqual([], flow_repository.candidates)

    def test_multiple_candidates_become_pending_review(self):
        flow_repository = FakeFlowRepository([
            CatalogWorkRecord(1, "Alpha"),
        ])
        manga_repository = FakeMangaRepository()
        integration = MangaUpdatesFlowIntegration(
            flow_repository_factory=lambda: flow_repository,
            manga_repository_factory=lambda: manga_repository,
            search_function=lambda *_args, **_kwargs: {
                "results": [
                    search_item("Alpha", 101),
                    search_item("Alpha", 102),
                ],
            },
        )

        result = integration.search_series()

        self.assertEqual(1, result.pending)
        self.assertEqual(
            {"pending_review"},
            {candidate.status for candidate in flow_repository.candidates},
        )
        self.assertEqual(1, len(manga_repository.decisions))

    def test_no_candidate_becomes_not_found_warning(self):
        flow_repository = FakeFlowRepository([
            CatalogWorkRecord(1, "Alpha"),
        ])
        integration = MangaUpdatesFlowIntegration(
            flow_repository_factory=lambda: flow_repository,
            manga_repository_factory=FakeMangaRepository,
            search_function=lambda *_args, **_kwargs: {"results": []},
        )

        result = integration.search_series()

        self.assertEqual(1, result.pending)
        self.assertEqual(1, result.not_found)
        self.assertEqual("not_found", flow_repository.candidates[0].status)

    def test_catalog_empty_is_warning_in_service(self):
        integration = FakeMangaUpdatesIntegration()
        result = ResolveIdsService(fake_integrations(integration)).execute()

        self.assertTrue(result.has_warnings)
        self.assertEqual("RESOLVE_IDS_EMPTY", result.warnings[0].code)

    def test_mangaupdates_failure_propagates_to_orchestrator_as_failed(self):
        flow_repository = FakeFlowRepository([
            CatalogWorkRecord(1, "Alpha"),
        ])
        integration = MangaUpdatesFlowIntegration(
            flow_repository_factory=lambda: flow_repository,
            manga_repository_factory=FakeMangaRepository,
            search_function=FailingSearch(),
        )

        with self.assertRaisesRegex(RuntimeError, "MangaUpdates indisponível"):
            integration.search_series()


class FakeExecution:
    execution_id = "wf_1"


class FakeFlowRepository:
    def __init__(self, works):
        self.works = works
        self.candidates = []

    def latest_execution(self):
        return FakeExecution()

    def list_catalog_works_for_id_resolution(self):
        return self.works

    def replace_id_candidates(self, execution_id, candidates):
        self.candidates = candidates


class FakeMangaRepository:
    def __init__(self):
        self.confirmed = []
        self.decisions = []

    def confirm_mangaupdates_id(self, name, series_id, found_title=None):
        self.confirmed.append((name, series_id, found_title))
        return True

    def enqueue_decision(self, **kwargs):
        self.decisions.append(kwargs)
        return True


class FailingSearch:
    def __call__(self, *_args, **_kwargs):
        raise RuntimeError("MangaUpdates indisponível")


class FakeMangaUpdatesIntegration:
    def search_series(self):
        from manhwateca.flows.integrations import SeriesSearchResult

        return SeriesSearchResult(metrics={"catalogWorks": 0})

    def validate(self, stage=None):
        from manhwateca.flows.integrations import IntegrationValidation

        return IntegrationValidation(stage=stage, valid=True)


class FakeIntegration(FakeMangaUpdatesIntegration):
    pass


def fake_integrations(mangaupdates):
    fake = FakeIntegration()
    return FlowIntegrations(
        database=fake,
        library=fake,
        mangaupdates=mangaupdates,
        notion=fake,
    )


def response(title, series_id, *, score_title=None):
    return {"results": [search_item(score_title or title, series_id)]}


def search_item(title, series_id):
    return {
        "record": {
            "series_id": series_id,
            "title": title,
            "type": "Manhwa",
            "url": f"https://example.test/{series_id}",
            "genres": ["Shounen Ai"],
        },
        "hit_title": title,
    }


if __name__ == "__main__":
    unittest.main()

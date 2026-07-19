import unittest
from types import SimpleNamespace

from manhwateca.flows.mangaupdates import MangaUpdatesFlowIntegration
from manhwateca.flows.repository import CatalogWorkRecord
from manhwateca.flows.services import ResolveIdsService
from manhwateca.flows.integrations import FlowIntegrations
from manhwateca.database.manga_repository import MangaUpdatesConfirmationResult


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
        self.assertEqual([(1, 101, "Alpha")], manga_repository.confirmed)
        self.assertEqual("auto_matched", flow_repository.candidates[0].status)

    def test_auto_match_collision_becomes_pending_review(self):
        flow_repository = FakeFlowRepository([
            CatalogWorkRecord(269, "How to Win Over Your Crush"),
        ])
        manga_repository = FakeMangaRepository(
            confirmation=MangaUpdatesConfirmationResult(
                status="external_id_already_assigned",
                work_id=269,
                series_id="74840589785",
                existing_work_id=53,
                existing_title="Segredo para Conquistar o Amor Não Correspondido",
            )
        )
        integration = MangaUpdatesFlowIntegration(
            flow_repository_factory=lambda: flow_repository,
            manga_repository_factory=lambda: manga_repository,
            search_function=lambda *_args, **_kwargs: response(
                "How to Win Over Your Crush",
                74840589785,
                score_title="How to Win Over Your Crush",
            ),
        )

        result = integration.search_series()

        self.assertEqual(1, result.searched)
        self.assertEqual(0, result.matched)
        self.assertEqual(1, result.pending)
        self.assertEqual([], manga_repository.confirmed)
        self.assertEqual("pending_review", flow_repository.candidates[0].status)
        self.assertEqual(
            "external_id_already_assigned",
            flow_repository.candidates[0].details["reason"],
        )
        self.assertEqual(1, len(manga_repository.decisions))

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

    def test_mangaupdates_failure_is_persisted_per_work_without_stalling(self):
        flow_repository = FakeFlowRepository([
            CatalogWorkRecord(1, "Alpha"),
        ])
        integration = MangaUpdatesFlowIntegration(
            flow_repository_factory=lambda: flow_repository,
            manga_repository_factory=FakeMangaRepository,
            search_function=FailingSearch(),
        )

        result = integration.search_series()

        self.assertEqual(1, result.pending)
        self.assertEqual(1, result.metrics["errors"])
        self.assertEqual("error", flow_repository.candidates[0].status)
        self.assertEqual("MANGAUPDATES_SEARCH_FAILED", flow_repository.logs[-1].error_code)
        self.assertEqual((1, 1, "Alpha"), flow_repository.progress_updates[-1])

    def test_update_metadata_uses_selected_postgresql_records_only(self):
        manga_repository = FakeMangaRepository(records=[
            manga_record(7, "Alpha", "101"),
            manga_record(
                9,
                "Beta",
                "102",
                mangaupdates_url="https://example.test/beta",
                cover_url="https://cdn.example.test/beta.jpg",
                alternative_title="Beta Alias",
            ),
            manga_record(11, "Gamma", "103"),
        ])
        integration = MangaUpdatesFlowIntegration(
            manga_repository_factory=lambda: manga_repository,
            detail_function=lambda series_id: {"series_id": series_id, "title": f"Title {series_id}"},
            summarize_function=lambda data: {
                "series_id": data["series_id"],
                "url": f"https://example.test/{data['series_id']}",
                "cover_url": f"https://cdn.example.test/{data['series_id']}.jpg",
                "format": "Manhwa",
                "associated_titles": [f"Alias {data['series_id']}"],
                "genres": [],
                "universe": [],
            },
        )

        result = integration.get_metadata(selected_ids=[7, 9])

        self.assertEqual(1, result.updated)
        self.assertEqual(0, result.failed)
        self.assertEqual([7, 9], result.metrics["selected_work_ids"])
        self.assertEqual([7], result.metrics["attempted_work_ids"])
        self.assertEqual([7, 9], result.metrics["processed_work_ids"])
        self.assertEqual([7, 9], manga_repository.requested_ids)
        self.assertEqual([("Alpha", "101")], [
            (title, series_id) for title, series_id, _summary in manga_repository.metadata_updates
        ])
        self.assertEqual(
            ["Alias 101"],
            manga_repository.metadata_updates[0][2]["associated_titles"],
        )

    def test_update_metadata_without_selection_does_not_process_all_records(self):
        manga_repository = FakeMangaRepository(records=[
            manga_record(7, "Alpha", "101"),
        ])
        integration = MangaUpdatesFlowIntegration(
            manga_repository_factory=lambda: manga_repository,
            detail_function=FailingSearch(),
        )

        result = integration.get_metadata(selected_ids=[])

        self.assertEqual(0, result.updated)
        self.assertEqual([], manga_repository.requested_ids)
        self.assertEqual([], manga_repository.metadata_updates)

    def test_update_metadata_fetches_selected_work_with_empty_alias(self):
        manga_repository = FakeMangaRepository(records=[
            manga_record(
                7,
                "Alpha",
                "101",
                mangaupdates_url="https://example.test/alpha",
                cover_url="https://cdn.example.test/alpha.jpg",
            ),
        ])
        integration = MangaUpdatesFlowIntegration(
            manga_repository_factory=lambda: manga_repository,
            detail_function=lambda series_id: {"series_id": series_id},
            summarize_function=lambda data: {
                "series_id": data["series_id"],
                "associated_titles": ["Alpha Alias"],
                "genres": [],
                "universe": [],
            },
        )

        result = integration.get_metadata(selected_ids=[7])

        self.assertEqual(1, result.updated)
        self.assertEqual([7], result.metrics["attempted_work_ids"])
        self.assertEqual([7], result.metrics["processed_work_ids"])
        self.assertEqual(["Alpha Alias"], manga_repository.metadata_updates[0][2]["associated_titles"])

    def test_update_metadata_does_not_fetch_work_with_existing_alias_only(self):
        manga_repository = FakeMangaRepository(records=[
            manga_record(
                7,
                "Alpha",
                "101",
                mangaupdates_url="https://example.test/alpha",
                cover_url="https://cdn.example.test/alpha.jpg",
                alternative_title="Alpha Alias",
            ),
        ])
        integration = MangaUpdatesFlowIntegration(
            manga_repository_factory=lambda: manga_repository,
            detail_function=FailingSearch(),
        )

        result = integration.get_metadata(selected_ids=[7])

        self.assertEqual(0, result.updated)
        self.assertEqual([], result.metrics["attempted_work_ids"])
        self.assertEqual([7], result.metrics["processed_work_ids"])
        self.assertEqual([], manga_repository.metadata_updates)

    def test_update_metadata_fetches_work_with_blank_alias(self):
        manga_repository = FakeMangaRepository(records=[
            manga_record(
                7,
                "Alpha",
                "101",
                mangaupdates_url="https://example.test/alpha",
                cover_url="https://cdn.example.test/alpha.jpg",
                alternative_title="   ",
            ),
        ])
        integration = MangaUpdatesFlowIntegration(
            manga_repository_factory=lambda: manga_repository,
            detail_function=lambda series_id: {"series_id": series_id},
            summarize_function=lambda data: {
                "series_id": data["series_id"],
                "associated_titles": ["Alpha Alias"],
                "genres": [],
                "universe": [],
            },
        )

        result = integration.get_metadata(selected_ids=[7])

        self.assertEqual(1, result.updated)
        self.assertEqual([7], result.metrics["attempted_work_ids"])

    def test_update_metadata_fetches_without_associated_titles_but_keeps_alias_empty(self):
        manga_repository = FakeMangaRepository(records=[
            manga_record(
                7,
                "Alpha",
                "101",
                mangaupdates_url="https://example.test/alpha",
                cover_url="https://cdn.example.test/alpha.jpg",
            ),
        ])
        integration = MangaUpdatesFlowIntegration(
            manga_repository_factory=lambda: manga_repository,
            detail_function=lambda series_id: {"series_id": series_id},
            summarize_function=lambda data: {
                "series_id": data["series_id"],
                "associated_titles": [],
                "genres": [],
                "universe": [],
            },
        )

        result = integration.get_metadata(selected_ids=[7])

        self.assertEqual(1, result.updated)
        self.assertEqual([7], result.metrics["attempted_work_ids"])
        self.assertEqual([], manga_repository.metadata_updates[0][2]["associated_titles"])

    def test_update_metadata_skips_selected_work_without_work_code(self):
        manga_repository = FakeMangaRepository(records=[
            manga_record(7, "Alpha", None),
        ])
        integration = MangaUpdatesFlowIntegration(
            manga_repository_factory=lambda: manga_repository,
            detail_function=FailingSearch(),
        )

        result = integration.get_metadata(selected_ids=[7])

        self.assertEqual(0, result.updated)
        self.assertEqual(1, result.skipped)
        self.assertEqual([7], result.metrics["skipped_work_ids"])
        self.assertEqual([], manga_repository.metadata_updates)


class FakeExecution:
    execution_id = "wf_1"


class FakeFlowRepository:
    def __init__(self, works):
        self.works = works
        self.candidates = []
        self.messages = []
        self.logs = []
        self.progress_updates = []

    def latest_execution(self):
        return FakeExecution()

    def list_catalog_works_for_id_resolution(self):
        return self.works

    def replace_id_candidates(self, execution_id, candidates):
        self.candidates = candidates

    def clear_id_candidates(self, execution_id):
        self.candidates = []

    def append_id_candidate(self, candidate):
        self.candidates.append(candidate)

    def append_message(self, execution_id, stage, severity, message):
        self.messages.append((stage, severity, message))

    def append_log(self, record):
        self.logs.append(record)

    def update_stage_progress(self, execution_id, stage, progress, current_item=None):
        self.progress_updates.append((progress.current, progress.total, current_item))


class FakeMangaRepository:
    def __init__(self, confirmation=None, records=None):
        self.confirmed = []
        self.decisions = []
        self.confirmation = confirmation
        self.records = records or []
        self.requested_ids = []
        self.metadata_updates = []

    def confirm_mangaupdates_id(self, name, series_id, found_title=None):
        self.confirmed.append((name, series_id, found_title))
        return True

    def confirm_mangaupdates_id_by_work_id(self, work_id, series_id, found_title=None):
        if self.confirmation is not None:
            return self.confirmation
        self.confirmed.append((work_id, series_id, found_title))
        return MangaUpdatesConfirmationResult(
            status="applied",
            work_id=work_id,
            series_id=str(series_id),
        )

    def enqueue_decision(self, **kwargs):
        self.decisions.append(kwargs)
        return True

    def list_mangas_by_ids(self, work_ids):
        self.requested_ids = list(work_ids)
        wanted = set(work_ids)
        return [record for record in self.records if record.id in wanted]

    def update_mangaupdates_fields(self, title, series_id, summary):
        self.metadata_updates.append((title, series_id, summary))
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


def manga_record(
    work_id,
    title,
    work_code,
    *,
    mangaupdates_url=None,
    cover_url=None,
    alternative_title=None,
):
    return SimpleNamespace(
        id=work_id,
        title=title,
        work_code=work_code,
        mangaupdates_url=mangaupdates_url,
        cover_url=cover_url,
        alternative_title=alternative_title,
    )


if __name__ == "__main__":
    unittest.main()

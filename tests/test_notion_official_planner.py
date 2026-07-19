import unittest
from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace

from manhwateca.notion_sync.official_planner import (
    OfficialNotionSyncPlanner,
    _expected_metadata_properties,
    plan_official_metadata_sync,
)
from manhwateca.notion_sync.sync_plan import NextAction, SyncStatus


@dataclass(frozen=True)
class FakeRecord:
    id: int = 1
    work_code: str = "123"
    title: str = "Alpha"
    alternative_title: str | None = "Alfa | Alpha Alias"
    latest_mangaupdates_chapter: Decimal | None = Decimal("12")
    mangaupdates_url: str | None = "https://example.test/alpha"
    themes: list[str] | None = None
    format: str | None = "Manhwa"
    spice_level: str | None = None
    personal_rank: str | None = None
    score: Decimal | None = None
    reading_status: str | None = None
    last_read_chapter: Decimal | None = None
    cover_url: str | None = None
    notion_page_id: str | None = None


class FakeRepository:
    def __init__(self, records):
        self.records = records
        self.updated = []
        self.list_calls = 0
        self.list_by_ids_calls = []

    def list_mangas(self):
        self.list_calls += 1
        return self.records

    def list_mangas_by_ids(self, work_ids):
        self.list_by_ids_calls.append(list(work_ids))
        wanted = {int(work_id) for work_id in work_ids}
        return [record for record in self.records if int(record.id) in wanted]

    def update_notion_sync_fields(self, *args, **kwargs):
        self.updated.append((args, kwargs))
        raise AssertionError("planner must not write PostgreSQL sync fields")


class FakeDatabases:
    def __init__(self, pages=None, error=None):
        self.pages = pages or []
        self.error = error
        self.queries = []

    def query(self, **kwargs):
        self.queries.append(kwargs)
        if self.error:
            raise self.error
        return {"results": self.pages, "has_more": False}


class FakePages:
    def __init__(self, by_id=None, error=None):
        self.by_id = by_id or {}
        self.error = error
        self.retrieved = []
        self.updated = []
        self.created = []
        self.archived = []

    def retrieve(self, **kwargs):
        page_id = kwargs["page_id"]
        self.retrieved.append(page_id)
        if self.error:
            raise self.error
        return self.by_id[page_id]

    def update(self, **kwargs):
        self.updated.append(kwargs)
        raise AssertionError("planner must not update Notion pages")

    def create(self, **kwargs):
        self.created.append(kwargs)
        raise AssertionError("planner must not create Notion pages")


class NotionOfficialPlannerTests(unittest.TestCase):
    def test_finds_page_by_notion_page_id(self):
        record = FakeRecord(notion_page_id="page-1")
        page = notion_page("Alpha", "page-1", url="https://example.test/alpha")
        notion = fake_notion(pages_by_id={"page-1": page})

        result = plan_official_metadata_sync(
            notion,
            "database",
            repository=FakeRepository([record]),
        )

        self.assertEqual(["page-1"], notion.pages.retrieved)
        self.assertFalse(notion.databases.queries)
        self.assertEqual(SyncStatus.PAUSED, result.result.status)
        self.assertEqual(1, result.result.updated_count)
        self.assertEqual(1, len(result.updates))
        assert_no_writes(self, notion)

    def test_finds_page_by_title_or_alias(self):
        record = FakeRecord(title="Alpha", alternative_title="Alfa")
        page = notion_page("Alfa", "page-1", url="https://example.test/alpha")
        notion = fake_notion(database_pages=[page])

        result = plan_official_metadata_sync(
            notion,
            "database",
            repository=FakeRepository([record]),
        )

        self.assertEqual(SyncStatus.PAUSED, result.result.status)
        self.assertEqual(1, result.result.updated_count)
        self.assertEqual(0, result.result.missing_count)
        assert_no_writes(self, notion)

    def test_reports_missing_page(self):
        result = plan_official_metadata_sync(
            fake_notion(database_pages=[]),
            "database",
            repository=FakeRepository([FakeRecord()]),
        )

        self.assertEqual(SyncStatus.BLOCKED, result.result.status)
        self.assertEqual(NextAction.REVIEW_MISSING, result.result.next_action)
        self.assertEqual("missing_page", result.result.blockers[0].code)
        self.assertEqual(1, result.result.blockers[0].work_id)

    def test_incremental_plan_uses_only_requested_ids(self):
        records = [
            FakeRecord(id=259, title="Dressed_to_Kill"),
            FakeRecord(id=258, title="Boredom"),
        ]
        repository = FakeRepository(records)
        notion = fake_notion(database_pages=[
            notion_page("Dressed_to_Kill", "page-259"),
        ])

        result = plan_official_metadata_sync(
            notion,
            "database",
            repository=repository,
        )
        incremental = OfficialNotionSyncPlanner(
            notion,
            "database",
            repository=repository,
        ).plan_metadata_sync_for_ids([259])

        self.assertEqual(1, repository.list_calls)
        self.assertEqual([[259]], repository.list_by_ids_calls)
        self.assertEqual(SyncStatus.PAUSED, incremental.result.status)
        self.assertEqual(1, len(incremental.updates))
        self.assertEqual(259, incremental.updates[0].work_id)
        self.assertEqual(0, incremental.result.missing_count)
        self.assertEqual(SyncStatus.BLOCKED, result.result.status)

    def test_incremental_plan_empty_scope_does_not_query_repository(self):
        repository = FakeRepository([FakeRecord(id=259)])
        planner = OfficialNotionSyncPlanner(
            fake_notion(),
            "database",
            repository=repository,
        )

        result = planner.plan_metadata_sync_for_ids([])

        self.assertEqual(SyncStatus.SYNCED, result.result.status)
        self.assertEqual(0, repository.list_calls)
        self.assertEqual([], repository.list_by_ids_calls)

    def test_incremental_plan_reports_missing_scope_work_id(self):
        repository = FakeRepository([FakeRecord(id=259)])
        planner = OfficialNotionSyncPlanner(
            fake_notion(database_pages=[notion_page("Dressed_to_Kill", "page-259")]),
            "database",
            repository=repository,
        )

        result = planner.plan_metadata_sync_for_ids([259, 999999])

        self.assertEqual(SyncStatus.BLOCKED, result.result.status)
        self.assertEqual("scope_work_missing", result.result.blockers[-1].code)
        self.assertEqual(999999, result.result.blockers[-1].work_id)

    def test_reports_duplicate_page(self):
        pages = [
            notion_page("Alpha", "page-1"),
            notion_page("Alpha", "page-2"),
        ]

        result = plan_official_metadata_sync(
            fake_notion(database_pages=pages),
            "database",
            repository=FakeRepository([FakeRecord()]),
        )

        self.assertEqual(SyncStatus.BLOCKED, result.result.status)
        self.assertEqual(NextAction.REVIEW_DUPLICATES, result.result.next_action)
        self.assertEqual("duplicate_page", result.result.blockers[0].code)

    def test_detects_updates_without_writing(self):
        record = FakeRecord(themes=["Drama", "Romance"])
        page = notion_page("Alpha", "page-1", url=None)
        notion = fake_notion(database_pages=[page])

        result = plan_official_metadata_sync(
            notion,
            "database",
            repository=FakeRepository([record]),
        )

        self.assertEqual(SyncStatus.PAUSED, result.result.status)
        self.assertEqual(1, result.result.updated_count)
        self.assertEqual(NextAction.APPLY, result.result.next_action)
        assert_no_writes(self, notion)

    def test_detects_unchanged(self):
        record = FakeRecord(themes=["Drama", "Romance"])
        page = notion_page(
            "Alpha",
            "page-1",
            work_code=123,
            url="https://example.test/alpha",
            chapter=12,
            alias="Alfa, Alpha Alias",
            themes=["Drama", "Romance"],
            formato="Manhwa",
        )
        notion = fake_notion(database_pages=[page])

        result = plan_official_metadata_sync(
            notion,
            "database",
            repository=FakeRepository([record]),
        )

        self.assertEqual(SyncStatus.SYNCED, result.result.status)
        self.assertEqual(0, result.result.updated_count)
        self.assertEqual(1, result.result.unchanged_count)
        self.assertEqual(1, len(result.unchanged))
        assert_no_writes(self, notion)

    def test_reports_api_error(self):
        result = plan_official_metadata_sync(
            fake_notion(database_error=RuntimeError("Rate limit")),
            "database",
            repository=FakeRepository([FakeRecord()]),
        )

        self.assertEqual(SyncStatus.ERROR, result.result.status)
        self.assertEqual(NextAction.RETRY, result.result.next_action)
        self.assertEqual("api_error", result.result.blockers[0].code)
        self.assertEqual("Rate limit", result.result.blockers[0].message)

    def test_never_writes_to_notion_or_postgresql(self):
        repository = FakeRepository([FakeRecord()])
        notion = fake_notion(database_pages=[notion_page("Alpha", "page-1")])

        plan_official_metadata_sync(notion, "database", repository=repository)

        self.assertEqual([], repository.updated)
        assert_no_writes(self, notion)

    def test_editorial_fields_do_not_enter_official_metadata_plan(self):
        record = FakeRecord(
            spice_level="🔥 Alta",
            personal_rank="Topzera",
            score=Decimal("8"),
            reading_status="Lendo",
            last_read_chapter=Decimal("12"),
        )

        properties = _expected_metadata_properties(
            record,
            notion_page(
                "Alpha",
                "page-1",
                interesse="Fila de Espera",
                picancia="💕 Baixa",
                nota="Ok",
                status="Quero ler",
                ultimo_lido=3,
            ),
        )

        self.assertNotIn("Interesse", properties)
        self.assertNotIn("Picância", properties)
        self.assertNotIn("Nota", properties)
        self.assertNotIn("Status", properties)
        self.assertNotIn("Último lido", properties)

    def test_cover_does_not_enter_official_metadata_plan(self):
        properties = _expected_metadata_properties(
            FakeRecord(cover_url="https://cdn.example.test/alpha.jpg"),
            notion_page("Alpha", "page-1"),
        )

        self.assertNotIn("Capa", properties)
        self.assertNotIn("Cover", properties)
        self.assertNotIn("cover_url", properties)

    def test_alias_preserves_existing_notion_aliases(self):
        properties = _expected_metadata_properties(
            FakeRecord(alternative_title="Alfa | Alpha Alias"),
            notion_page("Alpha", "page-1", alias="Alfa, Manual Alias"),
        )

        self.assertEqual(
            "Alfa, Manual Alias, Alpha Alias",
            properties["Alias"]["rich_text"][0]["text"]["content"],
        )

    def test_alias_adds_local_alias_without_duplicate(self):
        properties = _expected_metadata_properties(
            FakeRecord(alternative_title="Alfa | Alpha Alias | alfa"),
            notion_page("Alpha", "page-1", alias="Alfa"),
        )

        self.assertEqual(
            "Alfa, Alpha Alias",
            properties["Alias"]["rich_text"][0]["text"]["content"],
        )

    def test_alias_does_not_use_generated_id_from_work_code(self):
        properties = _expected_metadata_properties(
            FakeRecord(work_code="123", alternative_title="ID 123"),
            notion_page("Alpha", "page-1", work_code=123),
        )

        self.assertEqual(123, properties["ID da obra"]["number"])
        self.assertNotIn("Alias", properties)

    def test_alias_true_value_is_sent_with_work_code(self):
        properties = _expected_metadata_properties(
            FakeRecord(work_code="123", alternative_title="Alfa Real"),
            notion_page("Alpha", "page-1", work_code=123),
        )

        self.assertEqual(
            "Alfa Real",
            properties["Alias"]["rich_text"][0]["text"]["content"],
        )

    def test_generated_id_alias_already_in_notion_is_cleared(self):
        properties = _expected_metadata_properties(
            FakeRecord(work_code="123", alternative_title=None),
            notion_page("Alpha", "page-1", work_code=123, alias="ID 123"),
        )

        self.assertEqual({"rich_text": []}, properties["Alias"])

    def test_generated_id_alias_is_not_preserved_when_mixed_with_real_alias(self):
        properties = _expected_metadata_properties(
            FakeRecord(work_code="123", alternative_title="Alpha Alias"),
            notion_page("Alpha", "page-1", work_code=123, alias="ID 123, Alfa"),
        )

        self.assertEqual(
            "Alfa, Alpha Alias",
            properties["Alias"]["rich_text"][0]["text"]["content"],
        )


def fake_notion(database_pages=None, pages_by_id=None, database_error=None):
    return SimpleNamespace(
        databases=FakeDatabases(database_pages, error=database_error),
        pages=FakePages(pages_by_id),
    )


def notion_page(
    title,
    page_id,
    *,
    work_code=None,
    url=None,
    chapter=None,
    alias=None,
    themes=None,
    formato=None,
    interesse=None,
    picancia=None,
    nota=None,
    status=None,
    ultimo_lido=None,
):
    properties = {
        "Nome": {
            "type": "title",
            "title": [{"plain_text": title}],
        },
    }
    if work_code is not None:
        properties["ID da obra"] = {"type": "number", "number": work_code}
    if url is not None:
        properties["MangaUpdates"] = {"type": "url", "url": url}
    if chapter is not None:
        properties["Cap MangaUpdates"] = {
            "type": "number",
            "number": chapter,
        }
    if alias is not None:
        properties["Alias"] = {
            "type": "rich_text",
            "rich_text": [{"plain_text": alias}],
        }
    if themes is not None:
        properties["Temática"] = {
            "type": "multi_select",
            "multi_select": [{"name": theme} for theme in themes],
        }
    if formato is not None:
        properties["Formato"] = {
            "type": "select",
            "select": {"name": formato},
        }
    if interesse is not None:
        properties["Interesse"] = {
            "type": "select",
            "select": {"name": interesse},
        }
    if picancia is not None:
        properties["Picância"] = {
            "type": "select",
            "select": {"name": picancia},
        }
    if nota is not None:
        properties["Nota"] = {
            "type": "select",
            "select": {"name": nota},
        }
    if status is not None:
        properties["Status"] = {
            "type": "select",
            "select": {"name": status},
        }
    if ultimo_lido is not None:
        properties["Último lido"] = {
            "type": "number",
            "number": ultimo_lido,
        }
    return {"id": page_id, "properties": properties}


def assert_no_writes(testcase, notion):
    testcase.assertEqual([], notion.pages.updated)
    testcase.assertEqual([], notion.pages.created)


if __name__ == "__main__":
    unittest.main()

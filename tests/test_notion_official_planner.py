import unittest
from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace

from manhwateca.notion_sync.official_planner import (
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
    notion_page_id: str | None = None


class FakeRepository:
    def __init__(self, records):
        self.records = records
        self.updated = []

    def list_mangas(self):
        return self.records

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
        self.assertEqual(SyncStatus.PAUSED, result.status)
        self.assertEqual(1, result.updated_count)
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

        self.assertEqual(SyncStatus.PAUSED, result.status)
        self.assertEqual(1, result.updated_count)
        self.assertEqual(0, result.missing_count)
        assert_no_writes(self, notion)

    def test_reports_missing_page(self):
        result = plan_official_metadata_sync(
            fake_notion(database_pages=[]),
            "database",
            repository=FakeRepository([FakeRecord()]),
        )

        self.assertEqual(SyncStatus.BLOCKED, result.status)
        self.assertEqual(NextAction.REVIEW_MISSING, result.next_action)
        self.assertEqual("missing_page", result.blockers[0].code)
        self.assertEqual(1, result.blockers[0].work_id)

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

        self.assertEqual(SyncStatus.BLOCKED, result.status)
        self.assertEqual(NextAction.REVIEW_DUPLICATES, result.next_action)
        self.assertEqual("duplicate_page", result.blockers[0].code)

    def test_detects_updates_without_writing(self):
        record = FakeRecord(themes=["Drama", "Romance"])
        page = notion_page("Alpha", "page-1", url=None)
        notion = fake_notion(database_pages=[page])

        result = plan_official_metadata_sync(
            notion,
            "database",
            repository=FakeRepository([record]),
        )

        self.assertEqual(SyncStatus.PAUSED, result.status)
        self.assertEqual(1, result.updated_count)
        self.assertEqual(NextAction.APPLY, result.next_action)
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

        self.assertEqual(SyncStatus.SYNCED, result.status)
        self.assertEqual(0, result.updated_count)
        self.assertEqual(1, result.unchanged_count)
        assert_no_writes(self, notion)

    def test_reports_api_error(self):
        result = plan_official_metadata_sync(
            fake_notion(database_error=RuntimeError("Rate limit")),
            "database",
            repository=FakeRepository([FakeRecord()]),
        )

        self.assertEqual(SyncStatus.ERROR, result.status)
        self.assertEqual(NextAction.RETRY, result.next_action)
        self.assertEqual("api_error", result.blockers[0].code)
        self.assertEqual("Rate limit", result.blockers[0].message)

    def test_never_writes_to_notion_or_postgresql(self):
        repository = FakeRepository([FakeRecord()])
        notion = fake_notion(database_pages=[notion_page("Alpha", "page-1")])

        plan_official_metadata_sync(notion, "database", repository=repository)

        self.assertEqual([], repository.updated)
        assert_no_writes(self, notion)


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
    return {"id": page_id, "properties": properties}


def assert_no_writes(testcase, notion):
    testcase.assertEqual([], notion.pages.updated)
    testcase.assertEqual([], notion.pages.created)


if __name__ == "__main__":
    unittest.main()

import unittest

from manhwateca.notion_sync.official_applier import OfficialNotionSyncApplier
from manhwateca.notion_sync.official_planner import (
    NotionPageUpdatePlan,
    OfficialNotionSyncPlan,
)
from manhwateca.notion_sync.sync_plan import (
    NextAction,
    NotionBlocker,
    NotionSyncResult,
    SyncStatus,
)


class OfficialNotionSyncApplierTests(unittest.TestCase):
    def test_applies_safe_page_and_persists_by_work_id(self):
        item = update_plan()
        notion = fake_notion(pages={"page-1": page("page-1", url=None)})
        repository = FakeRepository()

        result = OfficialNotionSyncApplier(notion, repository).apply(
            sync_plan(updates=(item,))
        )

        self.assertEqual(SyncStatus.SYNCED, result.status)
        self.assertEqual(1, result.applied_count)
        self.assertEqual([("page-1", item.properties)], notion.pages.updated)
        self.assertEqual(1, len(repository.updated))
        self.assertEqual(7, repository.updated[0]["work_id"])
        self.assertEqual("page-1", repository.updated[0]["page_id"])
        self.assertEqual("synced", repository.updated[0]["status"])
        self.assertIsNotNone(repository.updated[0]["synced_at"])
        self.assertEqual(1, len(repository.events))

    def test_blocks_missing_page_without_writing(self):
        repository = FakeRepository()
        result = OfficialNotionSyncApplier(
            fake_notion(),
            repository,
        ).apply(sync_plan(blockers=(blocker("missing_page"),)))

        self.assertEqual(SyncStatus.BLOCKED, result.status)
        self.assertEqual(0, result.applied_count)
        self.assertEqual("pending", repository.updated[0]["status"])

    def test_blocks_duplicate_page_without_writing(self):
        notion = fake_notion()
        repository = FakeRepository()
        result = OfficialNotionSyncApplier(
            notion,
            repository,
        ).apply(sync_plan(blockers=(blocker("duplicate_page"),)))

        self.assertEqual(SyncStatus.BLOCKED, result.status)
        self.assertEqual("conflict", repository.updated[0]["status"])
        self.assertEqual([], notion.pages.updated)

    def test_rejects_editorial_property(self):
        item = update_plan(properties={"Interesse": {"select": {"name": "Topzera"}}})
        notion = fake_notion(pages={"page-1": page("page-1")})

        result = OfficialNotionSyncApplier(
            notion,
            FakeRepository(),
        ).apply(sync_plan(updates=(item,)))

        self.assertEqual(SyncStatus.BLOCKED, result.status)
        self.assertEqual("unsafe_property", result.blockers[0].code)
        self.assertEqual([], notion.pages.retrieved)
        self.assertEqual([], notion.pages.updated)

    def test_rejects_cover_property(self):
        item = update_plan(properties={"Capa": {"url": "https://example.test/c.jpg"}})
        notion = fake_notion(pages={"page-1": page("page-1")})

        result = OfficialNotionSyncApplier(
            notion,
            FakeRepository(),
        ).apply(sync_plan(updates=(item,)))

        self.assertEqual(SyncStatus.BLOCKED, result.status)
        self.assertEqual("unsafe_property", result.blockers[0].code)
        self.assertEqual([], notion.pages.updated)

    def test_aborts_when_last_edited_time_changed(self):
        item = update_plan(expected_last_edited_time="old")
        notion = fake_notion(pages={"page-1": page("page-1", edited="new")})
        repository = FakeRepository()

        result = OfficialNotionSyncApplier(
            notion,
            repository,
        ).apply(sync_plan(updates=(item,)))

        self.assertEqual(SyncStatus.BLOCKED, result.status)
        self.assertEqual("stale_notion_page", result.blockers[0].code)
        self.assertEqual("conflict", repository.updated[0]["status"])
        self.assertEqual([], notion.pages.updated)

    def test_aborts_when_current_diff_no_longer_matches_plan(self):
        item = update_plan(properties={"MangaUpdates": {"url": "https://example.test/a"}})
        notion = fake_notion(
            pages={"page-1": page("page-1", url="https://example.test/a")}
        )

        result = OfficialNotionSyncApplier(
            notion,
            FakeRepository(),
        ).apply(sync_plan(updates=(item,)))

        self.assertEqual(SyncStatus.BLOCKED, result.status)
        self.assertEqual("stale_notion_page", result.blockers[0].code)
        self.assertEqual([], notion.pages.updated)

    def test_does_not_update_timestamp_for_unchanged(self):
        unchanged = update_plan(properties={})
        repository = FakeRepository()

        result = OfficialNotionSyncApplier(
            fake_notion(),
            repository,
        ).apply(sync_plan(unchanged=(unchanged,)))

        self.assertEqual(SyncStatus.SYNCED, result.status)
        self.assertEqual(1, result.unchanged_count)
        self.assertEqual([], repository.updated)

    def test_api_error_returns_partial_error_and_interrupts(self):
        first = update_plan(work_id=7, page_id="page-1")
        second = update_plan(work_id=8, page_id="page-2")
        notion = fake_notion(
            pages={
                "page-1": page("page-1", url=None),
                "page-2": page("page-2", url=None),
            },
            update_error_at="page-2",
        )

        result = OfficialNotionSyncApplier(
            notion,
            FakeRepository(),
        ).apply(sync_plan(updates=(first, second)))

        self.assertEqual(SyncStatus.ERROR, result.status)
        self.assertEqual(1, result.applied_count)
        self.assertEqual(1, result.failed_count)
        self.assertEqual("api_error", result.blockers[0].code)
        self.assertEqual(["page-1", "page-2"], [item[0] for item in notion.pages.updated])

    def test_local_persistence_error_reports_partial_result(self):
        item = update_plan()
        repository = FakeRepository(fail_update=True)
        notion = fake_notion(pages={"page-1": page("page-1", url=None)})

        result = OfficialNotionSyncApplier(notion, repository).apply(
            sync_plan(updates=(item,))
        )

        self.assertEqual(SyncStatus.ERROR, result.status)
        self.assertEqual(1, result.applied_count)
        self.assertEqual(1, result.failed_count)
        self.assertEqual("local_persistence_error", result.blockers[0].code)
        self.assertEqual([("page-1", item.properties)], notion.pages.updated)

    def test_never_calls_create_archive_or_delete(self):
        notion = fake_notion(pages={"page-1": page("page-1", url=None)})

        OfficialNotionSyncApplier(notion, FakeRepository()).apply(
            sync_plan(updates=(update_plan(),))
        )

        self.assertEqual([], notion.pages.created)
        self.assertEqual([], notion.pages.archived)
        self.assertEqual([], notion.pages.deleted)


class FakeRepository:
    def __init__(self, fail_update=False):
        self.fail_update = fail_update
        self.updated = []
        self.events = []

    def update_notion_sync_fields_by_id(self, work_id, **kwargs):
        if self.fail_update:
            raise RuntimeError("DB unavailable")
        self.updated.append({"work_id": work_id, **kwargs})
        return True

    def record_sync_event_by_id(self, work_id, **kwargs):
        self.events.append({"work_id": work_id, **kwargs})
        return True


class FakePages:
    def __init__(self, pages=None, update_error_at=None):
        self.pages = pages or {}
        self.update_error_at = update_error_at
        self.retrieved = []
        self.updated = []
        self.created = []
        self.archived = []
        self.deleted = []

    def retrieve(self, **kwargs):
        page_id = kwargs["page_id"]
        self.retrieved.append(page_id)
        return self.pages[page_id]

    def update(self, **kwargs):
        page_id = kwargs["page_id"]
        self.updated.append((page_id, kwargs["properties"]))
        if page_id == self.update_error_at:
            raise RuntimeError("Rate limit")
        return self.pages.get(page_id, {"id": page_id})

    def create(self, **kwargs):
        self.created.append(kwargs)
        raise AssertionError("create must not be called")

    def archive(self, **kwargs):
        self.archived.append(kwargs)
        raise AssertionError("archive must not be called")

    def delete(self, **kwargs):
        self.deleted.append(kwargs)
        raise AssertionError("delete must not be called")


class FakeNotion:
    def __init__(self, pages=None, update_error_at=None):
        self.pages = FakePages(pages, update_error_at=update_error_at)


def fake_notion(pages=None, update_error_at=None):
    return FakeNotion(pages, update_error_at=update_error_at)


def sync_plan(updates=(), unchanged=(), blockers=()):
    status = SyncStatus.BLOCKED if blockers else SyncStatus.PAUSED
    next_action = NextAction.REVIEW_MISSING if blockers else NextAction.APPLY
    return OfficialNotionSyncPlan(
        result=NotionSyncResult(
            status=status,
            next_action=next_action,
            updated_count=len(updates),
            unchanged_count=len(unchanged),
            blockers=blockers,
        ),
        updates=updates,
        unchanged=unchanged,
    )


def update_plan(
    *,
    work_id=7,
    page_id="page-1",
    expected_last_edited_time="2026-01-01T00:00:00.000Z",
    properties=None,
):
    return NotionPageUpdatePlan(
        work_id=work_id,
        work_title=f"Work {work_id}",
        page_id=page_id,
        expected_last_edited_time=expected_last_edited_time,
        properties=properties or {"MangaUpdates": {"url": "https://example.test/a"}},
    )


def blocker(code):
    return NotionBlocker(
        code=code,
        work_id=7,
        work_title="Work 7",
        message=code,
    )


def page(page_id, *, edited="2026-01-01T00:00:00.000Z", url=None):
    return {
        "id": page_id,
        "last_edited_time": edited,
        "properties": {
            "MangaUpdates": {
                "type": "url",
                "url": url,
            },
        },
    }


if __name__ == "__main__":
    unittest.main()

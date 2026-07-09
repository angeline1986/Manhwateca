import unittest
from types import SimpleNamespace
from unittest.mock import patch

from manhwateca.notion_sync import metadata_service
from manhwateca.notion_sync.sync_plan import (
    BlockerSeverity,
    NextAction,
    NotionSyncResult,
    SyncStatus,
    build_sync_result,
)


class NotionSyncPlanTests(unittest.TestCase):
    def test_build_sync_result_synced_without_changes(self):
        result = build_sync_result({})

        self.assertEqual(SyncStatus.SYNCED, result.status)
        self.assertEqual(NextAction.NONE, result.next_action)
        self.assertEqual(0, result.updated_count)
        self.assertEqual((), result.blockers)

    def test_build_sync_result_paused_when_updates_exist(self):
        result = build_sync_result({
            "updates": [{"name": "Alpha"}, {"name": "Beta"}],
            "unchanged": [{"name": "Gamma"}],
        })

        self.assertEqual(SyncStatus.PAUSED, result.status)
        self.assertEqual(NextAction.APPLY, result.next_action)
        self.assertEqual(2, result.updated_count)
        self.assertEqual(1, result.unchanged_count)

    def test_build_sync_result_blocked_by_missing_pages(self):
        result = build_sync_result({
            "missing": [
                {"work_id": 123, "work_title": "Flor de Inverno"},
                "Obra sem página",
            ],
        })

        self.assertEqual(SyncStatus.BLOCKED, result.status)
        self.assertEqual(NextAction.REVIEW_MISSING, result.next_action)
        self.assertEqual(2, result.missing_count)
        self.assertEqual("missing_page", result.blockers[0].code)
        self.assertEqual(BlockerSeverity.BLOCKING, result.blockers[0].severity)
        self.assertEqual(123, result.blockers[0].work_id)
        self.assertEqual("Flor de Inverno", result.blockers[0].work_title)
        self.assertEqual("Obra sem página", result.blockers[1].work_title)

    def test_build_sync_result_blocked_by_duplicates(self):
        duplicate = SimpleNamespace(id="456", title="Duplicada")

        result = build_sync_result({"duplicates": [duplicate]})

        self.assertEqual(SyncStatus.BLOCKED, result.status)
        self.assertEqual(NextAction.REVIEW_DUPLICATES, result.next_action)
        self.assertEqual(1, result.duplicate_count)
        self.assertEqual("duplicate_page", result.blockers[0].code)
        self.assertEqual(456, result.blockers[0].work_id)
        self.assertEqual("Duplicada", result.blockers[0].work_title)

    def test_build_sync_result_error_requests_retry(self):
        result = build_sync_result({"error": "Rate limit"})

        self.assertEqual(SyncStatus.ERROR, result.status)
        self.assertEqual(NextAction.RETRY, result.next_action)
        self.assertEqual("api_error", result.blockers[0].code)
        self.assertEqual(NextAction.RETRY, result.blockers[0].next_action)
        self.assertEqual("Rate limit", result.blockers[0].message)

    def test_build_sync_result_creates_api_error_blockers_from_errors(self):
        result = build_sync_result({
            "errors": [
                {"work_id": 123, "work_title": "Alpha", "message": "Timeout"},
                {"name": "Beta", "error": "Rate limit"},
            ],
        })

        self.assertEqual(SyncStatus.ERROR, result.status)
        self.assertEqual(NextAction.RETRY, result.next_action)
        self.assertEqual(2, len(result.blockers))
        self.assertEqual("api_error", result.blockers[0].code)
        self.assertEqual(123, result.blockers[0].work_id)
        self.assertEqual("Alpha", result.blockers[0].work_title)
        self.assertEqual("Timeout", result.blockers[0].message)
        self.assertEqual("Beta", result.blockers[1].work_title)
        self.assertEqual("Rate limit", result.blockers[1].message)

    def test_build_sync_result_ignores_empty_error_values(self):
        result = build_sync_result({
            "error": None,
            "errors": None,
        })

        self.assertEqual(SyncStatus.SYNCED, result.status)
        self.assertEqual(NextAction.NONE, result.next_action)
        self.assertEqual((), result.blockers)

    def test_build_sync_result_tolerates_missing_keys(self):
        result = build_sync_result({"updated": 3})

        self.assertEqual(SyncStatus.PAUSED, result.status)
        self.assertEqual(3, result.updated_count)
        self.assertEqual(0, result.missing_count)
        self.assertEqual(0, result.duplicate_count)

    def test_build_sync_result_tolerates_none_values(self):
        result = build_sync_result({
            "missing": None,
            "duplicates": None,
        })

        self.assertEqual(SyncStatus.SYNCED, result.status)
        self.assertEqual(NextAction.NONE, result.next_action)
        self.assertEqual(0, result.missing_count)
        self.assertEqual(0, result.duplicate_count)
        self.assertEqual((), result.blockers)

    def test_simulate_metadata_sync_returns_notion_sync_result(self):
        notion = SimpleNamespace(pages=FakePages())
        rows = [{"Nome": "Alpha", "MangaUpdates": "https://example.test"}]
        existing = {
            "alpha": [{
                "id": "page-1",
                "properties": {
                    "Nome": {"title": [{"plain_text": "Alpha"}]},
                    "MangaUpdates": {"type": "url", "url": None},
                },
            }],
        }

        with patch.object(metadata_service, "load_existing_pages", return_value=existing):
            result = metadata_service.simulate_metadata_sync(
                notion,
                "database",
                rows,
                metadata={},
            )

        self.assertIsInstance(result, NotionSyncResult)
        self.assertEqual(SyncStatus.PAUSED, result.status)
        self.assertEqual(1, result.updated_count)
        self.assertFalse(notion.pages.updated)


class FakePages:
    def __init__(self):
        self.updated = []

    def update(self, **kwargs):
        self.updated.append(kwargs)


if __name__ == "__main__":
    unittest.main()

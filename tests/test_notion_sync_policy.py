import unittest
from datetime import datetime

from manhwateca.notion_sync import conflicts, statuses


class NotionSyncStatusTests(unittest.TestCase):
    def test_validates_official_status_values(self):
        self.assertEqual(
            statuses.PENDING,
            statuses.validate_status("pending"),
        )

        with self.assertRaisesRegex(ValueError, "inválido"):
            statuses.validate_status("aguardando")


class NotionSyncConflictTests(unittest.TestCase):
    def test_marks_conflict_when_both_sides_changed_after_last_sync(self):
        result = conflicts.decide_sync_status(
            local_updated_at=datetime.fromisoformat("2026-06-20T10:00:00"),
            notion_updated_at=datetime.fromisoformat("2026-06-20T10:05:00"),
            last_synced_at=datetime.fromisoformat("2026-06-20T09:00:00"),
        )

        self.assertEqual(statuses.CONFLICT, result)

    def test_marks_pending_when_only_one_side_changed(self):
        result = conflicts.decide_sync_status(
            local_updated_at="2026-06-20T10:00:00",
            notion_updated_at="2026-06-20T08:00:00",
            last_synced_at="2026-06-20T09:00:00",
        )

        self.assertEqual(statuses.PENDING, result)

    def test_marks_synced_when_nothing_changed_after_last_sync(self):
        result = conflicts.decide_sync_status(
            local_updated_at="2026-06-20T08:00:00",
            notion_updated_at="2026-06-20T08:30:00",
            last_synced_at="2026-06-20T09:00:00",
        )

        self.assertEqual(statuses.SYNCED, result)

    def test_field_owner_documents_conflict_direction(self):
        self.assertEqual(
            "postgresql",
            conflicts.field_owner("latest_available_chapter"),
        )
        self.assertEqual("notion", conflicts.field_owner("personal_rank"))
        self.assertEqual("postgresql", conflicts.field_owner("unknown"))


if __name__ == "__main__":
    unittest.main()

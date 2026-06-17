import tempfile
import unittest
from pathlib import Path

from manhwateca.notion_sync.sync_state import (
    build_state_records,
    write_sync_state,
)


class SyncStateTests(unittest.TestCase):
    def test_build_state_records_tracks_status_and_hashes(self):
        rows = [{"Nome": "Alpha", "Alias": "Alfa", "ID da obra": "1"}]
        summary = {
            "updates": [{"name": "Alpha", "page_id": "page-1"}],
            "unchanged": [],
            "missing": ["Beta"],
            "duplicates": ["Gamma"],
        }
        records = build_state_records(
            summary,
            rows,
            catalog={"alpha": {"nome": "Alpha", "main_caps": 10}},
            applied=False,
        )

        self.assertEqual("pendente", records["Alpha"]["status"])
        self.assertEqual("page-1", records["Alpha"]["notion_page_id"])
        self.assertTrue(records["Alpha"]["csv_hash"])
        self.assertTrue(records["Alpha"]["catalog_hash"])
        self.assertEqual("ausente_no_notion", records["Beta"]["status"])
        self.assertEqual("duplicado", records["Gamma"]["status"])

    def test_build_state_records_marks_applied_updates_as_synced(self):
        records = build_state_records(
            {
                "updates": [{"name": "Alpha", "page_id": "page-1"}],
                "unchanged": [{"name": "Beta", "page_id": "page-2"}],
                "missing": [],
                "duplicates": [],
            },
            [{"Nome": "Alpha"}, {"Nome": "Beta"}],
            applied=True,
        )

        self.assertEqual("sincronizado", records["Alpha"]["status"])
        self.assertEqual("sincronizado", records["Beta"]["status"])

    def test_write_sync_state_persists_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reports/integrations/sync_state.json"
            payload = write_sync_state({"Alpha": {"status": "ok"}}, path)

            self.assertTrue(path.is_file())
            self.assertIn("updated_at", payload)
            self.assertEqual({"status": "ok"}, payload["works"]["Alpha"])


if __name__ == "__main__":
    unittest.main()

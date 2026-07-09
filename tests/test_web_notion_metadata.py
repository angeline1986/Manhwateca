import json
import tempfile
import unittest
from pathlib import Path

from manhwateca.notion_sync.csv_status import write_csv_status
from manhwateca.webapp.notion_metadata import metadata_status


class WebNotionMetadataTests(unittest.TestCase):
    def test_status_writer_and_web_payload_include_preview(self):
        summary = {
            "updated": 1,
            "updates": [{
                "name": "Alpha",
                "properties": ["Alias", "ID da obra", "MangaUpdates"],
            }],
            "missing": ["Beta"],
            "duplicates": ["Gamma"],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "reports/integrations/manhwateca_import.csv"
            csv_path.parent.mkdir(parents=True)
            csv_path.write_text("Nome\nAlpha\n", encoding="utf-8")
            status_path = (
                root / "reports/integrations/notion_csv_status.json"
            )
            write_csv_status(
                summary,
                False,
                status_path,
                source={"kind": "postgresql", "label": "PostgreSQL"},
            )
            sync_path = root / "reports/integrations/sync_state.json"
            sync_path.write_text(
                json.dumps({
                    "updated_at": "2026-06-17T10:00:00-03:00",
                    "works": {
                        "Alpha": {"status": "sincronizado"},
                        "Beta": {"status": "pendente"},
                    },
                }),
                encoding="utf-8",
            )

            payload = metadata_status(root)

        self.assertTrue(payload["available"])
        self.assertTrue(payload["csv_available"])
        self.assertEqual("SIMULAÇÃO", payload["mode"])
        self.assertEqual("postgresql", payload["source"]["kind"])
        self.assertEqual("PostgreSQL", payload["source"]["label"])
        self.assertEqual(1, payload["summary"]["updates"])
        self.assertEqual(["Beta"], payload["missing"])
        self.assertEqual(
            ["Alias", "ID da obra", "MangaUpdates"],
            payload["updates"][0]["properties"],
        )
        self.assertIn("sync", payload)
        self.assertEqual("blocked", payload["sync"]["status"])
        self.assertEqual("review_duplicates", payload["sync"]["next_action"])
        self.assertEqual(1, payload["sync"]["updated_count"])
        self.assertEqual(1, payload["sync"]["missing_count"])
        self.assertEqual(1, payload["sync"]["duplicate_count"])
        self.assertEqual(
            ["missing_page", "duplicate_page"],
            [blocker["code"] for blocker in payload["sync"]["blockers"]],
        )
        self.assertTrue(payload["sync_state"]["available"])
        self.assertEqual(2, payload["sync_state"]["total"])
        self.assertEqual(
            1,
            payload["sync_state"]["statuses"]["sincronizado"],
        )

    def test_status_includes_synced_sync_result(self):
        payload = self._metadata_payload({
            "updated": 0,
            "updates": [],
            "unchanged": ["Alpha"],
            "missing": [],
            "duplicates": [],
        })

        self.assertTrue(payload["available"])
        self.assertEqual("synced", payload["sync"]["status"])
        self.assertEqual("none", payload["sync"]["next_action"])
        self.assertEqual(1, payload["sync"]["unchanged_count"])
        self.assertEqual([], payload["sync"]["blockers"])

    def test_status_includes_paused_sync_result(self):
        payload = self._metadata_payload({
            "updated": 2,
            "updates": [{"name": "Alpha"}, {"name": "Beta"}],
            "unchanged": [],
            "missing": [],
            "duplicates": [],
        })

        self.assertEqual("paused", payload["sync"]["status"])
        self.assertEqual("apply", payload["sync"]["next_action"])
        self.assertEqual(2, payload["sync"]["updated_count"])
        self.assertEqual([], payload["sync"]["blockers"])

    def test_status_includes_error_sync_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "reports/integrations/notion_csv_status.json"
            path.parent.mkdir(parents=True)
            path.write_text("{invalid", encoding="utf-8")

            payload = metadata_status(root)

        self.assertFalse(payload["available"])
        self.assertIn("inválido", payload["error"])
        self.assertEqual("error", payload["sync"]["status"])
        self.assertEqual("retry", payload["sync"]["next_action"])
        self.assertEqual("api_error", payload["sync"]["blockers"][0]["code"])
        self.assertIn("inválido", payload["sync"]["blockers"][0]["message"])

    def test_invalid_status_has_safe_empty_response(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "reports/integrations/notion_csv_status.json"
            path.parent.mkdir(parents=True)
            path.write_text("{invalid", encoding="utf-8")

            payload = metadata_status(root)

        self.assertFalse(payload["available"])
        self.assertIn("inválido", payload["error"])
        self.assertIn("sync", payload)

    def test_missing_status_keeps_legacy_empty_response(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = metadata_status(Path(directory))

        self.assertFalse(payload["available"])
        self.assertFalse(payload["csv_available"])
        self.assertEqual(
            {"updates": 0, "unchanged": 0, "missing": 0, "duplicates": 0},
            payload["summary"],
        )
        self.assertEqual([], payload["updates"])
        self.assertEqual([], payload["unchanged"])
        self.assertEqual([], payload["missing"])
        self.assertEqual([], payload["duplicates"])
        self.assertIsNone(payload["sync"])
        self.assertIsNone(payload["error"])

    def _metadata_payload(self, summary):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status_path = (
                root / "reports/integrations/notion_csv_status.json"
            )
            write_csv_status(
                summary,
                False,
                status_path,
                source={"kind": "postgresql", "label": "PostgreSQL"},
            )
            return metadata_status(root)

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
            write_csv_status(summary, False, status_path)

            payload = metadata_status(root)

        self.assertTrue(payload["available"])
        self.assertTrue(payload["csv_available"])
        self.assertEqual("SIMULAÇÃO", payload["mode"])
        self.assertEqual(1, payload["summary"]["updates"])
        self.assertEqual(["Beta"], payload["missing"])
        self.assertEqual(
            ["Alias", "ID da obra", "MangaUpdates"],
            payload["updates"][0]["properties"],
        )

    def test_invalid_status_has_safe_empty_response(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "reports/integrations/notion_csv_status.json"
            path.parent.mkdir(parents=True)
            path.write_text("{invalid", encoding="utf-8")

            payload = metadata_status(root)

        self.assertFalse(payload["available"])
        self.assertIn("inválido", payload["error"])

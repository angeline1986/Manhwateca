import json
import tempfile
import unittest
from pathlib import Path

from manhwateca.webapp.catalog import catalog_payload, compare_catalogs


class WebCatalogTests(unittest.TestCase):
    def test_catalog_payload_summarizes_and_hides_local_path(self):
        mangas = [
            {
                "nome": "Alpha",
                "main_caps": 12,
                "chapters_found": 4,
                "side_stories_found": 2,
                "count_status": "OK",
                "path": "/private/library/Alpha",
            },
            {
                "nome": "Beta",
                "main_caps": 20,
                "count_status": "Revisar",
                "unparsed_files": ["arquivo.pdf"],
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data/mangas.json").write_text(
                json.dumps(mangas), encoding="utf-8"
            )
            payload = catalog_payload(root)

        self.assertEqual(2, payload["summary"]["total"])
        self.assertEqual(32, payload["summary"]["main_caps"])
        self.assertEqual(1, payload["summary"]["review"])
        self.assertNotIn("path", payload["mangas"][0])

    def test_compare_catalogs_reports_new_updated_and_removed(self):
        before = [
            {"nome": "Alpha", "main_caps": 10},
            {"nome": "Removed", "main_caps": 3},
        ]
        after = [
            {"nome": "Alpha", "main_caps": 12},
            {"nome": "New", "main_caps": 1},
        ]

        changes = compare_catalogs(before, after)

        self.assertEqual(["New"], changes["new"])
        self.assertEqual(["Removed"], changes["removed"])
        self.assertEqual("Alpha", changes["updated"][0]["nome"])
        self.assertEqual(
            {"before": 10, "after": 12},
            changes["updated"][0]["fields"]["main_caps"],
        )

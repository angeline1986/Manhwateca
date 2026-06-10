import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import notion_csv


class FakeDatabases:
    def query(self, **_kwargs):
        return {
            "results": [{
                "id": "page-1",
                "properties": {
                    "Nome": {"title": [{"plain_text": "Alpha"}]}
                },
            }],
            "has_more": False,
        }


class FakePages:
    def __init__(self):
        self.updated = []

    def update(self, **kwargs):
        self.updated.append(kwargs)


class NotionCsvTests(unittest.TestCase):
    def test_empty_editorial_fields_are_not_cleared(self):
        properties = notion_csv.build_properties({
            "Alias": "",
            "Último capítulo disponível": "10",
            "Capítulos encontrados": "8",
            "Side stories": "0",
            "Lacunas": "4-5",
            "Status da contagem": "Revisar",
            "Capítulo MangaUpdates": "",
            "MangaUpdates": "",
            "ID da obra": "",
            "Temática": "",
            "Formato": "",
            "Universo": "",
            "Picância": "",
        })

        self.assertNotIn("Temática", properties)
        self.assertNotIn("Formato", properties)
        self.assertNotIn("Universo", properties)
        self.assertNotIn("Picância", properties)

    def test_update_from_csv_never_creates_missing_pages(self):
        pages = FakePages()
        notion = SimpleNamespace(databases=FakeDatabases(), pages=pages)
        rows = [
            {"Nome": "Alpha"},
            {"Nome": "Beta"},
        ]

        summary = notion_csv.update_from_csv(
            notion,
            "database",
            rows,
            apply=False,
        )

        self.assertEqual(1, summary["updated"])
        self.assertEqual(["Beta"], summary["missing"])
        self.assertFalse(pages.updated)

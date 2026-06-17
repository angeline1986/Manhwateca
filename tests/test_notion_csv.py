import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import notion_csv


class FakeDatabases:
    def __init__(self, properties=None):
        self.properties = properties or {
            "Nome": {"title": [{"plain_text": "Alpha"}]}
        }

    def query(self, **_kwargs):
        return {
            "results": [{
                "id": "page-1",
                "properties": self.properties,
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
            "Status da contagem": "Revisar",
            "Capítulo MangaUpdates": "",
            "MangaUpdates": "",
            "ID da obra": "",
            "Temática": "",
            "Formato": "",
            "Tamanho": "",
            "Universo": "",
            "Picância": "",
        })

        self.assertNotIn("Temática", properties)
        self.assertNotIn("Formato", properties)
        self.assertNotIn("Tamanho", properties)
        self.assertNotIn("Universo", properties)
        self.assertNotIn("Picância", properties)
        self.assertNotIn("Interesse", properties)

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
        self.assertEqual("Alpha", summary["updates"][0]["name"])
        self.assertIn("Alias", summary["updates"][0]["properties"])
        self.assertFalse(pages.updated)

    def test_update_from_csv_skips_unchanged_page(self):
        pages = FakePages()
        notion = SimpleNamespace(
            databases=FakeDatabases({
                "Nome": {"title": [{"plain_text": "Alpha"}]},
                "Alias": {"type": "rich_text", "rich_text": []},
                "Último cap disponível": {"type": "number", "number": 10},
                "Caps encontrados": {"type": "number", "number": 8},
                "Side stories": {"type": "number", "number": 0},
                "Status da contagem": {
                    "type": "select",
                    "select": {"name": "OK"},
                },
                "Cap MangaUpdates": {"type": "number", "number": None},
                "MangaUpdates": {"type": "url", "url": None},
                "ID da obra": {"type": "number", "number": None},
                "Último lido": {"type": "number", "number": 0},
            }),
            pages=pages,
        )

        summary = notion_csv.update_from_csv(
            notion,
            "database",
            [{
                "Nome": "Alpha",
                "Alias": "",
                "Último capítulo disponível": "10",
                "Capítulos encontrados": "8",
                "Side stories": "0",
                "Status da contagem": "OK",
                "Capítulo MangaUpdates": "",
                "MangaUpdates": "",
                "ID da obra": "",
                "Último lido": "0",
            }],
            apply=True,
        )

        self.assertEqual(0, summary["updated"])
        self.assertEqual(["Alpha"], summary["unchanged"])
        self.assertFalse(pages.updated)

    def test_update_matches_existing_page_by_portuguese_alias(self):
        pages = FakePages()
        notion = SimpleNamespace(databases=FakeDatabases(), pages=pages)

        summary = notion_csv.update_from_csv(
            notion,
            "database",
            [{"Nome": "Official Alpha", "Alias": "Alpha"}],
            apply=False,
        )

        self.assertEqual(1, summary["updated"])
        self.assertEqual([], summary["missing"])

    def test_update_matches_existing_page_by_local_catalog_name(self):
        pages = FakePages()
        notion = SimpleNamespace(databases=FakeDatabases(), pages=pages)
        metadata = {
            "Alpha": {
                "nome_oficial": "Official Alpha",
                "alias": "Alfa Oficial",
            },
        }

        summary = notion_csv.update_from_csv(
            notion,
            "database",
            [{"Nome": "Official Alpha", "Alias": "Alfa Oficial"}],
            apply=False,
            metadata=metadata,
        )

        self.assertEqual(1, summary["updated"])
        self.assertEqual([], summary["missing"])

    def test_interesse_is_mapped_when_present(self):
        properties = notion_csv.build_properties({
            "Interesse": "Muito alto",
        })

        self.assertEqual(
            {"name": "Muito alto"},
            properties["Interesse"]["select"],
        )

    def test_tamanho_is_mapped_when_present(self):
        properties = notion_csv.build_properties({"Tamanho": "Longo"})

        self.assertEqual(
            {"name": "Longo"},
            properties["Tamanho"]["select"],
        )

    def test_last_read_is_mapped_when_zero_or_positive(self):
        self.assertEqual(
            {"number": 0},
            notion_csv.build_properties(
                {"Último lido": "0"}
            )["Último lido"],
        )
        self.assertEqual(
            {"number": 17},
            notion_csv.build_properties(
                {"Último lido": "17"}
            )["Último lido"],
        )

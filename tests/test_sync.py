import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import sync


class FakeDatabases:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def query(self, **kwargs):
        self.calls.append(kwargs)
        return next(self.responses)


class FakePages:
    def __init__(self):
        self.created = []
        self.updated = []

    def create(self, **kwargs):
        self.created.append(kwargs)

    def update(self, **kwargs):
        self.updated.append(kwargs)


def page(page_id, name):
    return {
        "id": page_id,
        "properties": {
            "Nome": {"title": [{"plain_text": name}]},
        },
    }


def manga(name):
    return {
        "nome": name,
        "alias": [],
        "status": "Quero ler",
        "nota": "Ok",
        "ultimo_lido": 0,
        "total_caps": 12,
        "path": f"/tmp/{name}",
    }


class SyncTests(unittest.TestCase):
    def test_load_mangas_rejects_non_list(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mangas.json"
            path.write_text(json.dumps({"nome": "Teste"}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "esperada uma lista"):
                sync.load_mangas(path)

    def test_existing_pages_are_paginated(self):
        notion = SimpleNamespace(
            databases=FakeDatabases([
                {
                    "results": [page("1", "Alpha")],
                    "has_more": True,
                    "next_cursor": "cursor-2",
                },
                {
                    "results": [page("2", "Beta")],
                    "has_more": False,
                },
            ])
        )

        result = sync.load_existing_pages(notion, "database")

        self.assertEqual({"alpha", "beta"}, set(result))
        self.assertEqual("cursor-2", notion.databases.calls[1]["start_cursor"])

    def test_sync_updates_existing_and_creates_missing(self):
        notion = SimpleNamespace(
            databases=FakeDatabases([{
                "results": [page("1", "Alpha")],
                "has_more": False,
            }]),
            pages=FakePages(),
        )

        summary = sync.sync(
            notion,
            "database",
            [manga("Alpha"), manga("Beta")],
            apply=True,
        )

        self.assertEqual(1, summary["updated"])
        self.assertEqual(1, summary["created"])
        self.assertEqual("1", notion.pages.updated[0]["page_id"])
        self.assertEqual("database", notion.pages.created[0]["parent"]["database_id"])

    def test_sync_blocks_duplicate_notion_pages(self):
        notion = SimpleNamespace(
            databases=FakeDatabases([{
                "results": [page("1", "Alpha"), page("2", "Alpha")],
                "has_more": False,
            }]),
            pages=FakePages(),
        )

        summary = sync.sync(notion, "database", [manga("Alpha")], apply=True)

        self.assertEqual(1, summary["duplicates"])
        self.assertFalse(notion.pages.updated)
        self.assertFalse(notion.pages.created)


if __name__ == "__main__":
    unittest.main()

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
        "tamanho": "Curto",
        "total_caps": 12,
        "path": f"/tmp/{name}",
    }


class SyncTests(unittest.TestCase):
    def test_build_properties_includes_optional_classification_fields(self):
        item = manga("Alpha")
        item.update({
            "tematica": ["Regressão", "Sobrevivência"],
            "formato": "Manhwa e Novel",
            "universo": ["Fantasia", "Omegaverse"],
            "nivel_picancia": "🔥 Alta",
        })

        properties = sync.build_properties(item)

        self.assertNotIn("Path", properties)
        self.assertEqual(
            {"number": 0},
            properties["Último cap disponível"],
        )
        self.assertEqual(
            {"number": 0},
            properties["Caps encontrados"],
        )
        self.assertEqual(
            {"name": "Curto"},
            properties["Tamanho"]["select"],
        )
        self.assertEqual(
            [{"name": "Regressão"}, {"name": "Sobrevivência"}],
            properties["Temática"]["multi_select"],
        )
        self.assertEqual(
            {"name": "Manhwa e Novel"},
            properties["Formato"]["select"],
        )
        self.assertEqual(
            [{"name": "Fantasia"}, {"name": "Omegaverse"}],
            properties["Universo"]["multi_select"],
        )
        self.assertEqual(
            {"name": "🔥 Alta"},
            properties["Picância"]["select"],
        )

    def test_build_properties_preserves_unmanaged_classification_fields(self):
        properties = sync.build_properties(manga("Alpha"))

        self.assertNotIn("Alias", properties)
        self.assertNotIn("Último lido", properties)
        self.assertNotIn("Temática", properties)
        self.assertNotIn("Formato", properties)
        self.assertNotIn("Universo", properties)
        self.assertNotIn("Picância", properties)

    def test_build_properties_updates_alias_only_when_present(self):
        item = manga("Alpha")
        item["alias"] = ["Alfa", "Alpha Work"]

        properties = sync.build_properties(item)

        self.assertEqual(
            [{
                "text": {"content": "Alfa, Alpha Work"},
            }],
            properties["Alias"]["rich_text"],
        )

    def test_build_properties_updates_last_read_only_when_known(self):
        item = manga("Alpha")
        item["ultimo_lido"] = 12

        properties = sync.build_properties(item)

        self.assertEqual({"number": 12}, properties["Último lido"])

    def test_normalize_title_ignores_accents_punctuation_and_underscores(self):
        self.assertEqual(
            sync.normalize_title("Além_das Memórias!"),
            sync.normalize_title("Alem das memorias"),
        )

    def test_title_candidates_include_previous_configured_name(self):
        candidates = sync.build_title_candidates(
            manga("Salt Society"),
            {"salt sciety": "Salt Society"},
        )

        self.assertIn(sync.normalize_title("Salt Sciety"), candidates)

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
            title_aliases={},
        )

        self.assertEqual(1, summary["updated"])
        self.assertEqual(1, summary["created"])
        self.assertEqual(1, summary["existing"])
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
        self.assertEqual(2, summary["existing"])
        self.assertFalse(notion.pages.updated)
        self.assertFalse(notion.pages.created)

    def test_sync_matches_previous_configured_title(self):
        notion = SimpleNamespace(
            databases=FakeDatabases([{
                "results": [page("1", "Salt Sciety")],
                "has_more": False,
            }]),
            pages=FakePages(),
        )

        summary = sync.sync(
            notion,
            "database",
            [manga("Salt Society")],
            apply=True,
            title_aliases={"salt sciety": "Salt Society"},
        )

        self.assertEqual(1, summary["updated"])
        self.assertEqual(0, summary["created"])
        self.assertEqual(1, summary["existing"])

    def test_batch_creates_only_next_missing_titles_alphabetically(self):
        notion = SimpleNamespace(
            databases=FakeDatabases([{
                "results": [page("1", "Beta")],
                "has_more": False,
            }]),
            pages=FakePages(),
        )

        summary = sync.sync(
            notion,
            "database",
            [manga("Delta"), manga("Beta"), manga("Alpha"), manga("Charlie")],
            apply=True,
            create_limit=2,
            update_existing=False,
        )

        created_names = [
            item["properties"]["Nome"]["title"][0]["text"]["content"]
            for item in notion.pages.created
        ]
        self.assertEqual(["Alpha", "Charlie"], created_names)
        self.assertEqual(2, summary["created"])
        self.assertEqual(1, summary["pending"])
        self.assertEqual(0, summary["updated"])
        self.assertFalse(notion.pages.updated)

    def test_import_status_records_imported_and_pending_titles(self):
        summary = {
            "catalog_total": 4,
            "matched_titles": ["Beta"],
            "created_titles": ["Alpha", "Charlie"],
            "pending_titles": ["Delta"],
            "duplicate_titles": [],
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            sync.write_import_status(
                summary,
                "APLICAÇÃO EM LOTE (2)",
                applied=True,
                path=path,
            )
            status = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(3, status["resumo"]["total_importadas"])
        self.assertEqual(2, status["resumo"]["importadas_neste_lote"])
        self.assertEqual(["Alpha", "Beta", "Charlie"], status["importadas"])
        self.assertEqual(["Delta"], status["pendentes"])

    def test_simulation_keeps_proposed_creations_pending(self):
        summary = {
            "catalog_total": 2,
            "matched_titles": ["Alpha"],
            "created_titles": ["Beta"],
            "pending_titles": [],
            "duplicate_titles": [],
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            sync.write_import_status(summary, "SIMULAÇÃO", path=path)
            status = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(["Alpha"], status["importadas"])
        self.assertEqual([], status["importadas_neste_lote"])
        self.assertEqual(["Beta"], status["pendentes"])


if __name__ == "__main__":
    unittest.main()

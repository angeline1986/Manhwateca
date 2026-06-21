import json
import sys
import tempfile
import unittest
from decimal import Decimal
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


class FakeMangaRecord:
    def __init__(self, **values):
        self.id = values.get("id", 1)
        self.work_code = values.get("work_code")
        self.title = values.get("title", "Alpha")
        self.alternative_title = values.get("alternative_title")
        self.reading_status = values.get("reading_status", "Quero Ler")
        self.personal_rank = values.get("personal_rank", "Normal")
        self.score = values.get("score")
        self.last_read_chapter = values.get("last_read_chapter")
        self.latest_available_chapter = values.get("latest_available_chapter")
        self.size_label = values.get("size_label")
        self.count_status = values.get("count_status")
        self.latest_mangaupdates_chapter = values.get(
            "latest_mangaupdates_chapter"
        )
        self.mangaupdates_url = values.get("mangaupdates_url")
        self.spice_level = values.get("spice_level")
        self.format = values.get("format")
        self.themes = values.get("themes", [])
        self.notion_page_id = values.get("notion_page_id")
        self.notion_sync_status = values.get("notion_sync_status")


class FakeMangaRepository:
    def __init__(self, mangas):
        self.mangas = mangas

    def list_mangas(self):
        return self.mangas


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

    def test_build_progress_properties_excludes_metadata_fields(self):
        item = manga("Alpha")
        item.update({
            "alias": ["Alfa"],
            "tematica": ["Regressão"],
            "formato": "Manhwa",
            "universo": ["Omegaverse"],
            "nivel_picancia": "🔥 Alta",
            "mangaupdates_latest_chapter": 40,
            "mangaupdates_url": "https://example.test/alpha",
        })

        properties = sync.build_progress_properties(item)

        self.assertIn("Último lido", properties)
        self.assertIn("Caps encontrados", properties)
        self.assertIn("Status da contagem", properties)
        self.assertNotIn("Nome", properties)
        self.assertNotIn("Status", properties)
        self.assertNotIn("Nota", properties)
        self.assertNotIn("Alias", properties)
        self.assertNotIn("MangaUpdates", properties)
        self.assertNotIn("Cap MangaUpdates", properties)
        self.assertNotIn("Temática", properties)
        self.assertNotIn("Formato", properties)
        self.assertNotIn("Universo", properties)
        self.assertNotIn("Picância", properties)

    def test_build_properties_preserves_unmanaged_classification_fields(self):
        properties = sync.build_properties(manga("Alpha"))

        self.assertNotIn("Alias", properties)
        self.assertEqual({"number": 0}, properties["Último lido"])
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

    def test_load_mangas_from_database_maps_view_records_to_catalog_items(self):
        result = sync.load_mangas_from_database(FakeMangaRepository([
            FakeMangaRecord(
                title="Official Alpha",
                alternative_title="Alfa | Alpha Work",
                reading_status="Aguardando Atualização",
                personal_rank="Topzera",
                last_read_chapter=Decimal("12"),
                latest_available_chapter=Decimal("40"),
                latest_mangaupdates_chapter=Decimal("42.5"),
                mangaupdates_url="https://example.test/alpha",
                size_label="Médio",
                count_status="OK",
                format="Manhwa",
                themes=["Drama", "Omegaverse"],
                spice_level="🔥 Alta",
                notion_page_id="page-1",
                notion_sync_status="pending",
            ),
        ]))

        self.assertEqual(1, len(result))
        self.assertEqual("Official Alpha", result[0]["nome"])
        self.assertEqual(["Alfa", "Alpha Work"], result[0]["alias"])
        self.assertEqual("Em espera", result[0]["status"])
        self.assertEqual("Topzera", result[0]["nota"])
        self.assertEqual(12, result[0]["ultimo_lido"])
        self.assertEqual(40, result[0]["main_caps"])
        self.assertEqual(42.5, result[0]["mangaupdates_latest_chapter"])
        self.assertEqual(["Drama", "Omegaverse"], result[0]["tematica"])
        self.assertEqual("page-1", result[0]["notion_page_id"])

    def test_catalog_source_defaults_to_json(self):
        args = sync.parse_args([])

        self.assertEqual("json", args.catalog_source)

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

    def test_sync_uses_custom_property_builder_for_existing_pages(self):
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
            [manga("Alpha")],
            apply=True,
            property_builder=lambda item: {
                "Último lido": {"number": item["ultimo_lido"]}
            },
        )

        self.assertEqual(1, summary["updated"])
        self.assertEqual(
            {"Último lido": {"number": 0}},
            notion.pages.updated[0]["properties"],
        )

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

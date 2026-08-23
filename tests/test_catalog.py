import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from manhwateca.catalog.discovery import find_manga_folders
from manhwateca.catalog.repository import save_mangas
from manhwateca.catalog.scanner import scan_mangas, save_mangas_to_database
from manhwateca.webapp.notion import notion_status


class FakeCatalogRepository:
    def __init__(self):
        self.saved = []

    def save_catalog_mangas(self, mangas):
        self.saved = list(mangas)
        return len(self.saved)


class FakeCatalogRecord:
    def __init__(self, title):
        self.title = title
        self.alternative_title = None
        self.last_read_chapter = 0
        self.latest_available_chapter = 0
        self.size_label = "Curto"
        self.count_status = "Revisar"
        self.latest_mangaupdates_chapter = None
        self.cover_url = None
        self.reading_status = "Quero Ler"
        self.personal_rank = "Normal"
        self.themes = []


class CatalogTests(unittest.TestCase):
    def test_finds_manga_inside_group_and_ignores_status_folder_itself(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manga = root / "A" / "Antidote"
            ignored = root / "Aguardando"
            manga.mkdir(parents=True)
            ignored.mkdir(parents=True)
            (manga / "Antidote cap 1.pdf").touch()
            (ignored / "Outra obra cap 1.pdf").touch()

            result = find_manga_folders(root)

        self.assertEqual([manga], result)

    def test_builds_catalog_progress_and_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manga = root / "A" / "Agenda Alfa"
            manga.mkdir(parents=True)
            (manga / "Agenda Alfa cap 18-45.pdf").touch()

            result = scan_mangas(root, external_cache={})

        self.assertEqual(1, len(result))
        self.assertEqual("Agenda Alfa", result[0]["nome"])
        self.assertEqual(17, result[0]["ultimo_lido"])
        self.assertEqual(45, result[0]["main_caps"])
        self.assertEqual("Médio", result[0]["tamanho"])

    def test_catalogs_work_with_unparsed_pdfs_for_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manga = root / "A" / "A princesa bebe2"
            manga.mkdir(parents=True)
            first = "A_Princesa_Bebê_Pode_Ver_as_Janelas_de_Status_Capitulo_01=10.pdf"
            second = "A_Princesa_Bebê_Pode_Ver_as_Janelas_de_Status_Capitulo_11=20.pdf"
            (manga / first).touch()
            (manga / second).touch()

            result = scan_mangas(root, external_cache={})
            repository = FakeCatalogRepository()
            saved = save_mangas_to_database(
                result,
                repository_factory=lambda: repository,
            )

        self.assertEqual(1, len(result))
        self.assertEqual("A princesa bebe2", result[0]["nome"])
        self.assertEqual(sorted([first, second]), result[0]["unparsed_files"])
        self.assertEqual("Revisar", result[0]["count_status"])
        self.assertEqual(["arquivos não interpretados"], result[0]["count_issues"])
        self.assertEqual(1, saved)
        self.assertEqual("A princesa bebe2", repository.saved[0]["nome"])

    def test_notion_status_stops_returning_cataloged_unparsed_pdf_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status = root / "reports/integrations/notion_import_status.json"
            status.parent.mkdir(parents=True)
            status.write_text(
                json.dumps({
                    "resumo": {
                        "total_catalogo": 1,
                        "total_importadas": 1,
                        "total_pendentes": 0,
                        "total_duplicadas": 0,
                    },
                }),
                encoding="utf-8",
            )
            library = root / "library"
            manga = library / "A princesa bebe2"
            manga.mkdir(parents=True)
            (manga / "A_Princesa_Bebe_Status_Capitulo_final.pdf").touch()

            def active_source(_project_root, *_args, **_kwargs):
                record = FakeCatalogRecord("A princesa bebe2")
                return {
                    "kind": "postgresql",
                    "label": "PostgreSQL",
                    "detail": "vw_mangas",
                    "count": 1,
                    "mangas": [record],
                }

            with (
                patch.dict(os.environ, {"MANGA_ROOT": str(library)}),
                patch("manhwateca.webapp.data_source.active_catalog_source", active_source),
                patch("manhwateca.webapp.notion.active_catalog_source", active_source),
            ):
                payload = notion_status(root)

        self.assertEqual([], payload["uncataloged"])
        self.assertEqual(0, payload["summary"]["uncataloged"])

    def test_marks_external_chapter_divergence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manga = root / "A" / "Antidote"
            manga.mkdir(parents=True)
            (manga / "Antidote cap 1-10.pdf").touch()
            cache = {
                "antidote": {
                    "series_id": 123,
                    "latest_chapter": 20,
                    "cover_url": "https://cdn.example.test/antidote.jpg",
                },
            }

            result = scan_mangas(root, external_cache=cache)

        self.assertEqual("Divergência externa", result[0]["count_status"])
        self.assertIn("MangaUpdates divergente", result[0]["count_issues"])
        self.assertEqual(123, result[0]["mangaupdates_id"])
        self.assertEqual(
            "https://cdn.example.test/antidote.jpg",
            result[0]["cover_url"],
        )

    def test_saves_catalog_creating_parent_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "mangas.json"
            save_mangas([{"nome": "Antidote"}], path)

            with path.open(encoding="utf-8") as file:
                result = json.load(file)

        self.assertEqual([{"nome": "Antidote"}], result)

    def test_persists_catalog_to_database_repository(self):
        repository = FakeCatalogRepository()

        saved = save_mangas_to_database(
            [{"nome": "Antidote"}],
            repository_factory=lambda: repository,
        )

        self.assertEqual(1, saved)
        self.assertEqual([{"nome": "Antidote"}], repository.saved)


if __name__ == "__main__":
    unittest.main()

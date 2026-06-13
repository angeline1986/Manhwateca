import json
import tempfile
import unittest
from pathlib import Path

from manhwateca.catalog.discovery import find_manga_folders
from manhwateca.catalog.repository import save_mangas
from manhwateca.catalog.scanner import scan_mangas


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
                },
            }

            result = scan_mangas(root, external_cache=cache)

        self.assertEqual("Divergência externa", result[0]["count_status"])
        self.assertIn("MangaUpdates divergente", result[0]["count_issues"])
        self.assertEqual(123, result[0]["mangaupdates_id"])

    def test_saves_catalog_creating_parent_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "mangas.json"
            save_mangas([{"nome": "Antidote"}], path)

            with path.open(encoding="utf-8") as file:
                result = json.load(file)

        self.assertEqual([{"nome": "Antidote"}], result)


if __name__ == "__main__":
    unittest.main()

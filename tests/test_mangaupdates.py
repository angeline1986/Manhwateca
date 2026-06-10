import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import mangaupdates


class MangaUpdatesTests(unittest.TestCase):
    def test_choose_search_result_prefers_exact_manhwa(self):
        response = {
            "results": [
                {
                    "record": {
                        "series_id": 1,
                        "title": "Kiss Me if You Can",
                        "type": "Manhwa",
                    },
                    "hit_title": "Kiss Me if You Can",
                },
                {
                    "record": {
                        "series_id": 2,
                        "title": "Kiss Me if You Can (Novel)",
                        "type": "Novel",
                    },
                    "hit_title": "Kiss Me if You Can (Novel)",
                },
            ]
        }

        record, status = mangaupdates.choose_search_result(
            "Kiss Me If You Can",
            response,
        )

        self.assertEqual(1, record["series_id"])
        self.assertEqual("Exata (Manhwa)", status)

    def test_choose_search_result_rejects_ambiguous_exact_matches(self):
        response = {
            "results": [
                {
                    "record": {
                        "series_id": 1,
                        "title": "Alpha",
                        "type": "Novel",
                    },
                    "hit_title": "Alpha",
                },
                {
                    "record": {
                        "series_id": 2,
                        "title": "Alpha",
                        "type": "Novel",
                    },
                    "hit_title": "Alpha",
                },
            ]
        }

        record, status = mangaupdates.choose_search_result("Alpha", response)

        self.assertIsNone(record)
        self.assertEqual("Ambígua", status)

    def test_write_csv_uses_notion_columns_and_id(self):
        manga = {
            "nome": "Alpha",
            "alias": [],
            "status": "Quero ler",
            "nota": "Ok",
            "ultimo_lido": 0,
            "main_caps": 10,
            "chapters_found": 8,
            "side_stories_found": 2,
            "missing_ranges": ["4-5"],
            "count_status": "Revisar",
        }
        external = {
            "series_id": 123,
            "url": "https://example.test/alpha",
            "latest_chapter": 11,
            "format": "Manhwa",
            "genres": ["Drama"],
            "universe": ["Fantasia"],
            "associated_titles": ["A"],
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "output.csv"
            mangaupdates.write_csv(
                [manga],
                {"Alpha": external},
                {"Alpha": {"match_status": "Exata"}},
                path,
            )
            with path.open(encoding="utf-8-sig", newline="") as file:
                row = next(csv.DictReader(file))

        self.assertEqual("123", row["ID da obra"])
        self.assertEqual("Drama", row["Temática"])
        self.assertEqual("4-5", row["Lacunas"])
        self.assertEqual("Exata", row["Correspondência API"])

    def test_enrich_catalog_reuses_confirmed_cache_without_api_calls(self):
        manga = {"nome": "Alpha"}
        cached = {"series_id": 123, "title": "Alpha"}

        with tempfile.TemporaryDirectory() as directory:
            progress_path = Path(directory) / "progress.json"
            cache_path = Path(directory) / "cache.json"
            cache_path.write_text(
                json.dumps({"Alpha": cached}),
                encoding="utf-8",
            )
            progress, _cache = mangaupdates.enrich_catalog(
                [manga],
                delay=0,
                progress_path=progress_path,
                cache_path=cache_path,
            )

        self.assertEqual("Cache confirmado", progress["Alpha"]["match_status"])
        self.assertEqual(123, progress["Alpha"]["series_id"])

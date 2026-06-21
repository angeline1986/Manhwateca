import json
import tempfile
import unittest
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from manhwateca.webapp.catalog import catalog_payload, compare_catalogs


@dataclass
class FakeMangaRecord:
    id: int = 1
    work_code: str = "1"
    title: str = "Database Alpha"
    alternative_title: str = "Alpha BR | Alpha Alias"
    reading_status: str = "Quero Ler"
    personal_rank: str = "Topzera"
    score: Decimal | None = None
    last_read_chapter: Decimal = Decimal("4")
    latest_available_chapter: Decimal = Decimal("12")
    size_label: str = "Curto"
    count_status: str = "OK"
    latest_mangaupdates_chapter: Decimal | None = Decimal("13")
    mangaupdates_url: str | None = None
    spice_level: str | None = None
    format: str | None = "Manhwa"
    themes: list[str] | None = None
    notion_page_id: str | None = None
    notion_last_synced_at: str | None = None
    notion_sync_status: str | None = None


class FakeRepository:
    def list_mangas(self):
        record = FakeMangaRecord()
        record.themes = ["Drama", "Romance"]
        return [record]


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
                "count_issues": ["arquivo não interpretado"],
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

        self.assertEqual("json", payload["source"]["kind"])
        self.assertEqual(2, payload["summary"]["total"])
        self.assertEqual(32, payload["summary"]["main_caps"])
        self.assertEqual(1, payload["summary"]["review"])
        self.assertNotIn("path", payload["mangas"][0])

    def test_catalog_payload_can_read_from_database_repository(self):
        payload = catalog_payload(
            Path("."),
            repository_factory=lambda: FakeRepository(),
        )

        self.assertEqual("postgresql", payload["source"]["kind"])
        self.assertEqual("PostgreSQL", payload["source"]["label"])
        self.assertEqual(1, payload["summary"]["total"])
        self.assertEqual(12, payload["summary"]["main_caps"])
        self.assertEqual("Database Alpha", payload["mangas"][0]["nome"])
        self.assertEqual(["Alpha BR", "Alpha Alias"], payload["mangas"][0]["alias"])
        self.assertEqual("Quero Ler", payload["mangas"][0]["reading_status"])
        self.assertEqual(["Drama", "Romance"], payload["mangas"][0]["themes"])

    def test_expected_gaps_are_not_shown_as_operational_alerts(self):
        mangas = [{
            "nome": "Alpha",
            "count_status": "Revisar",
            "count_issues": ["lacunas", "somente side stories"],
        }]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data/mangas.json").write_text(
                json.dumps(mangas), encoding="utf-8"
            )
            payload = catalog_payload(root)

        self.assertEqual(0, payload["summary"]["review"])
        self.assertEqual([], payload["mangas"][0]["count_issues"])

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

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from manhwateca.webapp.notion import notion_status


class WebNotionTests(unittest.TestCase):
    def test_status_exposes_summary_and_reconciliation_lists(self):
        payload = {
            "atualizado_em": "2026-06-12T12:00:00-03:00",
            "modo": "SIMULAÇÃO DO PRÓXIMO LOTE (25)",
            "resumo": {
                "total_catalogo": 5,
                "total_importadas": 2,
                "importadas_neste_lote": 0,
                "total_pendentes": 2,
                "total_duplicadas": 1,
            },
            "importadas_neste_lote": [],
            "pendentes": ["Beta", "Gamma"],
            "duplicadas": ["Alpha"],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "reports/integrations/notion_import_status.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(payload), encoding="utf-8")

            status = notion_status(root)

        self.assertTrue(status["available"])
        self.assertEqual(2, status["summary"]["pending"])
        self.assertEqual(["Beta", "Gamma"], status["pending"])
        self.assertEqual(["Alpha"], status["duplicates"])

    def test_missing_status_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as directory:
            status = notion_status(directory)

        self.assertFalse(status["available"])
        self.assertEqual(0, status["summary"]["catalog"])

    def test_status_detects_works_in_drive_missing_from_catalog(self):
        payload = {
            "resumo": {
                "total_catalogo": 1,
                "total_importadas": 1,
                "total_pendentes": 0,
            },
            "pendentes": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status_path = root / "reports/integrations/notion_import_status.json"
            status_path.parent.mkdir(parents=True)
            status_path.write_text(json.dumps(payload), encoding="utf-8")
            catalog_path = root / "data/mangas.json"
            catalog_path.parent.mkdir()
            catalog_path.write_text(
                json.dumps([{"nome": "Alpha"}]),
                encoding="utf-8",
            )
            library = root / "library"
            for name in ("Alpha", "Beta"):
                work = library / "A" / name
                work.mkdir(parents=True)
                (work / f"{name} cap 1.pdf").touch()

            with patch.dict(os.environ, {"MANGA_ROOT": str(library)}):
                status = notion_status(root)

        self.assertEqual(2, status["summary"]["library"])
        self.assertEqual(1, status["summary"]["uncataloged"])
        self.assertEqual(["Beta"], status["uncataloged"])

    def test_status_is_stale_when_catalog_changed_after_notion_check(self):
        payload = {
            "resumo": {
                "total_catalogo": 1,
                "total_importadas": 1,
                "total_pendentes": 0,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status_path = root / "reports/integrations/notion_import_status.json"
            status_path.parent.mkdir(parents=True)
            status_path.write_text(json.dumps(payload), encoding="utf-8")
            catalog_path = root / "data/mangas.json"
            catalog_path.parent.mkdir()
            catalog_path.write_text(
                json.dumps([{"nome": "Alpha"}, {"nome": "Beta"}]),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"MANGA_ROOT": ""}):
                status = notion_status(root)

        self.assertTrue(status["stale"])
        self.assertEqual(1, status["summary"]["catalog"])
        self.assertEqual(2, status["summary"]["current_catalog"])

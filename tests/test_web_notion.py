import json
import tempfile
import unittest
from pathlib import Path

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

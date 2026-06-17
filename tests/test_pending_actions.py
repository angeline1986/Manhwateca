import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from manhwateca.webapp.pending_actions import pending_payload


class PendingActionsTests(unittest.TestCase):
    def test_empty_project_has_no_actionable_pending_items(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {}, clear=True):
                payload = pending_payload(Path(directory))

        self.assertEqual(0, payload["total"])
        self.assertIn("Nenhuma", payload["empty_message"])

    def test_detects_catalog_work_missing_from_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_json(root / "data/mangas.json", [{"nome": "Alpha"}])
            _write_csv(root / "reports/integrations/manhwateca_import.csv", [])
            with patch.dict("os.environ", {}, clear=True):
                payload = pending_payload(root)

        self.assertEqual("Atualizar CSV", payload["items"][0]["title"])
        self.assertEqual("mangaupdates_csv", payload["items"][0]["action"])

    def test_detects_review_and_uncached_confirmed_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_json(root / "reports/integrations/buscaIds.json", [
                {"Nome": "Alpha", "Status": "Revisar", "IDs": []},
                {
                    "Nome": "Beta",
                    "Status": "Confirmado manualmente",
                    "ID": 123,
                },
            ])
            _write_json(root / "data/mangaupdates.json", {})
            with patch.dict("os.environ", {}, clear=True):
                payload = pending_payload(root)

        titles = {item["title"] for item in payload["items"]}
        self.assertIn("Revisar correspondências", titles)
        self.assertIn("Consultar detalhes na API", titles)

    def test_detects_sync_state_pending_items(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_json(root / "reports/integrations/sync_state.json", {
                "works": {
                    "Alpha": {"status": "pendente"},
                    "Beta": {"status": "ausente_no_notion"},
                    "Gamma": {"status": "duplicado"},
                }
            })
            with patch.dict("os.environ", {}, clear=True):
                payload = pending_payload(root)

        titles = {item["title"] for item in payload["items"]}
        self.assertIn("Aplicar sincronização pendente", titles)
        self.assertIn("Resolver ausentes no Notion", titles)
        self.assertIn("Resolver duplicadas no Notion", titles)


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["Nome", "Alias"]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()

import csv
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from manhwateca.webapp.pending_actions import (
    _mangaupdates_database_pending,
    pending_payload,
)


class PendingActionsTests(unittest.TestCase):
    def test_empty_project_has_no_actionable_pending_items(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {}, clear=True):
                payload = pending_payload(Path(directory))

        self.assertEqual(0, payload["total"])
        self.assertIn("Nenhuma", payload["empty_message"])

    def test_csv_gap_does_not_create_web_action_without_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_json(root / "data/mangas.json", [{"nome": "Alpha"}])
            _write_csv(root / "reports/integrations/manhwateca_import.csv", [])
            with patch.dict("os.environ", {}, clear=True):
                payload = pending_payload(root)

        self.assertEqual(0, payload["total"])

    def test_csv_gap_is_not_operational_pending_when_database_is_active(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_json(root / "data/mangas.json", [{"nome": "Alpha"}])
            _write_csv(root / "reports/integrations/manhwateca_import.csv", [])
            with patch(
                "manhwateca.webapp.pending_actions.active_catalog_source",
                return_value={
                    "kind": "postgresql",
                    "label": "PostgreSQL",
                    "detail": "vw_mangas",
                    "count": 1,
                    "mangas": [],
                },
            ):
                payload = pending_payload(root)

        self.assertEqual(0, payload["total"])
        self.assertEqual("postgresql", payload["source"]["kind"])

    def test_orphaned_csv_rows_do_not_create_web_action_without_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_json(root / "data/mangas.json", [{"nome": "Alpha"}])
            _write_csv(root / "reports/integrations/manhwateca_import.csv", [
                {
                    "Nome": "Alpha",
                    "Correspondência API": "ID confirmado manualmente",
                },
                {
                    "Nome": "Removed",
                    "Correspondência API": "Fora do catálogo local",
                },
            ])
            with patch.dict("os.environ", {}, clear=True):
                payload = pending_payload(root)

        self.assertEqual(0, payload["total"])

    def test_legacy_json_review_and_cache_do_not_create_web_actions(self):
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

        self.assertEqual(0, payload["total"])

    def test_database_mangaupdates_pending_links_to_official_flows(self):
        class FakeRepository:
            def list_decisions(self, **_kwargs):
                return [{
                    "payload": json.dumps({
                        "nome": "Alpha",
                        "candidatos": [],
                    })
                }]

            def list_mangas(self):
                return [
                    SimpleNamespace(work_code="123", mangaupdates_url=None, cover_url=None),
                    SimpleNamespace(work_code=None, mangaupdates_url=None, cover_url=None),
                ]

        items = _mangaupdates_database_pending(
            repository_factory=lambda: FakeRepository()
        )

        titles = {item["title"] for item in items}
        self.assertIn("Revisar correspondências", titles)
        self.assertIn("Consultar detalhes na API", titles)
        details = next(item for item in items if item["title"] == "Consultar detalhes na API")
        self.assertIsNone(details["action"])
        self.assertEqual("flows", details["page"])

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
    fields = ["Nome", "Alias", "Correspondência API"]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()

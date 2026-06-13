import json
import tempfile
import unittest
from pathlib import Path

from manhwateca.webapp.mangaupdates import (
    apply_review_decisions,
    review_payload,
)


class WebMangaUpdatesTests(unittest.TestCase):
    def test_review_payload_filters_low_score_and_explicit_non_bl(self):
        items = [{
            "Nome": "Alpha",
            "Status": "Revisar",
            "IDs": [
                {"id": 1, "titulo": "Valid", "pontuacao": 0.9, "bl": True},
                {"id": 2, "titulo": "Low", "pontuacao": 0.7, "bl": True},
                {"id": 3, "titulo": "Not BL", "pontuacao": 0.95, "bl": False},
            ],
        }]
        with tempfile.TemporaryDirectory() as directory:
            root = self._project(directory, items)
            payload = review_payload(root)

        self.assertEqual(1, payload["summary"]["review"])
        self.assertEqual([1], [
            candidate["id"] for candidate in payload["items"][0]["candidates"]
        ])

    def test_apply_manual_decision_updates_json_and_creates_backup(self):
        items = [{"Nome": "Alpha", "Status": "Revisar", "IDs": []}]
        decision = {
            "Nome": "Alpha",
            "ID": 99,
            "Nome encontrado": "Official Alpha",
            "Origem": "ID informado manualmente",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = self._project(directory, items)
            applied, rejected, backup = apply_review_decisions(
                root, [decision]
            )
            saved = json.loads(
                (root / "reports/integrations/buscaIds.json").read_text()
            )

        self.assertEqual(["Alpha"], applied)
        self.assertEqual([], rejected)
        self.assertTrue(backup.name.startswith("buscaIds.backup-"))
        self.assertEqual(99, saved[0]["ID"])
        self.assertEqual("Confirmado manualmente", saved[0]["Status"])
        self.assertNotIn("IDs", saved[0])

    def _project(self, directory, items):
        root = Path(directory)
        integrations = root / "reports/integrations"
        integrations.mkdir(parents=True)
        (integrations / "buscaIds.json").write_text(
            json.dumps(items), encoding="utf-8"
        )
        return root

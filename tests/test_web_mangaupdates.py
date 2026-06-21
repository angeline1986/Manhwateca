import json
import tempfile
import unittest
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from manhwateca.webapp.mangaupdates import (
    apply_review_decisions,
    review_payload,
)
from manhwateca.webapp.mangaupdates_status import mangaupdates_status


@dataclass
class FakeMangaRecord:
    title: str
    work_code: str | None = None
    mangaupdates_url: str | None = None
    latest_mangaupdates_chapter: Decimal | None = None


class FakeRepository:
    def list_mangas(self):
        return [
            FakeMangaRecord(
                title="Cached",
                work_code="1",
                mangaupdates_url="https://example.test/cached",
            ),
            FakeMangaRecord(title="Missing", work_code="2"),
            FakeMangaRecord(title="No ID"),
        ]


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

        self.assertEqual("json", payload["source"]["kind"])
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

    def test_status_counts_predicted_api_calls_without_network(self):
        items = [
            {
                "Nome": "Cached",
                "Status": "Confirmado automaticamente",
                "ID": 1,
            },
            {
                "Nome": "Missing",
                "Status": "Confirmado manualmente",
                "ID": 2,
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = self._project(directory, items)
            (root / "data").mkdir()
            (root / "data/mangaupdates.json").write_text(
                json.dumps({"1": {"series_id": 1}}),
                encoding="utf-8",
            )
            (root / "reports/integrations/mangaupdates_state.json").write_text(
                json.dumps({
                    "series": {
                        "1": {
                            "last_checked_at": "2099-01-01T00:00:00+00:00",
                            "status": "cache_valido",
                        }
                    }
                }),
                encoding="utf-8",
            )
            payload = mangaupdates_status(root, batch_size=10)

        self.assertEqual("json", payload["source"]["kind"])
        self.assertEqual(2, payload["summary"]["confirmed_ids"])
        self.assertEqual(1, payload["summary"]["cached_ids"])
        self.assertEqual(1, payload["summary"]["calls_needed"])
        self.assertEqual(2, payload["summary"]["force_refresh_calls"])
        self.assertEqual(["Missing"], [
            item["name"] for item in payload["next_batch"]
        ])

    def test_status_prefers_database_when_available(self):
        payload = mangaupdates_status(
            Path("."),
            batch_size=10,
            repository_factory=lambda: FakeRepository(),
        )

        self.assertEqual("postgresql", payload["source"]["kind"])
        self.assertEqual(2, payload["summary"]["confirmed_ids"])
        self.assertEqual(1, payload["summary"]["cached_ids"])
        self.assertEqual(1, payload["summary"]["calls_needed"])
        self.assertEqual(["Missing"], [
            item["name"] for item in payload["next_batch"]
        ])

    def _project(self, directory, items):
        root = Path(directory)
        integrations = root / "reports/integrations"
        integrations.mkdir(parents=True)
        (integrations / "buscaIds.json").write_text(
            json.dumps(items), encoding="utf-8"
        )
        return root

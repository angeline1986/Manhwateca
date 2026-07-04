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
from manhwateca.webapp.mangaupdates_decisions import (
    apply_decisions_payload,
    validate_decisions_payload,
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


class FakeReviewRepository:
    def __init__(self):
        self.confirmed = []
        self.resolved = []
        self.flow_applied = []

    def list_decisions(self, *, decision_type=None, status=None):
        return [{
            "decision_type": decision_type,
            "status": status,
            "source": "mangaupdates",
            "title": "Alpha",
            "payload": {
                "nome": "Alpha",
                "candidatos": [
                    {
                        "id": 1,
                        "titulo": "Valid",
                        "pontuacao": 0.9,
                        "bl": True,
                    },
                    {
                        "id": 2,
                        "titulo": "Low",
                        "pontuacao": 0.6,
                        "bl": True,
                    },
                ],
            },
        }]

    def list_mangas(self):
        return [
            FakeMangaRecord(title="Alpha", work_code="1"),
            FakeMangaRecord(title="Beta"),
        ]

    def confirm_mangaupdates_id(self, name, series_id, found_title=None):
        self.confirmed.append((name, series_id, found_title))
        return True

    def resolve_decision(self, **kwargs):
        self.resolved.append(kwargs)
        return True

    def mark_flow_id_candidates_applied(self, **kwargs):
        self.flow_applied.append(kwargs)
        return True


class FakeFlowConnection:
    def __init__(self, rows):
        self.rows = rows
        self.closed = False

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _sql):
        return None

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


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

    def test_review_payload_prefers_decision_queue_when_available(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._project(directory, [])
            payload = review_payload(
                root,
                repository_factory=lambda: FakeReviewRepository(),
            )

        self.assertEqual("postgresql", payload["source"]["kind"])
        self.assertEqual("decision_queue", payload["source"]["detail"])
        self.assertEqual(1, payload["summary"]["review"])
        self.assertEqual(1, payload["summary"]["confirmed"])
        self.assertEqual("Alpha", payload["items"][0]["nome"])
        self.assertEqual([1], [
            candidate["id"] for candidate in payload["items"][0]["candidates"]
        ])

    def test_review_payload_uses_flow_candidates_before_decision_queue(self):
        rows = [
            {
                "id": 10,
                "work_id": 7,
                "searched_title": "Alpha",
                "candidate_external_id": "101",
                "candidate_title": "Alpha Official",
                "confidence": Decimal("0.82"),
                "status": "pending_review",
                "details": {"candidate": {"url": "https://example.test/101"}},
                "created_at": "2026-07-01 10:00:00",
                "local_title": "Alpha",
            },
            {
                "id": 11,
                "work_id": 7,
                "searched_title": "Alpha",
                "candidate_external_id": "102",
                "candidate_title": "Alpha Other",
                "confidence": Decimal("0.78"),
                "status": "pending_review",
                "details": {},
                "created_at": "2026-07-01 10:00:00",
                "local_title": "Alpha",
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = self._project(directory, [])
            payload = review_payload(
                root,
                repository_factory=lambda: FakeReviewRepository(),
                connection_factory=lambda: FakeFlowConnection(rows),
            )

        self.assertEqual("flow_id_candidates", payload["source"]["detail"])
        self.assertEqual(1, payload["summary"]["review"])
        self.assertEqual("Alpha", payload["items"][0]["localTitle"])
        self.assertEqual(["101", "102"], [
            candidate["id"] for candidate in payload["items"][0]["candidates"]
        ])

    def test_review_payload_deduplicates_orders_filters_and_limits_candidates(self):
        rows = []
        for index, (external_id, confidence) in enumerate([
            ("101", "0.72"),
            ("102", "0.95"),
            ("101", "0.88"),
            ("103", "0.64"),
            ("104", "0.65"),
            ("105", "0.77"),
            ("106", "0.81"),
            ("107", "0.70"),
            ("108", "0.69"),
        ], start=1):
            rows.append({
                "id": index,
                "work_id": 7,
                "searched_title": "Alpha",
                "candidate_external_id": external_id,
                "candidate_title": f"Candidate {external_id}",
                "confidence": Decimal(confidence),
                "status": "pending_review",
                "details": {},
                "created_at": "2026-07-01 10:00:00",
                "local_title": "Alpha",
            })
        with tempfile.TemporaryDirectory() as directory:
            payload = review_payload(
                self._project(directory, []),
                repository_factory=lambda: FakeReviewRepository(),
                connection_factory=lambda: FakeFlowConnection(rows),
            )

        self.assertEqual(["102", "101", "106", "105", "107"], [
            candidate["id"] for candidate in payload["items"][0]["candidates"]
        ])

    def test_validate_decisions_payload_blocks_missing_ids(self):
        payload = validate_decisions_payload([
            {"Nome": "Alpha", "ID": 10},
            {"Nome": "Beta", "ID": None},
        ])

        self.assertFalse(payload["valid"])
        self.assertEqual(1, payload["ready"])
        self.assertEqual(1, payload["blocked"])

    def test_apply_decisions_payload_returns_job_contract(self):
        def apply_callback(_root, decisions):
            return [decision["Nome"] for decision in decisions], [], None

        payload, status = apply_decisions_payload(
            Path("."),
            [{"Nome": "Alpha", "ID": 10}],
            apply_callback,
        )

        self.assertEqual(200, status)
        self.assertTrue(payload["jobId"].startswith("mangaupdates-apply-"))
        self.assertEqual(1, payload["accepted"])

    def test_apply_decisions_payload_does_not_fake_queue_ids_contract(self):
        def apply_callback(_root, decisions):
            self.assertEqual(["flow_258"], decisions)
            return [], ["Decisão inválida: era esperado um objeto."], None

        payload, status = apply_decisions_payload(
            Path("."),
            ["flow_258"],
            apply_callback,
        )

        self.assertEqual(422, status)
        self.assertEqual([], payload["applied"])
        self.assertEqual(1, payload["blocked"])

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

    def test_apply_decision_uses_decision_queue_and_mirrors_json(self):
        repository = FakeReviewRepository()
        decision = {
            "queueId": "flow_42",
            "Nome": "Alpha",
            "ID": 1,
            "Nome encontrado": "Valid",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = self._project(directory, [])
            applied, rejected, backup = apply_review_decisions(
                root,
                [decision],
                repository_factory=lambda: repository,
            )

        self.assertEqual(["Alpha"], applied)
        self.assertEqual([], rejected)
        self.assertIsNone(backup)
        self.assertEqual(("Alpha", 1, "Valid"), repository.confirmed[0])
        self.assertEqual("mangaupdates_match", repository.resolved[0]["decision_type"])
        self.assertEqual({
            "work_id": 42,
            "title": "Alpha",
            "series_id": 1,
            "candidate_title": "Valid",
        }, repository.flow_applied[0])

    def test_apply_decision_accepts_flow_candidate_review_source(self):
        repository = FakeReviewRepository()
        rows = [{
            "id": 10,
            "work_id": 42,
            "searched_title": "Boredom",
            "candidate_external_id": "22961829567",
            "candidate_title": "Boredom",
            "confidence": Decimal("0.95"),
            "status": "pending_review",
            "details": {},
            "created_at": "2026-07-01 10:00:00",
            "local_title": "Boredom",
        }]
        decision = {
            "queueId": "flow_42",
            "Nome": "Boredom",
            "ID": 22961829567,
            "Nome encontrado": "Boredom",
        }
        with tempfile.TemporaryDirectory() as directory:
            applied, rejected, backup = apply_review_decisions(
                self._project(directory, []),
                [decision],
                repository_factory=lambda: repository,
                connection_factory=lambda: FakeFlowConnection(rows),
            )

        self.assertEqual(["Boredom"], applied)
        self.assertEqual([], rejected)
        self.assertIsNone(backup)
        self.assertEqual(("Boredom", 22961829567, "Boredom"), repository.confirmed[0])
        self.assertEqual(42, repository.flow_applied[0]["work_id"])

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

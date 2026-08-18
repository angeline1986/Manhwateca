import unittest

from manhwateca.webapp.organization import organization_pending_review_payload


class FakeRepository:
    def list_decisions(self, **kwargs):
        return [
            {
                "id": 1,
                "decision_type": "organization_local",
                "source": "validate_chapters",
                "source_key": "chapter:Romance in Romance",
                "title": "Romance in Romance",
                "status": "pending",
                "payload": {
                    "review_category": "correct",
                    "kind": "Capítulo ausente",
                    "detail": "Capítulo 12 ausente.",
                    "impact": "Sequência incompleta",
                    "suggested_action": "Corrigir a origem.",
                    "origin_label": "Validar capítulos",
                },
            }
        ]


class PendingReviewTest(unittest.TestCase):
    def test_reads_only_structured_organization_decisions(self):
        payload = organization_pending_review_payload(
            repository_factory=FakeRepository
        )
        self.assertEqual(payload["summary"]["correct"], 1)
        self.assertEqual(payload["summary"]["decide"], 0)
        self.assertEqual(payload["items"][0]["origin_label"], "Validar capítulos")


if __name__ == "__main__":
    unittest.main()

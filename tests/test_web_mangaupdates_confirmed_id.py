import unittest
from types import SimpleNamespace

from manhwateca.database.manga_repository import ConfirmedIdCorrectionResult
from manhwateca.webapp.mangaupdates_confirmed_id import (
    apply_confirmed_id_correction_payload,
    confirmed_id_candidates_payload,
    confirmed_id_preview_payload,
)


class ConfirmedIdCorrectionPayloadTests(unittest.TestCase):
    def test_candidates_list_only_works_with_confirmed_id(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
            work(300, "Sem ID", work_code=None),
            work(301, "Tuojiang", work_code="56302347523"),
        ])

        payload, status = confirmed_id_candidates_payload("", repository=repository)

        self.assertEqual(200, status)
        self.assertEqual(2, payload["total"])
        self.assertEqual([254, 301], [item["id"] for item in payload["items"]])

    def test_candidates_filter_by_title_local_id_or_work_code(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
            work(301, "Tuojiang", work_code="56302347523"),
        ])

        by_title, _ = confirmed_id_candidates_payload("search=mad", repository=repository)
        by_local_id, _ = confirmed_id_candidates_payload("search=301", repository=repository)
        by_work_code, _ = confirmed_id_candidates_payload("search=56302347523", repository=repository)

        self.assertEqual([254], [item["id"] for item in by_title["items"]])
        self.assertEqual([301], [item["id"] for item in by_local_id["items"]])
        self.assertEqual([301], [item["id"] for item in by_work_code["items"]])

    def test_preview_validates_new_id_without_persisting(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
        ])

        payload, status = confirmed_id_preview_payload(
            {"work_id": 254, "new_work_code": "56302347523"},
            repository=repository,
            detail_function=fake_details,
            summarize_function=fake_summary,
        )

        self.assertEqual(200, status)
        self.assertTrue(payload["can_apply"])
        self.assertEqual(254, payload["work"]["id"])
        self.assertEqual("57487635157", payload["work"]["current_work_code"])
        self.assertEqual("Record of Mad Love", payload["current"]["title"])
        self.assertEqual("56302347523", payload["proposed"]["work_code"])
        self.assertEqual("Tuojiang", payload["proposed"]["title"])
        self.assertEqual("https://cdn.example.test/tuojiang.jpg", payload["proposed"]["cover_url"])
        self.assertEqual(["Mad For Love", "Tuojiang"], payload["proposed"]["aliases"])
        self.assertEqual([], repository.corrections)

    def test_preview_blocks_id_assigned_to_another_work(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
            work(300, "Tuojiang", work_code="56302347523"),
        ])

        payload, status = confirmed_id_preview_payload(
            {"work_id": 254, "new_work_code": "56302347523"},
            repository=repository,
            detail_function=fake_details,
            summarize_function=fake_summary,
        )

        self.assertEqual(409, status)
        self.assertFalse(payload["can_apply"])
        self.assertEqual("external_id_already_assigned", payload["blockers"][0]["code"])
        self.assertEqual(300, payload["blockers"][0]["existing_work_id"])

    def test_preview_blocks_same_id_without_persisting(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
        ])

        payload, status = confirmed_id_preview_payload(
            {"work_id": 254, "new_work_code": "57487635157"},
            repository=repository,
            detail_function=fake_details,
            summarize_function=fake_summary,
        )

        self.assertEqual(409, status)
        self.assertFalse(payload["can_apply"])
        self.assertEqual("same_id", payload["blockers"][0]["code"])
        self.assertEqual([], repository.corrections)

    def test_preview_returns_not_found_for_unknown_mangaupdates_id(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
        ])

        payload, status = confirmed_id_preview_payload(
            {"work_id": 254, "new_work_code": "999"},
            repository=repository,
            detail_function=lambda work_code: None,
            summarize_function=fake_summary,
        )

        self.assertEqual(404, status)
        self.assertEqual("ID MangaUpdates não encontrado.", payload["error"])
        self.assertEqual([], repository.corrections)

    def test_preview_returns_bad_gateway_when_mangaupdates_fails(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
        ])

        def failing_details(_work_code):
            raise TimeoutError("timeout")

        payload, status = confirmed_id_preview_payload(
            {"work_id": 254, "new_work_code": "56302347523"},
            repository=repository,
            detail_function=failing_details,
            summarize_function=fake_summary,
        )

        self.assertEqual(502, status)
        self.assertEqual("Não foi possível validar o novo ID no MangaUpdates.", payload["error"])
        self.assertEqual([], repository.corrections)

    def test_apply_invalidates_metadata_without_rebuilding_it(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
        ])

        payload, status = apply_confirmed_id_correction_payload(
            {
                "work_id": 254,
                "expected_current_work_code": "57487635157",
                "new_work_code": "56302347523",
                "confirmed": True,
            },
            repository=repository,
            detail_function=fake_details,
            summarize_function=fake_summary,
        )

        self.assertEqual(200, status)
        self.assertTrue(payload["applied"])
        self.assertEqual(254, payload["work_id"])
        self.assertEqual("57487635157", payload["old_work_code"])
        self.assertEqual("56302347523", payload["new_work_code"])
        self.assertEqual("pending", payload["metadata_status"])
        self.assertEqual("pending", payload["notion_sync_status"])
        self.assertIn("mangaupdates_url", payload["invalidated_fields"])
        self.assertIn("cover_url", payload["invalidated_fields"])
        correction = repository.corrections[0]
        self.assertEqual(254, correction["work_id"])
        self.assertEqual("56302347523", correction["new_work_code"])
        self.assertEqual("Tuojiang", correction["event_payload"]["proposed"]["title"])

    def test_apply_requires_explicit_confirmation(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
        ])

        payload, status = apply_confirmed_id_correction_payload(
            {
                "work_id": 254,
                "expected_current_work_code": "57487635157",
                "new_work_code": "56302347523",
            },
            repository=repository,
            detail_function=fake_details,
            summarize_function=fake_summary,
        )

        self.assertEqual(400, status)
        self.assertIn("Confirme", payload["error"])
        self.assertEqual([], repository.corrections)

    def test_apply_requires_expected_current_work_code(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
        ])

        payload, status = apply_confirmed_id_correction_payload(
            {
                "work_id": 254,
                "new_work_code": "56302347523",
                "confirmed": True,
            },
            repository=repository,
            detail_function=fake_details,
            summarize_function=fake_summary,
        )

        self.assertEqual(400, status)
        self.assertIn("nova validação", payload["error"])
        self.assertEqual([], repository.corrections)

    def test_apply_blocks_stale_preview_before_persisting(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="12345678900"),
        ])

        payload, status = apply_confirmed_id_correction_payload(
            {
                "work_id": 254,
                "expected_current_work_code": "57487635157",
                "new_work_code": "56302347523",
                "confirmed": True,
            },
            repository=repository,
            detail_function=fake_details,
            summarize_function=fake_summary,
        )

        self.assertEqual(409, status)
        self.assertFalse(payload["can_apply"])
        self.assertEqual("stale_preview", payload["blockers"][0]["code"])
        self.assertEqual("57487635157", payload["expected_current_work_code"])
        self.assertEqual("12345678900", payload["actual_current_work_code"])
        self.assertEqual([], repository.corrections)

    def test_apply_blocks_late_collision_without_persisting(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
            work(300, "Tuojiang", work_code="56302347523"),
        ])

        payload, status = apply_confirmed_id_correction_payload(
            {
                "work_id": 254,
                "expected_current_work_code": "57487635157",
                "new_work_code": "56302347523",
                "confirmed": True,
            },
            repository=repository,
            detail_function=fake_details,
            summarize_function=fake_summary,
        )

        self.assertEqual(409, status)
        self.assertFalse(payload["can_apply"])
        self.assertEqual("external_id_already_assigned", payload["blockers"][0]["code"])
        self.assertEqual([], repository.corrections)

    def test_apply_revalidates_mangaupdates_and_does_not_persist_when_it_fails(self):
        repository = FakeConfirmedIdRepository([
            work(254, "Mad for love", work_code="57487635157"),
        ])

        def failing_details(_work_code):
            raise TimeoutError("timeout")

        payload, status = apply_confirmed_id_correction_payload(
            {
                "work_id": 254,
                "expected_current_work_code": "57487635157",
                "new_work_code": "56302347523",
                "confirmed": True,
            },
            repository=repository,
            detail_function=failing_details,
            summarize_function=fake_summary,
        )

        self.assertEqual(502, status)
        self.assertEqual("Não foi possível validar o novo ID no MangaUpdates.", payload["error"])
        self.assertEqual([], repository.corrections)


class FakeConfirmedIdRepository:
    def __init__(self, works):
        self.works = works
        self.corrections = []

    def find_by_id(self, work_id):
        return next((item for item in self.works if int(item.id) == int(work_id)), None)

    def find_by_work_code(self, work_code):
        return next((item for item in self.works if str(item.work_code or "") == str(work_code)), None)

    def list_mangas(self):
        return self.works

    def correct_confirmed_mangaupdates_id(self, work_id, new_work_code, **kwargs):
        item = self.find_by_id(work_id)
        existing = self.find_by_work_code(new_work_code)
        if existing is not None and int(existing.id) != int(work_id):
            return ConfirmedIdCorrectionResult(
                status="external_id_already_assigned",
                work_id=int(work_id),
                old_series_id=str(item.work_code),
                new_series_id=str(new_work_code),
                existing_work_id=int(existing.id),
                existing_title=existing.title,
                expected_current_work_code=kwargs.get("expected_current_work_code"),
                actual_current_work_code=str(item.work_code),
                message="ID MangaUpdates já associado a outra obra.",
            )
        self.corrections.append({
            "work_id": work_id,
            "new_work_code": new_work_code,
            **kwargs,
        })
        return ConfirmedIdCorrectionResult(
            status="applied",
            work_id=int(work_id),
            old_series_id=str(item.work_code),
            new_series_id=str(new_work_code),
            invalidated_fields=(
                "mangaupdates_url",
                "cover_url",
                "format",
                "latest_mangaupdates_chapter",
                "alternative_title",
            ),
            notion_sync_status="pending",
        )


def work(work_id, title, *, work_code=None):
    return SimpleNamespace(
        id=work_id,
        title=title,
        work_code=work_code,
        mangaupdates_url="https://example.test/current",
        cover_url="https://example.test/current.jpg",
        alternative_title="Record of Mad Love",
        notion_sync_status="synced",
    )


def fake_details(work_code):
    return {"series_id": int(work_code), "title": f"Series {work_code}"}


def fake_summary(raw):
    if raw["series_id"] == 56302347523:
        return {
            "title": "Tuojiang",
            "url": "https://www.mangaupdates.com/series/pv4ypdv/tuojiang",
            "cover_url": "https://cdn.example.test/tuojiang.jpg",
            "format": "Manhua",
            "latest_chapter": 74,
            "associated_titles": ["Mad For Love", "Tuojiang"],
        }
    return {
        "title": "Record of Mad Love",
        "url": "https://www.mangaupdates.com/series/qeqnj6d/record-of-mad-love",
        "cover_url": None,
        "format": "Manhwa",
        "latest_chapter": 0,
        "associated_titles": ["Gwangaerok"],
    }


if __name__ == "__main__":
    unittest.main()

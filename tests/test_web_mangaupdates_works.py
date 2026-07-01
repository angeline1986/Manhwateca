import unittest

from manhwateca.webapp.mangaupdates_works import works_payload


class MangaUpdatesWorksPayloadTests(unittest.TestCase):
    def test_without_id_payload_returns_kpis_and_rows(self):
        payload = works_payload(
            "status=WITHOUT_ID&page=1&pageSize=10",
            connection_factory=lambda: FakeConnection([
                row(1, "Alpha"),
                row(2, "Beta", pending_count=2, candidates_count=2),
                row(3, "Gamma", not_found_count=1),
                row(4, "Delta", error_count=1),
                row(5, "Confirmed", work_code="123"),
            ]),
        )

        self.assertTrue(payload["success"])
        data = payload["data"]
        self.assertEqual(4, data["kpis"]["withoutId"])
        self.assertEqual(1, data["kpis"]["readyToSearch"])
        self.assertEqual(1, data["kpis"]["candidatesFound"])
        self.assertEqual(1, data["kpis"]["noResult"])
        self.assertEqual(1, data["kpis"]["apiErrors"])
        self.assertEqual(4, data["pagination"]["total"])
        self.assertEqual(
            ["READY_TO_SEARCH", "PENDING_REVIEW", "ERROR", "MANUAL_ID_REQUIRED"],
            [item["decisionStatus"] for item in data["items"]],
        )

    def test_filters_specific_status_and_search(self):
        payload = works_payload(
            "status=PENDING_REVIEW&search=bet",
            connection_factory=lambda: FakeConnection([
                row(1, "Alpha", pending_count=1, candidates_count=1),
                row(2, "Beta Love", pending_count=1, candidates_count=2),
            ]),
        )

        items = payload["data"]["items"]
        self.assertEqual(1, len(items))
        self.assertEqual("Beta Love", items[0]["localTitle"])
        self.assertEqual("REVIEW_CANDIDATES", items[0]["nextAction"])


def row(
    manga_id,
    title,
    *,
    work_code=None,
    pending_count=0,
    not_found_count=0,
    error_count=0,
    candidates_count=0,
):
    return {
        "id": manga_id,
        "title": title,
        "alternative_title": "",
        "work_code": work_code,
        "mangaupdates_url": None,
        "created_at": "2026-07-01T10:00:00",
        "updated_at": "2026-07-01T10:00:00",
        "latest_candidate_status": None,
        "searched_title": title,
        "last_search_at": None,
        "pending_count": pending_count,
        "not_found_count": not_found_count,
        "error_count": error_count,
        "candidates_count": candidates_count,
    }


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.closed = False

    def cursor(self):
        return FakeCursor(self.rows)

    def close(self):
        self.closed = True


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, *_args):
        return None

    def fetchall(self):
        return self.rows


if __name__ == "__main__":
    unittest.main()

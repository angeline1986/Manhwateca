import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

from manhwateca.release_monitor.parser import parse_external_releases
from manhwateca.release_monitor.service import ReleaseMonitorService, current_periods


class FakeRepository:
    def __init__(self):
        self.running = False
        self.rows = {}
        self.finished = []

    def active_run(self):
        return {"id": 99, "started_at": datetime(2026, 8, 6, tzinfo=ZoneInfo("UTC"))} if self.running else None

    def start_run(self, reference_date, timezone):
        return None if self.running else 1

    def finish_run(self, run_id, status, metrics, error_message=None):
        self.finished.append((status, dict(metrics), error_message))

    def latest_run(self):
        return {"started_at": datetime(2026, 8, 6, 13, tzinfo=ZoneInfo("UTC")), "finished_at": datetime(2026, 8, 6, 13, 1, tzinfo=ZoneInfo("UTC"))}

    def list_active_subscriptions(self):
        return [{"manga_id": 10, "work_code": "123", "title": "Obra A"}]

    def upsert_release(self, release, manga_id):
        key = release.external_release_id or (
            release.series_id,
            release.release_date,
            release.chapter.casefold(),
            (release.group_name or "").casefold(),
            (release.volume or "").casefold(),
        )
        inserted = key not in self.rows
        self.rows[key] = release
        return inserted


class ReleaseMonitorTests(unittest.TestCase):
    def test_periods_use_sao_paulo_week_and_month_boundaries(self):
        periods = current_periods(datetime(2026, 8, 6, 2, 0, tzinfo=ZoneInfo("UTC")))
        self.assertEqual(periods.today_start, date(2026, 8, 5))
        self.assertEqual(periods.week_start, date(2026, 8, 3))
        self.assertEqual(periods.week_end, date(2026, 8, 9))
        self.assertEqual(periods.month_start, date(2026, 8, 1))
        self.assertEqual(periods.month_end, date(2026, 8, 31))

    def test_parser_keeps_alphanumeric_chapters(self):
        releases = parse_external_releases({
            "results": [{
                "id": "rel-1",
                "series_id": 123,
                "chapter": "Side Story 4",
                "volume": None,
                "date": "2026-08-06",
                "group": {"name": "Grupo"},
            }]
        })
        self.assertEqual(releases[0].chapter, "Side Story 4")
        self.assertIsNone(releases[0].volume)
        self.assertEqual(releases[0].group_name, "Grupo")

    def test_service_matches_only_monitored_series_and_is_idempotent(self):
        repository = FakeRepository()
        payload = {"results": [
            {"id": "a", "series_id": 123, "chapter": "35.5", "date": "2026-08-06"},
            {"id": "b", "series_id": 456, "chapter": "Extra", "date": "2026-08-06"},
        ], "total_pages": 1}
        service = ReleaseMonitorService(
            repository=repository,
            client_func=lambda **kwargs: payload,
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        )
        first = service.run()
        second = service.run()
        self.assertEqual(first.releases_inserted, 1)
        self.assertEqual(first.releases_unmatched, 1)
        self.assertEqual(second.releases_already_known, 1)

    def test_concurrent_run_returns_already_running(self):
        repository = FakeRepository()
        repository.running = True
        result = ReleaseMonitorService(repository=repository).run()
        self.assertEqual(result.status, "already_running")


if __name__ == "__main__":
    unittest.main()

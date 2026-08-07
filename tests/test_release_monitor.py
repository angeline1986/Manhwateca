import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

from manhwateca.release_monitor.parser import (
    parse_external_releases,
    parse_external_releases_with_stats,
)
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
        return [
            {"manga_id": 10, "work_code": "123", "title": "Obra A"},
            {"manga_id": 390, "work_code": "39054810010", "title": "Accidental Baby (Luharang)"},
        ]

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

    def test_parser_reads_record_and_metadata_series_id(self):
        releases, stats = parse_external_releases_with_stats({
            "results": [_release_item(chapter="29.5", volume=None)]
        })
        self.assertEqual(stats["releases_received"], 1)
        self.assertEqual(stats["releases_parsed"], 1)
        self.assertEqual(stats["releases_with_series_metadata"], 1)
        self.assertEqual(releases[0].series_id, 39054810010)
        self.assertEqual(releases[0].chapter, "29.5")
        self.assertEqual(releases[0].release_date, date(2026, 8, 6))
        self.assertIsNone(releases[0].volume)
        self.assertEqual(releases[0].external_release_id, "123")
        self.assertEqual(releases[0].source_url, "https://www.mangaupdates.com/series/example")

    def test_parser_preserves_textual_chapters_and_all_groups(self):
        releases = parse_external_releases({
            "results": [_release_item(
                chapter="Side Story 4",
                groups=[{"name": "Group B"}, {"name": "Group A"}],
            )]
        })
        self.assertEqual(releases[0].chapter, "Side Story 4")
        self.assertEqual(releases[0].group_name, "Group A, Group B")

    def test_parser_counts_missing_metadata_and_invalid_dates(self):
        _releases, stats = parse_external_releases_with_stats({
            "results": [
                {"record": {"id": 1, "chapter": "Extra", "release_date": "2026-08-06"}},
                _release_item(release_date="not-a-date"),
            ]
        })
        self.assertEqual(stats["releases_missing_series_metadata"], 1)
        self.assertEqual(stats["releases_invalid"], 1)
        self.assertEqual(stats["releases_parsed"], 0)

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

    def test_service_matches_complete_item_by_work_code(self):
        repository = FakeRepository()
        payload = {"results": [_release_item()], "total_pages": 1}
        service = ReleaseMonitorService(
            repository=repository,
            client_func=lambda **kwargs: payload,
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        )
        result = service.run()
        self.assertEqual(result.releases_received, 1)
        self.assertEqual(result.releases_parsed, 1)
        self.assertEqual(result.releases_with_series_metadata, 1)
        self.assertEqual(result.monitored_series_count, 2)
        self.assertEqual(result.releases_matched, 1)
        self.assertEqual(result.releases_inserted, 1)

    def test_service_marks_missing_metadata_response_as_partial_success(self):
        repository = FakeRepository()
        payload = {"results": [{"record": {"id": 1, "chapter": "Special", "release_date": "2026-08-06"}}], "total_pages": 1}
        service = ReleaseMonitorService(
            repository=repository,
            client_func=lambda **kwargs: payload,
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        )
        result = service.run()
        self.assertEqual(result.status, "partial_success")
        self.assertEqual(result.releases_missing_series_metadata, 1)
        self.assertEqual(result.releases_parsed, 0)

    def test_concurrent_run_returns_already_running(self):
        repository = FakeRepository()
        repository.running = True
        result = ReleaseMonitorService(repository=repository).run()
        self.assertEqual(result.status, "already_running")


if __name__ == "__main__":
    unittest.main()


def _release_item(
    *,
    release_id=123,
    series_id=39054810010,
    title="Accidental Baby (Luharang)",
    chapter="29",
    volume="",
    release_date="2026-08-06",
    groups=None,
):
    return {
        "record": {
            "id": release_id,
            "title": title,
            "volume": volume,
            "chapter": chapter,
            "groups": groups if groups is not None else [
                {
                    "name": "Group A",
                    "group_id": 1,
                    "url": "https://www.mangaupdates.com/group/example",
                }
            ],
            "release_date": release_date,
            "time_added": {},
        },
        "metadata": {
            "series": {
                "series_id": series_id,
                "title": title,
                "url": "https://www.mangaupdates.com/series/example",
            }
        },
    }

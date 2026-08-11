import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

from manhwateca.release_monitor.parser import (
    parse_external_releases,
    parse_external_releases_with_stats,
)
from manhwateca.release_monitor import repository as repository_module
from manhwateca.release_monitor.models import ExternalRelease
from manhwateca.release_monitor.repository import ReleaseMonitorRepository
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
            release.external_series_id,
            release.release_date,
            release.chapter.casefold(),
            (release.group_name or "").casefold(),
            (release.volume or "").casefold(),
        )
        inserted = key not in self.rows
        self.rows[key] = release
        return inserted


class CapturingCursor:
    def __init__(self):
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _sql, params=None):
        self.params = params

    def fetchone(self):
        return {"id": 1, "inserted": True}


class CapturingConnection:
    def __init__(self):
        self.cursor_instance = CapturingCursor()

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        pass


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
        self.assertEqual(releases[0].provider, "mangaupdates")
        self.assertEqual(releases[0].external_series_id, "39054810010")
        self.assertEqual(releases[0].chapter, "29.5")
        self.assertEqual(releases[0].release_date, date(2026, 8, 6))
        self.assertIsNone(releases[0].volume)
        self.assertEqual(releases[0].external_release_id, "123")
        self.assertEqual(releases[0].source_url, "https://www.mangaupdates.com/series/example")

    def test_parser_accepts_string_external_series_id(self):
        external_id = "eede42a0-78a1-413d-8cb6-3a03ec365e2b"
        releases = parse_external_releases({
            "results": [{
                "id": "rel-uuid",
                "series_id": external_id,
                "chapter": "1",
                "date": "2026-08-06",
            }]
        })
        self.assertEqual(releases[0].external_series_id, external_id)

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

    def test_service_stops_when_period_is_exhausted_before_page_ten(self):
        repository = FakeRepository()
        payloads = {
            1: {"results": [_release_item(release_id="in-month", release_date="2026-08-06")]},
            2: {"results": [_release_item(release_id="old", release_date="2026-07-31")]},
        }
        seen_pages = []
        service = ReleaseMonitorService(
            repository=repository,
            client_func=lambda page, **_kwargs: seen_pages.append(page) or payloads[page],
            now_func=lambda: datetime(2026, 8, 7, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        )
        result = service.run()
        self.assertEqual(seen_pages, [1, 2])
        self.assertEqual(result.pages_requested, 2)
        self.assertEqual(result.stop_reason, "period_exhausted")
        self.assertEqual(result.releases_inserted, 1)

    def test_service_does_not_stop_at_page_ten_when_month_continues(self):
        repository = FakeRepository()
        payloads = {
            page: {"results": [_release_item(release_id=f"month-{page}", release_date="2026-08-02")]}
            for page in range(1, 13)
        }
        payloads[13] = {"results": [_release_item(release_id="old", release_date="2026-07-31")]}
        seen_pages = []
        service = ReleaseMonitorService(
            repository=repository,
            client_func=lambda page, **_kwargs: seen_pages.append(page) or payloads[page],
            now_func=lambda: datetime(2026, 8, 7, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        )
        result = service.run()
        self.assertEqual(seen_pages, list(range(1, 14)))
        self.assertEqual(result.pages_requested, 13)
        self.assertEqual(result.stop_reason, "period_exhausted")
        self.assertEqual(result.releases_inserted, 12)
        self.assertEqual(len(repository.rows), 12)

    def test_service_stops_on_empty_results_page(self):
        repository = FakeRepository()
        result = ReleaseMonitorService(
            repository=repository,
            client_func=lambda **_kwargs: {"results": []},
            now_func=lambda: datetime(2026, 8, 7, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run()
        self.assertEqual(result.pages_requested, 1)
        self.assertEqual(result.stop_reason, "empty_page")
        self.assertEqual(result.releases_received, 0)

    def test_service_stops_when_api_has_no_results_collection(self):
        repository = FakeRepository()
        result = ReleaseMonitorService(
            repository=repository,
            client_func=lambda **_kwargs: {"total_hits": 0},
            now_func=lambda: datetime(2026, 8, 7, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run()
        self.assertEqual(result.pages_requested, 1)
        self.assertEqual(result.stop_reason, "empty_page")

    def test_service_reports_safety_limit_when_period_never_ends(self):
        repository = FakeRepository()
        result = ReleaseMonitorService(
            repository=repository,
            client_func=lambda page, **_kwargs: {
                "results": [_release_item(release_id=f"rel-{page}", release_date="2026-08-06")]
            },
            now_func=lambda: datetime(2026, 8, 7, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run(max_pages=3)
        self.assertEqual(result.pages_requested, 3)
        self.assertEqual(result.stop_reason, "safety_limit")
        self.assertEqual(result.releases_inserted, 3)

    def test_service_keeps_month_release_after_page_ten(self):
        repository = FakeRepository()

        def client(page, **_kwargs):
            if page == 12:
                return {"results": [_release_item(release_id="late-month", release_date="2026-08-01")]}
            if page == 13:
                return {"results": [_release_item(release_id="old", release_date="2026-07-31")]}
            return {"results": [_release_item(release_id=f"other-{page}", series_id=456, release_date="2026-08-02")]}

        result = ReleaseMonitorService(
            repository=repository,
            client_func=client,
            now_func=lambda: datetime(2026, 8, 7, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run()
        self.assertEqual(result.pages_requested, 13)
        self.assertEqual(result.stop_reason, "period_exhausted")
        self.assertEqual(result.releases_matched, 1)
        self.assertEqual(result.releases_inserted, 1)

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

    def test_repository_wraps_source_payload_for_jsonb(self):
        class JsonbSentinel:
            def __init__(self, value):
                self.value = value

        connection = CapturingConnection()
        original_jsonb = repository_module.Jsonb
        repository_module.Jsonb = JsonbSentinel
        try:
            release = ExternalRelease(
                provider="mangaupdates",
                external_series_id="39845325740",
                external_release_id="rel-1",
                chapter="1",
                volume=None,
                release_date=date(2026, 8, 6),
                group_name="Grupo",
                source_url=None,
                raw_payload={"record": {"chapter": "1"}},
            )
            ReleaseMonitorRepository(connection=connection).upsert_release(release, 10)
        finally:
            repository_module.Jsonb = original_jsonb

        payload_param = connection.cursor_instance.params[-1]
        self.assertIsInstance(payload_param, JsonbSentinel)
        self.assertEqual(payload_param.value["record"]["chapter"], "1")

    def test_repository_converts_mangaupdates_external_series_id_to_bigint(self):
        connection = CapturingConnection()
        release = ExternalRelease(
            provider="mangaupdates",
            external_series_id="39845325740",
            external_release_id="rel-1",
            chapter="1",
            release_date=date(2026, 8, 6),
        )
        ReleaseMonitorRepository(connection=connection).upsert_release(release, 10)
        self.assertEqual(connection.cursor_instance.params[1], 39845325740)

    def test_repository_rejects_non_numeric_mangaupdates_external_series_id(self):
        connection = CapturingConnection()
        release = ExternalRelease(
            provider="mangaupdates",
            external_series_id="eede42a0-78a1-413d-8cb6-3a03ec365e2b",
            external_release_id="rel-1",
            chapter="1",
            release_date=date(2026, 8, 6),
        )
        with self.assertRaises(ValueError):
            ReleaseMonitorRepository(connection=connection).upsert_release(release, 10)


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

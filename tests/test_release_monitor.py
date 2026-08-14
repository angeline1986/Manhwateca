import unittest
from pathlib import Path
from datetime import date, datetime
from zoneinfo import ZoneInfo

from manhwateca.release_monitor.parser import (
    parse_external_releases,
    parse_external_releases_with_stats,
)
from manhwateca.release_monitor import repository as repository_module
from manhwateca.release_monitor.models import ExternalRelease
from manhwateca.release_monitor.providers import (
    MangaUpdatesReleaseProvider,
    ReleaseProviderPage,
)
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


class ExternalReleaseCursor:
    def __init__(self, connection):
        self.connection = connection
        self.row = None
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        self.params = params
        normalized = " ".join(sql.split()).casefold()
        if normalized.startswith("insert into external_releases"):
            self.row = self.connection.upsert_external_release(normalized, params)

    def fetchone(self):
        return self.row


class ExternalReleaseConnection:
    def __init__(self):
        self.rows = []
        self.cursor_instance = ExternalReleaseCursor(self)
        self.commits = []
        self.clock = 0

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commits.append(True)

    def upsert_external_release(self, sql, params):
        with_external_id = "nullif(%s, '')" in sql
        if with_external_id:
            (
                manga_id,
                provider,
                external_series_id,
                external_release_id,
                volume,
                chapter,
                normalized_volume,
                normalized_chapter,
                release_date,
                language,
                title,
                source_url,
                raw_payload,
            ) = params
        else:
            (
                manga_id,
                provider,
                external_series_id,
                volume,
                chapter,
                normalized_volume,
                normalized_chapter,
                release_date,
                language,
                title,
                source_url,
                raw_payload,
            ) = params
            external_release_id = None
        if external_release_id:
            existing = next(
                (
                    row for row in self.rows
                    if row["provider"] == provider
                    and row["external_release_id"] == external_release_id
                ),
                None,
            )
        else:
            existing = next(
                (
                    row for row in self.rows
                    if row["provider"] == provider
                    and row["external_series_id"] == external_series_id
                    and row["release_date"] == release_date
                    and row["normalized_chapter"] == normalized_chapter
                    and row["normalized_volume"] == normalized_volume
                    and row["external_release_id"] is None
                ),
                None,
            )
        inserted = existing is None
        if inserted:
            self.clock += 1
            existing = {
                "id": len(self.rows) + 1,
                "first_seen_at": f"seen-{self.clock}",
                "viewed_at": None,
            }
            self.rows.append(existing)
        else:
            self.clock += 1
        existing.update({
            "manga_id": existing.get("manga_id") or manga_id,
            "provider": provider,
            "external_series_id": external_series_id,
            "external_release_id": external_release_id,
            "volume": volume,
            "chapter": chapter,
            "normalized_volume": normalized_volume,
            "normalized_chapter": normalized_chapter,
            "release_date": release_date,
            "language": language,
            "title": title,
            "source_url": source_url,
            "raw_payload": raw_payload,
            "last_seen_at": f"seen-{self.clock}",
        })
        return {"id": existing["id"], "inserted": inserted}


class FakeProvider:
    def __init__(self, pages):
        self.pages = pages
        self.seen_pages = []

    def fetch_page(self, page):
        self.seen_pages.append(page)
        return self.pages[page]


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

    def test_mangaupdates_provider_fetches_normalizes_and_reports_next_page(self):
        provider = MangaUpdatesReleaseProvider(
            client_func=lambda page, **_kwargs: {
                "results": [_release_item(release_id=f"rel-{page}")],
                "total_pages": 2,
            }
        )
        page = provider.fetch_page(1)
        self.assertTrue(page.has_results_collection)
        self.assertTrue(page.has_next_page)
        self.assertEqual(page.stats["releases_received"], 1)
        self.assertEqual(page.releases[0].provider, "mangaupdates")
        self.assertEqual(page.releases[0].external_series_id, "39054810010")

    def test_service_uses_provider_page_contract(self):
        repository = FakeRepository()
        provider = FakeProvider({
            1: ReleaseProviderPage(
                releases=[
                    ExternalRelease(
                        provider="mangaupdates",
                        external_series_id="123",
                        chapter="1",
                        release_date=date(2026, 8, 6),
                        external_release_id="rel-1",
                    )
                ],
                stats={
                    "releases_received": 1,
                    "releases_parsed": 1,
                    "releases_with_series_metadata": 1,
                    "releases_missing_series_metadata": 0,
                    "releases_invalid": 0,
                },
                has_results_collection=True,
                has_next_page=False,
            )
        })
        result = ReleaseMonitorService(
            repository=repository,
            provider=provider,
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run()
        self.assertEqual(provider.seen_pages, [1])
        self.assertEqual(result.stop_reason, "end_of_results")
        self.assertEqual(result.releases_inserted, 1)

    def test_service_does_not_import_mangaupdates_client_directly(self):
        source = Path("manhwateca/release_monitor/service.py").read_text(encoding="utf-8")
        self.assertNotIn("mangaupdates_service.client", source)
        self.assertNotIn("list_releases_by_day", source)

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

    def test_upserts_external_release_with_mangadex_uuid_and_release_id(self):
        connection = ExternalReleaseConnection()
        release = ExternalRelease(
            provider="mangadex",
            external_series_id="eede42a0-78a1-413d-8cb6-3a03ec365e2b",
            external_release_id="release-uuid-123",
            chapter="29",
            volume=None,
            release_date=date(2026, 8, 6),
            language="pt-br",
            title="Capítulo 29",
            raw_payload={"id": "release-uuid-123"},
        )

        inserted = ReleaseMonitorRepository(connection=connection).upsert_external_release(
            release,
            390,
        )

        self.assertTrue(inserted)
        row = connection.rows[0]
        self.assertEqual(row["provider"], "mangadex")
        self.assertEqual(row["external_series_id"], "eede42a0-78a1-413d-8cb6-3a03ec365e2b")
        self.assertEqual(row["external_release_id"], "release-uuid-123")
        self.assertEqual(row["language"], "pt-br")
        self.assertEqual(row["raw_payload"], {"id": "release-uuid-123"})

    def test_external_release_keeps_mangaupdates_series_id_as_text(self):
        connection = ExternalReleaseConnection()
        release = ExternalRelease(
            provider="mangaupdates",
            external_series_id="39054810010",
            external_release_id=None,
            chapter="29",
            release_date=date(2026, 8, 6),
        )

        ReleaseMonitorRepository(connection=connection).upsert_external_release(release, 390)

        self.assertEqual(connection.rows[0]["external_series_id"], "39054810010")

    def test_external_release_accepts_decimal_textual_and_null_chapters(self):
        connection = ExternalReleaseConnection()
        repository = ReleaseMonitorRepository(connection=connection)
        for index, chapter in enumerate(("10", "10.5", "extra", None), start=1):
            repository.upsert_external_release(
                ExternalRelease(
                    provider="mangadex",
                    external_series_id="manga-uuid",
                    external_release_id=f"release-{index}",
                    chapter=chapter,
                    release_date=date(2026, 8, 6),
                ),
                390,
            )

        self.assertEqual(
            [row["chapter"] for row in connection.rows],
            ["10", "10.5", "extra", None],
        )
        self.assertEqual(connection.rows[-1]["normalized_chapter"], "")

    def test_duplicate_mangadex_external_release_updates_last_seen_only(self):
        connection = ExternalReleaseConnection()
        repository = ReleaseMonitorRepository(connection=connection)
        release = ExternalRelease(
            provider="mangadex",
            external_series_id="manga-uuid",
            external_release_id="release-uuid-123",
            chapter="29",
            release_date=date(2026, 8, 6),
        )

        first = repository.upsert_external_release(release, 390)
        connection.rows[0]["viewed_at"] = "viewed"
        first_seen = connection.rows[0]["first_seen_at"]
        second = repository.upsert_external_release(release, 390)

        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(len(connection.rows), 1)
        self.assertEqual(connection.rows[0]["first_seen_at"], first_seen)
        self.assertEqual(connection.rows[0]["viewed_at"], "viewed")
        self.assertEqual(connection.rows[0]["last_seen_at"], "seen-2")

    def test_duplicate_without_external_release_id_uses_fallback_key(self):
        connection = ExternalReleaseConnection()
        repository = ReleaseMonitorRepository(connection=connection)
        release = ExternalRelease(
            provider="mangaupdates",
            external_series_id="39054810010",
            external_release_id=None,
            chapter="29",
            volume=None,
            release_date=date(2026, 8, 6),
        )

        first = repository.upsert_external_release(release, 390)
        second = repository.upsert_external_release(release, 390)

        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(len(connection.rows), 1)

    def test_same_chapter_can_coexist_across_providers(self):
        connection = ExternalReleaseConnection()
        repository = ReleaseMonitorRepository(connection=connection)
        for provider, series_id, release_id in (
            ("mangaupdates", "39054810010", None),
            ("mangadex", "manga-uuid", "release-uuid-123"),
        ):
            repository.upsert_external_release(
                ExternalRelease(
                    provider=provider,
                    external_series_id=series_id,
                    external_release_id=release_id,
                    chapter="29",
                    release_date=date(2026, 8, 6),
                ),
                390,
            )

        self.assertEqual(len(connection.rows), 2)
        self.assertEqual({row["provider"] for row in connection.rows}, {
            "mangaupdates",
            "mangadex",
        })


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

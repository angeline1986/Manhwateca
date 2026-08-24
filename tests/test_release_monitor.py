import unittest
from pathlib import Path
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import patch
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
from manhwateca.release_monitor.mangadex_execution import MangaDexExecutionResult
from manhwateca.release_monitor.service import (
    MangaDexMonitorExecutor,
    MangaUpdatesMonitorExecutor,
    ReleaseMonitorService,
    current_periods,
)
from manhwateca.webapp.actions import SAFE_ACTIONS, build_command
from manhwateca.webapp import releases as web_releases


class FakeRepository:
    def __init__(self, subscriptions=None):
        self.running = False
        self.rows = {}
        self.external_rows = {}
        self.finished = []
        self.subscriptions = subscriptions
        self.checked = []
        self.requested_manga_id = None

    def active_run(self):
        return {"id": 99, "started_at": datetime(2026, 8, 6, tzinfo=ZoneInfo("UTC"))} if self.running else None

    def start_run(self, reference_date, timezone):
        return None if self.running else 1

    def finish_run(self, run_id, status, metrics, error_message=None):
        self.finished.append((status, dict(metrics), error_message))

    def latest_run(self):
        return {"started_at": datetime(2026, 8, 6, 13, tzinfo=ZoneInfo("UTC")), "finished_at": datetime(2026, 8, 6, 13, 1, tzinfo=ZoneInfo("UTC"))}

    def list_active_subscriptions(self, manga_id=None):
        self.requested_manga_id = manga_id
        if self.subscriptions is not None:
            subscriptions = self.subscriptions
        else:
            subscriptions = [
                {"manga_id": 10, "work_code": "123", "title": "Obra A"},
                {"manga_id": 390, "work_code": "39054810010", "title": "Accidental Baby (Luharang)"},
            ]
        if manga_id is not None:
            return [
                row for row in subscriptions
                if int(row.get("manga_id") or 0) == int(manga_id)
            ]
        return subscriptions

    def mark_subscriptions_checked(self, manga_ids, success=True, error_message=None):
        self.checked.append((list(manga_ids), success, error_message))

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

    def upsert_external_release(self, release, manga_id):
        key = (release.provider, release.external_release_id)
        inserted = key not in self.external_rows
        self.external_rows[key] = (release, manga_id)
        return inserted


class FakeExternalRefRepository:
    def __init__(self, refs_by_manga):
        self.refs_by_manga = refs_by_manga
        self.seen_manga_ids = []

    def list_external_refs(self, manga_id):
        self.seen_manga_ids.append(manga_id)
        return list(self.refs_by_manga.get(manga_id, []))


class FakeMangaDexProcess:
    def __init__(self, results_by_external_id):
        self.results_by_external_id = results_by_external_id
        self.calls = []

    def __call__(self, manga_id, mangadex_id, **kwargs):
        self.calls.append((manga_id, mangadex_id, kwargs))
        result = self.results_by_external_id[mangadex_id]
        return result(manga_id, mangadex_id, kwargs) if callable(result) else result


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
        self.connection.current_sql = normalized
        if normalized.startswith("insert into external_releases"):
            self.row = self.connection.upsert_external_release(normalized, params)
        elif normalized.startswith("select count(*) filter"):
            self.row = self.connection.release_summary(params)
        elif normalized.startswith("select count(*) as total from external_releases"):
            self.row = {"total": len(self.connection.filtered_rows(params))}
        elif normalized.startswith("select r.*, m.title from external_releases"):
            self.connection.result_rows = self.connection.list_release_rows(params)
        elif normalized.startswith("update external_releases"):
            self.row = self.connection.mark_viewed(normalized, params)

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.connection.result_rows


class ExternalReleaseConnection:
    def __init__(self):
        self.rows = []
        self.mangas = {}
        self.cursor_instance = ExternalReleaseCursor(self)
        self.commits = []
        self.clock = 0
        self.result_rows = []

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
                release_group,
                normalized_release_group,
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
                release_group,
                normalized_release_group,
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
                    and row["normalized_release_group"] == normalized_release_group
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
            "release_group": release_group,
            "normalized_release_group": normalized_release_group,
            "source_url": source_url,
            "raw_payload": getattr(raw_payload, "obj", raw_payload),
            "last_seen_at": f"seen-{self.clock}",
        })
        return {"id": existing["id"], "inserted": inserted}

    def release_summary(self, periods):
        rows = [row for row in self.rows if row.get("manga_id") is not None]
        return {
            "today_chapters": count_between(rows, periods["today_start"], periods["today_end"]),
            "today_releases": count_between(rows, periods["today_start"], periods["today_end"]),
            "today_works": works_between(rows, periods["today_start"], periods["today_end"]),
            "today_unseen": unseen_between(rows, periods["today_start"], periods["today_end"]),
            "week_chapters": count_between(rows, periods["week_start"], periods["week_end"]),
            "week_releases": count_between(rows, periods["week_start"], periods["week_end"]),
            "week_works": works_between(rows, periods["week_start"], periods["week_end"]),
            "week_unseen": unseen_between(rows, periods["week_start"], periods["week_end"]),
            "month_chapters": count_between(rows, periods["month_start"], periods["month_end"]),
            "month_releases": count_between(rows, periods["month_start"], periods["month_end"]),
            "month_works": works_between(rows, periods["month_start"], periods["month_end"]),
            "month_unseen": unseen_between(rows, periods["month_start"], periods["month_end"]),
        }

    def filtered_rows(self, params):
        start_date, end_date = params[0], params[1]
        rows = [
            row for row in self.rows
            if row.get("manga_id") is not None
            and start_date <= row["release_date"] <= end_date
        ]
        if "r.viewed_at is null" in self.current_sql:
            rows = [row for row in rows if row.get("viewed_at") is None]
        rest = list(params[2:])
        if rest and isinstance(rest[0], str) and rest[0].startswith("%"):
            left, right = rest.pop(0), rest.pop(0)
            search = left.strip("%").casefold()
            rows = [
                row for row in rows
                if search in self.mangas.get(row["manga_id"], {}).get("title", "").casefold()
                or search in self.mangas.get(row["manga_id"], {}).get("alternative_title", "").casefold()
            ]
        if rest and not isinstance(rest[0], int):
            manga_id = rest.pop(0)
            rows = [row for row in rows if row["manga_id"] == manga_id]
        return rows

    def list_release_rows(self, params):
        *filter_params, per_page, offset = params
        rows = self.filtered_rows(tuple(filter_params))
        rows = sorted(
            rows,
            key=lambda row: (
                row["release_date"],
                row["first_seen_at"],
                self.mangas.get(row["manga_id"], {}).get("title", ""),
                row["normalized_chapter"],
            ),
            reverse=True,
        )
        page = rows[offset:offset + per_page]
        return [
            {
                **row,
                "title": self.mangas.get(row["manga_id"], {}).get("title"),
            }
            for row in page
        ]

    def mark_viewed(self, sql, params):
        if "where id = %s" in sql:
            rows = [row for row in self.rows if row["id"] == params[0]]
        else:
            start_date, end_date = params
            rows = [
                row for row in self.rows
                if start_date <= row["release_date"] <= end_date
            ]
        for row in rows:
            row["viewed_at"] = row["viewed_at"] or "viewed-now"
        return {"changed": len(rows)} if rows else None


class FakeProvider:
    def __init__(self, pages):
        self.pages = pages
        self.seen_pages = []

    def fetch_page(self, page):
        self.seen_pages.append(page)
        return self.pages[page]


def ref(provider, external_id):
    return SimpleNamespace(provider=provider, external_id=external_id)


def count_between(rows, start_date, end_date):
    return sum(1 for row in rows if start_date <= row["release_date"] <= end_date)


def works_between(rows, start_date, end_date):
    return len({
        row["manga_id"] for row in rows
        if start_date <= row["release_date"] <= end_date
    })


def unseen_between(rows, start_date, end_date):
    return sum(
        1 for row in rows
        if start_date <= row["release_date"] <= end_date and row.get("viewed_at") is None
    )


class ReleaseMonitorTests(unittest.TestCase):
    def test_favorite_migration_adds_default_false_column(self):
        sql = Path(
            "manhwateca/database/migrations/016_release_monitor_favorites.sql"
        ).read_text(encoding="utf-8").casefold()

        self.assertIn("alter table manhwateca.release_monitor_subscriptions", sql)
        self.assertIn("favorite boolean not null default false", sql)

    def test_days_range_uses_inclusive_window(self):
        periods = current_periods(
            datetime(2026, 8, 24, 12, tzinfo=ZoneInfo("America/Sao_Paulo"))
        )

        period, start, end = web_releases._range_from_args({"days": ["15"]}, periods)

        self.assertEqual("15d", period)
        self.assertEqual(date(2026, 8, 10), start)
        self.assertEqual(date(2026, 8, 24), end)

    def test_days_one_returns_today_and_period_still_works(self):
        periods = current_periods(
            datetime(2026, 8, 24, 12, tzinfo=ZoneInfo("America/Sao_Paulo"))
        )

        one = web_releases._range_from_args({"days": ["1"]}, periods)
        month = web_releases._range_from_args({"period": ["month"]}, periods)

        self.assertEqual((date(2026, 8, 24), date(2026, 8, 24)), one[1:])
        self.assertEqual("month", month[0])
        self.assertEqual(date(2026, 8, 1), month[1])

    def test_invalid_days_raises_route_error(self):
        periods = current_periods(
            datetime(2026, 8, 24, 12, tzinfo=ZoneInfo("America/Sao_Paulo"))
        )

        with self.assertRaises(web_releases.ReleaseMonitorRouteError):
            web_releases._range_from_args({"days": ["0"]}, periods)

    def test_check_parameters_accepts_optional_manga_id(self):
        self.assertEqual(({}, 202), web_releases.check_parameters_payload({}))
        self.assertEqual(
            ({"manga_id": 7}, 202),
            web_releases.check_parameters_payload({"manga_id": "7"}),
        )

        payload, status = web_releases.check_parameters_payload({"manga_id": "abc"})

        self.assertEqual(400, status)
        self.assertIn("error", payload)

    def test_release_check_command_keeps_general_and_accepts_manga_id(self):
        config = SAFE_ACTIONS["release_check"]

        self.assertEqual(
            ["scripts/check_releases.py"],
            build_command(config, {}),
        )
        self.assertEqual(
            ["scripts/check_releases.py", "--manga-id", "12"],
            build_command(config, {"manga_id": 12}),
        )

    def test_update_favorite_payload_persists_true_and_false(self):
        class FavoriteRepository:
            def __init__(self):
                self.values = {}

            def update_favorite(self, manga_id, favorite):
                self.values[manga_id] = favorite
                return {"manga_id": manga_id, "favorite": favorite}

        repository = FavoriteRepository()

        with patch.object(web_releases, "ReleaseMonitorRepository", return_value=repository):
            enabled, enabled_status = web_releases.update_favorite_payload({
                "manga_id": "12",
                "favorite": "true",
            })
            disabled, disabled_status = web_releases.update_favorite_payload({
                "manga_id": "12",
                "favorite": "false",
            })

        self.assertEqual(200, enabled_status)
        self.assertEqual({"manga_id": 12, "favorite": True}, enabled)
        self.assertEqual(200, disabled_status)
        self.assertEqual({"manga_id": 12, "favorite": False}, disabled)
        self.assertFalse(repository.values[12])

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

    def test_service_with_manga_id_processes_only_that_subscription(self):
        repository = FakeRepository(subscriptions=[
            {"manga_id": 1, "work_code": "mu-a", "title": "Obra A"},
            {"manga_id": 2, "work_code": "mu-b", "title": "Obra B"},
        ])
        provider = FakeProvider({
            1: ReleaseProviderPage(
                releases=[
                    ExternalRelease("mangaupdates", "mu-a", "1", date(2026, 8, 6), external_release_id="a"),
                    ExternalRelease("mangaupdates", "mu-b", "1", date(2026, 8, 6), external_release_id="b"),
                ],
                stats={
                    "releases_received": 2,
                    "releases_parsed": 2,
                    "releases_with_series_metadata": 2,
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
            external_ref_repository=FakeExternalRefRepository({}),
            provider_executors=[MangaUpdatesMonitorExecutor(provider)],
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run(manga_id=2)

        self.assertEqual(2, repository.requested_manga_id)
        self.assertEqual(["b"], list(repository.rows))
        self.assertEqual([([2], True, None)], repository.checked)
        self.assertEqual(1, result.monitored_series_count)

    def test_service_with_unknown_manga_id_does_not_run_general_check(self):
        repository = FakeRepository(subscriptions=[
            {"manga_id": 1, "work_code": "mu-a", "title": "Obra A"},
        ])
        provider = FakeProvider({})

        result = ReleaseMonitorService(
            repository=repository,
            provider=provider,
            external_ref_repository=FakeExternalRefRepository({}),
            provider_executors=[MangaUpdatesMonitorExecutor(provider)],
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run(manga_id=999)

        self.assertEqual(999, repository.requested_manga_id)
        self.assertEqual([], provider.seen_pages)
        self.assertEqual([], repository.checked)
        self.assertEqual(0, result.monitored_series_count)

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

    def test_service_processes_mangaupdates_mangadex_and_mangadex_only_refs(self):
        subscriptions = [
            {"manga_id": 1, "work_code": "mu-a", "title": "Obra A"},
            {"manga_id": 2, "work_code": "mu-b", "title": "Obra B"},
            {"manga_id": 3, "work_code": None, "title": "Obra C", "enabled": True},
        ]
        repository = FakeRepository(subscriptions=subscriptions)
        refs = FakeExternalRefRepository({
            1: [ref("mangaupdates", "mu-a"), ref("mangadex", "md-a")],
            2: [ref("mangaupdates", "mu-b")],
            3: [ref("mangadex", "md-c")],
        })
        provider = FakeProvider({
            1: ReleaseProviderPage(
                releases=[
                    ExternalRelease("mangaupdates", "mu-a", "1", date(2026, 8, 6), external_release_id="mu-rel-a"),
                    ExternalRelease("mangaupdates", "mu-b", "2", date(2026, 8, 6), external_release_id="mu-rel-b"),
                ],
                stats={
                    "releases_received": 2,
                    "releases_parsed": 2,
                    "releases_with_series_metadata": 2,
                    "releases_missing_series_metadata": 0,
                    "releases_invalid": 0,
                },
                has_results_collection=True,
                has_next_page=False,
            )
        })
        mangadex_process = FakeMangaDexProcess({
            "md-a": MangaDexExecutionResult(
                manga_id=1,
                external_series_id="md-a",
                status="success",
                pages_requested=1,
                items_received=1,
                releases_normalized=1,
                releases_inserted=1,
                stop_reason="end_of_feed",
            ),
            "md-c": MangaDexExecutionResult(
                manga_id=3,
                external_series_id="md-c",
                status="success",
                pages_requested=1,
                items_received=1,
                releases_normalized=1,
                releases_inserted=1,
                stop_reason="end_of_feed",
            ),
        })

        result = ReleaseMonitorService(
            repository=repository,
            provider=provider,
            external_ref_repository=refs,
            provider_executors=[
                MangaUpdatesMonitorExecutor(provider),
                MangaDexMonitorExecutor(mangadex_process),
            ],
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run()

        self.assertEqual("success", result.status)
        self.assertEqual(provider.seen_pages, [1])
        self.assertEqual([(1, "md-a"), (3, "md-c")], [
            (manga_id, mangadex_id) for manga_id, mangadex_id, _kwargs in mangadex_process.calls
        ])
        self.assertEqual({("mu-rel-a"), ("mu-rel-b")}, set(repository.rows))
        self.assertEqual(result.provider_metrics["mangaupdates"]["works_consulted"], 2)
        self.assertEqual(result.provider_metrics["mangadex"]["works_consulted"], 2)
        self.assertEqual(result.provider_metrics["mangadex"]["releases_inserted"], 2)
        self.assertEqual(refs.seen_manga_ids, [1, 2, 3])

    def test_service_runs_mangadex_only_when_explicitly_eligible(self):
        repository = FakeRepository(subscriptions=[
            {"manga_id": 3, "work_code": None, "title": "Obra C", "enabled": True},
        ])
        refs = FakeExternalRefRepository({3: [ref("mangadex", "md-c")]})
        provider = FakeProvider({})
        mangadex_process = FakeMangaDexProcess({
            "md-c": MangaDexExecutionResult(
                manga_id=3,
                external_series_id="md-c",
                status="success",
                pages_requested=1,
                items_received=1,
                releases_normalized=1,
                releases_inserted=1,
                stop_reason="end_of_feed",
            )
        })

        result = ReleaseMonitorService(
            repository=repository,
            provider=provider,
            external_ref_repository=refs,
            provider_executors=[
                MangaDexMonitorExecutor(mangadex_process),
            ],
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run()

        self.assertEqual("success", result.status)
        self.assertEqual([(3, "md-c")], [
            (manga_id, mangadex_id) for manga_id, mangadex_id, _kwargs in mangadex_process.calls
        ])
        self.assertEqual(0, result.monitored_series_count)
        self.assertEqual(1, result.provider_metrics["mangadex"]["works_consulted"])

    def test_service_skips_unknown_provider_without_external_call(self):
        repository = FakeRepository(subscriptions=[
            {"manga_id": 1, "work_code": None, "title": "Obra"},
        ])
        refs = FakeExternalRefRepository({1: [ref("provider_inexistente", "abc")]})
        provider = FakeProvider({})

        result = ReleaseMonitorService(
            repository=repository,
            provider=provider,
            external_ref_repository=refs,
            provider_executors=[],
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run()

        self.assertEqual("partial_success", result.status)
        self.assertEqual(1, result.provider_metrics["unknown"]["references_skipped"])

    def test_mangadex_failure_does_not_stop_mangaupdates_or_other_works(self):
        repository = FakeRepository(subscriptions=[
            {"manga_id": 1, "work_code": "mu-a", "title": "Obra A"},
            {"manga_id": 2, "work_code": "mu-b", "title": "Obra B"},
        ])
        refs = FakeExternalRefRepository({
            1: [ref("mangaupdates", "mu-a"), ref("mangadex", "md-a")],
            2: [ref("mangaupdates", "mu-b")],
        })
        provider = FakeProvider({
            1: ReleaseProviderPage(
                releases=[
                    ExternalRelease("mangaupdates", "mu-a", "1", date(2026, 8, 6), external_release_id="mu-a"),
                    ExternalRelease("mangaupdates", "mu-b", "1", date(2026, 8, 6), external_release_id="mu-b"),
                ],
                stats={
                    "releases_received": 2,
                    "releases_parsed": 2,
                    "releases_with_series_metadata": 2,
                    "releases_missing_series_metadata": 0,
                    "releases_invalid": 0,
                },
                has_results_collection=True,
                has_next_page=False,
            )
        })
        mangadex_process = FakeMangaDexProcess({
            "md-a": MangaDexExecutionResult(
                manga_id=1,
                external_series_id="md-a",
                status="failed",
                failures=1,
                stop_reason="error",
                error_message="MangaDex indisponível",
            )
        })

        result = ReleaseMonitorService(
            repository=repository,
            provider=provider,
            external_ref_repository=refs,
            provider_executors=[
                MangaUpdatesMonitorExecutor(provider),
                MangaDexMonitorExecutor(mangadex_process),
            ],
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run()

        self.assertEqual("partial_success", result.status)
        self.assertEqual(2, result.releases_inserted)
        self.assertEqual(1, result.provider_metrics["mangadex"]["failures"])
        self.assertIn("mangadex: MangaDex indisponível", result.error_message)

    def test_mangaupdates_failure_does_not_stop_mangadex(self):
        repository = FakeRepository(subscriptions=[
            {"manga_id": 1, "work_code": "mu-a", "title": "Obra A"},
        ])
        refs = FakeExternalRefRepository({
            1: [ref("mangaupdates", "mu-a"), ref("mangadex", "md-a")],
        })

        class FailingProvider:
            def fetch_page(self, _page):
                raise RuntimeError("MangaUpdates indisponível")

        mangadex_process = FakeMangaDexProcess({
            "md-a": MangaDexExecutionResult(
                manga_id=1,
                external_series_id="md-a",
                status="success",
                pages_requested=1,
                items_received=1,
                releases_normalized=1,
                releases_inserted=1,
                stop_reason="end_of_feed",
            )
        })

        result = ReleaseMonitorService(
            repository=repository,
            provider=FailingProvider(),
            external_ref_repository=refs,
            provider_executors=[
                MangaUpdatesMonitorExecutor(FailingProvider()),
                MangaDexMonitorExecutor(mangadex_process),
            ],
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run()

        self.assertEqual("partial_success", result.status)
        self.assertEqual([(1, "md-a")], [
            (manga_id, mangadex_id) for manga_id, mangadex_id, _kwargs in mangadex_process.calls
        ])
        self.assertEqual(1, result.provider_metrics["mangaupdates"]["failures"])
        self.assertEqual(1, result.provider_metrics["mangadex"]["releases_inserted"])

    def test_service_reports_failed_when_all_executed_providers_fail(self):
        repository = FakeRepository(subscriptions=[
            {"manga_id": 1, "work_code": "mu-a", "title": "Obra A"},
        ])
        refs = FakeExternalRefRepository({
            1: [ref("mangaupdates", "mu-a"), ref("mangadex", "md-a")],
        })

        class FailingProvider:
            def fetch_page(self, _page):
                raise RuntimeError("MangaUpdates indisponível")

        mangadex_process = FakeMangaDexProcess({
            "md-a": MangaDexExecutionResult(
                manga_id=1,
                external_series_id="md-a",
                status="failed",
                failures=1,
                stop_reason="error",
                error_message="MangaDex indisponível",
            )
        })

        result = ReleaseMonitorService(
            repository=repository,
            provider=FailingProvider(),
            external_ref_repository=refs,
            provider_executors=[
                MangaUpdatesMonitorExecutor(FailingProvider()),
                MangaDexMonitorExecutor(mangadex_process),
            ],
            now_func=lambda: datetime(2026, 8, 6, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run()

        self.assertEqual("failed", result.status)
        self.assertIn("mangaupdates: MangaUpdates indisponível", result.error_message)
        self.assertIn("mangadex: MangaDex indisponível", result.error_message)

    def test_service_does_not_include_api_specific_calls(self):
        source = Path("manhwateca/release_monitor/service.py").read_text(encoding="utf-8")
        self.assertNotIn("/manga/", source)
        self.assertNotIn("/releases/days", source)
        self.assertNotIn("list_releases_by_day", source)
        self.assertIn("process_manga", source)

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

    def test_fallback_key_keeps_mangaupdates_release_groups_distinct(self):
        connection = ExternalReleaseConnection()
        repository = ReleaseMonitorRepository(connection=connection)
        for group in ("Grupo A", "Grupo B"):
            repository.upsert_external_release(
                ExternalRelease(
                    provider="mangaupdates",
                    external_series_id="39054810010",
                    external_release_id=None,
                    chapter="29",
                    group_name=group,
                    release_date=date(2026, 8, 6),
                ),
                390,
            )

        self.assertEqual(len(connection.rows), 2)
        self.assertEqual(
            {row["release_group"] for row in connection.rows},
            {"Grupo A", "Grupo B"},
        )

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

    def test_dashboard_summary_reads_external_releases(self):
        connection = ExternalReleaseConnection()
        connection.mangas = {
            1: {"title": "Alpha", "alternative_title": ""},
            2: {"title": "Beta", "alternative_title": ""},
        }
        repository = ReleaseMonitorRepository(connection=connection)
        repository.upsert_external_release(
            ExternalRelease("mangaupdates", "111", "1", date(2026, 8, 14), external_release_id="mu-1"),
            1,
        )
        repository.upsert_external_release(
            ExternalRelease("mangadex", "md-1", "1", date(2026, 8, 13), external_release_id="md-1", language="pt-br"),
            1,
        )
        repository.upsert_external_release(
            ExternalRelease("mangadex", "md-2", "extra", date(2026, 8, 1), external_release_id="md-2", language="en"),
            2,
        )
        connection.rows[1]["viewed_at"] = "viewed"
        periods = current_periods(datetime(2026, 8, 14, 12, tzinfo=ZoneInfo("America/Sao_Paulo")))

        counts, _latest = repository.release_summary(periods, "America/Sao_Paulo")

        self.assertEqual(1, counts["today_chapters"])
        self.assertEqual(2, counts["week_chapters"])
        self.assertEqual(3, counts["month_chapters"])
        self.assertEqual(1, counts["today_works"])
        self.assertEqual(1, counts["week_unseen"])
        self.assertEqual(2, counts["month_unseen"])

    def test_dashboard_list_reads_external_releases_with_filters_order_and_pagination(self):
        connection = ExternalReleaseConnection()
        connection.mangas = {
            1: {"title": "Alpha", "alternative_title": "Primeira"},
            2: {"title": "Beta", "alternative_title": ""},
        }
        repository = ReleaseMonitorRepository(connection=connection)
        repository.upsert_external_release(
            ExternalRelease("mangaupdates", "111", "10.5", date(2026, 8, 14), external_release_id="mu-1", group_name="Grupo"),
            1,
        )
        repository.upsert_external_release(
            ExternalRelease("mangadex", "md-1", "extra", date(2026, 8, 13), external_release_id="md-1", language="en"),
            2,
        )
        repository.upsert_external_release(
            ExternalRelease("mangadex", "md-2", "texto", date(2026, 8, 12), external_release_id="md-2", language="pt-br"),
            1,
        )
        connection.rows[2]["viewed_at"] = "viewed"

        result = repository.list_releases(
            date(2026, 8, 1),
            date(2026, 8, 31),
            search="alpha",
            page=1,
            per_page=1,
        )
        unseen = repository.list_releases(
            date(2026, 8, 1),
            date(2026, 8, 31),
            unseen_only=True,
            page=1,
            per_page=20,
        )

        self.assertEqual(2, result["total"])
        self.assertEqual(["10.5"], [row["chapter"] for row in result["items"]])
        self.assertEqual("Grupo", result["items"][0]["release_group"])
        self.assertEqual(2, unseen["total"])
        self.assertEqual({"10.5", "extra"}, {row["chapter"] for row in unseen["items"]})

    def test_mark_viewed_updates_external_releases_by_id_and_period(self):
        connection = ExternalReleaseConnection()
        repository = ReleaseMonitorRepository(connection=connection)
        repository.upsert_external_release(
            ExternalRelease("mangaupdates", "111", "1", date(2026, 8, 14), external_release_id="mu-1"),
            1,
        )
        repository.upsert_external_release(
            ExternalRelease("mangadex", "md-1", "2", date(2026, 8, 14), external_release_id="md-1"),
            1,
        )

        by_id = repository.mark_viewed(release_id=connection.rows[0]["id"])
        by_period = repository.mark_viewed(start_date=date(2026, 8, 14), end_date=date(2026, 8, 14))

        self.assertEqual(1, by_id)
        self.assertEqual(2, by_period)
        self.assertTrue(all(row["viewed_at"] for row in connection.rows))

    def test_mangaupdates_executor_writes_legacy_and_external_tables(self):
        repository = FakeRepository(subscriptions=[
            {"manga_id": 1, "work_code": "mu-a", "title": "Obra A"},
        ])
        provider = FakeProvider({
            1: ReleaseProviderPage(
                releases=[
                    ExternalRelease(
                        "mangaupdates",
                        "mu-a",
                        "29",
                        date(2026, 8, 14),
                        external_release_id="mu-rel",
                        group_name="Grupo",
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
            external_ref_repository=FakeExternalRefRepository({}),
            provider_executors=[MangaUpdatesMonitorExecutor(provider)],
            now_func=lambda: datetime(2026, 8, 14, 12, tzinfo=ZoneInfo("America/Sao_Paulo")),
        ).run()

        self.assertEqual("success", result.status)
        self.assertEqual(["mu-rel"], list(repository.rows))
        self.assertEqual([("mangaupdates", "mu-rel")], list(repository.external_rows))


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

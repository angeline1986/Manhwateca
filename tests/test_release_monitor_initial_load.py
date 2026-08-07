import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime
from zoneinfo import ZoneInfo

from manhwateca.webapp import releases


class EmptyRepository:
    def release_summary(self, periods, timezone):
        return {}, None

    def list_releases(self, *args, **kwargs):
        return {"items": [], "total": 0}


class BrokenRepository:
    def release_summary(self, periods, timezone):
        raise RuntimeError("database unavailable")


class MissingTableRepository:
    def release_summary(self, periods, timezone):
        raise RuntimeError('relation "mangaupdates_releases" does not exist')

    def list_releases(self, *args, **kwargs):
        raise RuntimeError('relation "mangaupdates_releases" does not exist')


class ChapterCountRepository:
    def release_summary(self, periods, timezone):
        return {
            "today_chapters": 3,
            "today_releases": 3,
            "today_works": 2,
            "today_unseen": 3,
            "week_chapters": 5,
            "week_releases": 5,
            "week_works": 2,
            "week_unseen": 5,
            "month_chapters": 7,
            "month_releases": 7,
            "month_works": 3,
            "month_unseen": 7,
        }, None


class ExistingRunRepository:
    def release_summary(self, periods, timezone):
        return {}, {
            "id": 2,
            "status": "success",
            "started_at": datetime(2026, 8, 6, 23, 20, tzinfo=ZoneInfo("America/Sao_Paulo")),
            "finished_at": datetime(2026, 8, 6, 23, 21, tzinfo=ZoneInfo("America/Sao_Paulo")),
            "error_message": None,
        }


class SubscriptionRepository:
    def __init__(self):
        pass

    def update_subscription(self, manga_id, enabled, monitor_mode="releases"):
        return {
            "id": 1,
            "manga_id": manga_id,
            "enabled": enabled,
            "monitor_mode": monitor_mode,
            "created_at": datetime(2026, 8, 6, 23, 46, tzinfo=ZoneInfo("America/Sao_Paulo")),
            "updated_at": datetime(2026, 8, 6, 23, 47, tzinfo=ZoneInfo("America/Sao_Paulo")),
        }


class ReleaseMonitorInitialLoadTests(unittest.TestCase):
    def test_summary_route_payload_is_json_ready(self):
        with patch.object(releases, "ReleaseMonitorRepository", EmptyRepository):
            payload = releases.dashboard_releases_summary()
        self.assertEqual(payload["today"]["release_count"], 0)
        self.assertEqual(payload["today"]["chapter_count"], 0)
        self.assertEqual(payload["week"]["work_count"], 0)
        self.assertEqual(payload["month"]["unseen_count"], 0)
        self.assertEqual(payload["timezone"], "America/Sao_Paulo")

    def test_summary_returns_latest_monitor_run_when_it_exists(self):
        with patch.object(releases, "ReleaseMonitorRepository", ExistingRunRepository):
            payload = releases.dashboard_releases_summary()
        self.assertEqual(payload["last_monitor_run"]["id"], 2)
        self.assertEqual(payload["last_monitor_run"]["status"], "success")
        self.assertEqual(
            payload["last_monitor_run"]["finished_at"],
            "2026-08-06T23:21:00-03:00",
        )

    def test_two_chapters_from_same_work_count_separately(self):
        with patch.object(releases, "ReleaseMonitorRepository", ChapterCountRepository):
            payload = releases.dashboard_releases_summary()
        self.assertEqual(payload["today"]["chapter_count"], 3)
        self.assertEqual(payload["today"]["release_count"], 3)
        self.assertEqual(payload["today"]["work_count"], 2)

    def test_missing_tables_return_zero_summary(self):
        with patch.object(releases, "ReleaseMonitorRepository", MissingTableRepository):
            payload = releases.dashboard_releases_summary()
        self.assertEqual(payload["today"]["release_count"], 0)
        self.assertIn("warning", payload)

    def test_repository_error_returns_controlled_exception(self):
        with patch.object(releases, "ReleaseMonitorRepository", BrokenRepository):
            with self.assertRaises(releases.ReleaseMonitorRouteError) as context:
                releases.dashboard_releases_summary()
        self.assertEqual(context.exception.status, 503)
        self.assertIn("resumo de lançamentos", str(context.exception))

    def test_update_subscription_serializes_datetimes(self):
        with patch.object(releases, "ReleaseMonitorRepository", SubscriptionRepository):
            payload, status = releases.update_subscription_payload({
                "manga_id": 5,
                "enabled": True,
                "monitor_mode": "releases",
            })
        self.assertEqual(status, 200)
        self.assertTrue(payload["subscription"]["enabled"])
        self.assertEqual(payload["subscription"]["created_at"], "2026-08-06T23:46:00-03:00")

    def test_frontend_uses_relative_urls_and_network_message(self):
        api = Path("web/js/api/releasesApi.js").read_text(encoding="utf-8")
        client = Path("web/js/api/client.js").read_text(encoding="utf-8")
        self.assertIn('getJson("/api/dashboard/releases-summary")', api)
        self.assertIn('getJson(`/api/releases?', api)
        self.assertNotIn("localhost", api)
        self.assertNotIn("127.0.0.1", api)
        self.assertIn("Não foi possível acessar o servidor da Manhwateca.", client)

    def test_frontend_renders_cards_and_click_changes_period(self):
        page = Path("web/js/pages/overviewPage.js").read_text(encoding="utf-8")
        self.assertIn('["month", "week", "today"].map(period => releaseCard', page)
        self.assertIn('data-release-card="${period}"', page)
        self.assertIn("setReleasePeriod(button.dataset.releaseCard)", page)
        self.assertIn('let releasePeriod = "today"', page)
        self.assertIn("Capítulos disponíveis hoje", page)
        self.assertIn("chapter_count", page)
        self.assertNotIn("em ${data.work_count", page)
        self.assertNotIn("${data.unseen_count", page)
        self.assertIn('if (!run) return "Monitor ainda não executado"', page)
        self.assertIn("Última verificação:", page)

    def test_frontend_list_title_and_columns_are_chapter_focused(self):
        html = Path("web/index.html").read_text(encoding="utf-8")
        self.assertIn("<h3>Capítulos disponíveis</h3>", html)
        self.assertIn("<th>Data de lançamento</th>", html)
        self.assertNotIn("<h3>Lançamentos recentes</h3>", html)
        self.assertNotIn("<th>Ação</th>", html)


if __name__ == "__main__":
    unittest.main()

from calendar import monthrange
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from manhwateca.release_monitor.models import (
    TIMEZONE,
    ReleaseMonitorPeriods,
    ReleaseMonitorResult,
)
from manhwateca.release_monitor.providers import MangaUpdatesReleaseProvider
from manhwateca.release_monitor.repository import ReleaseMonitorRepository


def current_periods(now=None, timezone=TIMEZONE):
    tz = ZoneInfo(timezone)
    current = (now or datetime.now(tz)).astimezone(tz).date()
    week_start = current - timedelta(days=current.weekday())
    last_day = monthrange(current.year, current.month)[1]
    return ReleaseMonitorPeriods(
        today_start=current,
        today_end=current,
        week_start=week_start,
        week_end=week_start + timedelta(days=6),
        month_start=current.replace(day=1),
        month_end=current.replace(day=last_day),
    )


class ReleaseMonitorService:
    def __init__(
        self,
        repository=None,
        provider=None,
        client_func=None,
        now_func=None,
        timezone=TIMEZONE,
    ):
        self.repository = repository or ReleaseMonitorRepository()
        self.provider = provider or MangaUpdatesReleaseProvider(client_func=client_func)
        self.now_func = now_func
        self.timezone = timezone

    def run(self, max_pages=100):
        tz = ZoneInfo(self.timezone)
        now = self.now_func() if self.now_func else datetime.now(tz)
        periods = current_periods(now, self.timezone)
        run_id = self.repository.start_run(periods.today_start, self.timezone)
        if run_id is None:
            active = self.repository.active_run() or {}
            return ReleaseMonitorResult(
                status="already_running",
                run_id=active.get("id"),
                started_at=active.get("started_at"),
                finished_at=None,
                error_message="Monitor de lançamentos já está em execução.",
            )

        metrics = {
            "pages_requested": 0,
            "monitored_series_count": 0,
            "releases_received": 0,
            "releases_parsed": 0,
            "releases_in_period": 0,
            "releases_with_series_metadata": 0,
            "releases_missing_series_metadata": 0,
            "releases_matched": 0,
            "releases_inserted": 0,
            "releases_already_known": 0,
            "releases_unmatched": 0,
            "releases_invalid": 0,
            "earliest_release_date": None,
            "latest_release_date": None,
            "stop_reason": None,
        }
        status = "success"
        error_message = None
        try:
            subscriptions = self.repository.list_active_subscriptions()
            by_series = {
                str(row["work_code"]).strip(): row["manga_id"]
                for row in subscriptions
                if str(row.get("work_code") or "").strip()
            }
            metrics["monitored_series_count"] = len(by_series)
            previous_oldest_date = None
            descending_order_observed = True
            for page in range(1, max_pages + 1):
                metrics["pages_requested"] += 1
                provider_page = self.provider.fetch_page(page)
                if not provider_page.has_results_collection:
                    metrics["stop_reason"] = "empty_page"
                    break
                for key, value in provider_page.stats.items():
                    metrics[key] += value
                if not provider_page.stats["releases_received"]:
                    metrics["stop_reason"] = "empty_page"
                    break
                releases = provider_page.releases
                page_dates = [release.release_date for release in releases]
                if page_dates:
                    page_newest = max(page_dates)
                    page_oldest = min(page_dates)
                    if previous_oldest_date is not None and page_newest > previous_oldest_date:
                        descending_order_observed = False
                    previous_oldest_date = page_oldest
                    metrics["earliest_release_date"] = (
                        page_oldest
                        if metrics["earliest_release_date"] is None
                        else min(metrics["earliest_release_date"], page_oldest)
                    )
                    metrics["latest_release_date"] = (
                        page_newest
                        if metrics["latest_release_date"] is None
                        else max(metrics["latest_release_date"], page_newest)
                    )
                for release in releases:
                    if release.release_date < periods.earliest_start:
                        continue
                    metrics["releases_in_period"] += 1
                    manga_id = by_series.get(release.external_series_id)
                    if manga_id is None:
                        metrics["releases_unmatched"] += 1
                        continue
                    metrics["releases_matched"] += 1
                    if self.repository.upsert_release(release, manga_id):
                        metrics["releases_inserted"] += 1
                    else:
                        metrics["releases_already_known"] += 1
                if (
                    page_dates
                    and descending_order_observed
                    and max(page_dates) < periods.earliest_start
                ):
                    metrics["stop_reason"] = "period_exhausted"
                    break
                if (
                    not provider_page.stats["releases_received"]
                    or not provider_page.has_next_page
                ):
                    metrics["stop_reason"] = "end_of_results"
                    break
            else:
                metrics["stop_reason"] = "safety_limit"
            if metrics["releases_received"] and not metrics["releases_parsed"]:
                status = "partial_success"
                error_message = "A API retornou itens, mas nenhum release pôde ser convertido com series_id e data válidos."
            elif metrics["releases_received"] and not metrics["releases_with_series_metadata"]:
                status = "partial_success"
                error_message = "A API retornou itens sem metadata.series.series_id."
            elif not metrics["monitored_series_count"]:
                status = "partial_success"
                error_message = "Nenhuma obra com ID MangaUpdates confirmado está habilitada para monitoramento."
        except Exception as error:
            status = "failed" if metrics["releases_received"] == 0 else "partial_success"
            error_message = _safe_error(error)
        self.repository.finish_run(run_id, status, metrics, error_message)
        latest = self.repository.latest_run() or {}
        return ReleaseMonitorResult(
            status=status,
            run_id=run_id,
            started_at=latest.get("started_at"),
            finished_at=latest.get("finished_at"),
            error_message=error_message,
            **metrics,
        )

def _safe_error(error):
    text = str(error).strip()
    if not text:
        return "Falha inesperada ao consultar lançamentos."
    return text[:500]

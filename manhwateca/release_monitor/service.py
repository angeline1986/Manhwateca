from calendar import monthrange
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from manhwateca.release_monitor.models import (
    TIMEZONE,
    ReleaseMonitorPeriods,
    ReleaseMonitorResult,
)
from manhwateca.database.manga_repository import MangaRepository
from manhwateca.release_monitor.mangadex_execution import process_manga
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
        external_ref_repository=None,
        provider_executors=None,
    ):
        self.repository = repository or ReleaseMonitorRepository()
        self.provider = provider or MangaUpdatesReleaseProvider(client_func=client_func)
        self.now_func = now_func
        self.timezone = timezone
        self.external_ref_repository = external_ref_repository
        if (
            self.external_ref_repository is None
            and isinstance(self.repository, ReleaseMonitorRepository)
        ):
            self.external_ref_repository = MangaRepository()
        self.provider_executors = (
            [
                MangaUpdatesMonitorExecutor(self.provider),
                MangaDexMonitorExecutor(),
            ]
            if provider_executors is None
            else provider_executors
        )

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
        provider_metrics = {}
        status = "success"
        error_message = None
        try:
            subscriptions = self.repository.list_active_subscriptions()
            work_refs = _resolve_work_refs(subscriptions, self.external_ref_repository)
            metrics["monitored_series_count"] = len({
                ref.external_id
                for refs in work_refs.values()
                for ref in refs
                if ref.provider == "mangaupdates"
            })
            known_providers = {executor.provider for executor in self.provider_executors}
            unknown_refs = [
                ref
                for refs in work_refs.values()
                for ref in refs
                if ref.provider not in known_providers
            ]
            if unknown_refs:
                provider_metrics["unknown"] = {
                    "references_skipped": len(unknown_refs),
                    "failures": 0,
                    "error_messages": [],
                }
            for executor in self.provider_executors:
                execution = executor.run(
                    subscriptions,
                    work_refs,
                    repository=self.repository,
                    periods=periods,
                    max_pages=max_pages,
                    now_func=self.now_func,
                )
                provider_metrics[executor.provider] = execution.provider_metrics
                _merge_metrics(metrics, execution.metrics)
                if execution.error_messages:
                    status = "partial_success"
            if not metrics["stop_reason"]:
                metrics["stop_reason"] = _combined_stop_reason(provider_metrics)
            if metrics["releases_received"] and not metrics["releases_parsed"]:
                status = "partial_success"
                error_message = "A API retornou itens, mas nenhum release pôde ser convertido com series_id e data válidos."
            elif metrics["releases_received"] and not metrics["releases_with_series_metadata"]:
                status = "partial_success"
                error_message = "A API retornou itens sem metadata.series.series_id."
            elif (
                not metrics["monitored_series_count"]
                and not _has_consulted_provider(provider_metrics, "mangadex")
            ):
                status = "partial_success"
                error_message = "Nenhuma obra com ID MangaUpdates confirmado está habilitada para monitoramento."
            provider_errors = _provider_error_message(provider_metrics)
            if provider_errors:
                status = "failed" if _all_executed_providers_failed(provider_metrics) else "partial_success"
                error_message = provider_errors if error_message is None else f"{error_message} {provider_errors}"
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
            provider_metrics=provider_metrics,
            **metrics,
        )


class ProviderExecution:
    def __init__(self, metrics=None, provider_metrics=None, error_messages=None):
        self.metrics = metrics or _empty_metrics()
        self.provider_metrics = provider_metrics or {}
        self.error_messages = error_messages or []


class MangaUpdatesMonitorExecutor:
    provider = "mangaupdates"

    def __init__(self, provider):
        self.release_provider = provider

    def run(self, _subscriptions, work_refs, *, repository, periods, max_pages, **_kwargs):
        metrics = _empty_metrics()
        provider_metrics = _empty_provider_metrics()
        by_series = {
            ref.external_id: manga_id
            for manga_id, refs in work_refs.items()
            for ref in refs
            if ref.provider == self.provider
        }
        provider_metrics["works_consulted"] = len(by_series)
        if not by_series:
            provider_metrics["stop_reason"] = "no_references"
            return ProviderExecution(metrics, provider_metrics)

        previous_oldest_date = None
        descending_order_observed = True
        try:
            for page in range(1, max_pages + 1):
                metrics["pages_requested"] += 1
                provider_metrics["pages_requested"] += 1
                provider_page = self.release_provider.fetch_page(page)
                if not provider_page.has_results_collection:
                    provider_metrics["stop_reason"] = "empty_page"
                    break
                for key, value in provider_page.stats.items():
                    metrics[key] += value
                provider_metrics["releases_received"] += provider_page.stats["releases_received"]
                provider_metrics["releases_normalized"] += provider_page.stats["releases_parsed"]
                if not provider_page.stats["releases_received"]:
                    provider_metrics["stop_reason"] = "empty_page"
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
                    if repository.upsert_release(release, manga_id):
                        metrics["releases_inserted"] += 1
                        provider_metrics["releases_inserted"] += 1
                    else:
                        metrics["releases_already_known"] += 1
                        provider_metrics["releases_already_known"] += 1
                if (
                    page_dates
                    and descending_order_observed
                    and max(page_dates) < periods.earliest_start
                ):
                    provider_metrics["stop_reason"] = "period_exhausted"
                    break
                if (
                    not provider_page.stats["releases_received"]
                    or not provider_page.has_next_page
                ):
                    provider_metrics["stop_reason"] = "end_of_results"
                    break
            else:
                provider_metrics["stop_reason"] = "safety_limit"
        except Exception as error:
            provider_metrics["failures"] += 1
            provider_metrics["error_messages"].append(_safe_error(error))
        metrics["stop_reason"] = provider_metrics["stop_reason"]
        return ProviderExecution(metrics, provider_metrics, provider_metrics["error_messages"])


class MangaDexMonitorExecutor:
    provider = "mangadex"

    def __init__(self, process_func=None):
        self.process_func = process_func or process_manga

    def run(self, _subscriptions, work_refs, *, repository, max_pages, now_func=None, **_kwargs):
        metrics = _empty_metrics()
        provider_metrics = _empty_provider_metrics()
        refs = [
            (manga_id, ref)
            for manga_id, refs in work_refs.items()
            for ref in refs
            if ref.provider == self.provider
        ]
        provider_metrics["works_consulted"] = len(refs)
        if not refs:
            provider_metrics["stop_reason"] = "no_references"
            return ProviderExecution(metrics, provider_metrics)
        for manga_id, ref in refs:
            result = self.process_func(
                manga_id,
                ref.external_id,
                release_repository=repository,
                max_pages=max_pages,
                now_func=now_func,
            )
            provider_metrics["pages_requested"] += result.pages_requested
            provider_metrics["releases_received"] += result.items_received
            provider_metrics["releases_normalized"] += result.releases_normalized
            provider_metrics["releases_inserted"] += result.releases_inserted
            provider_metrics["releases_already_known"] += result.releases_already_known
            provider_metrics["failures"] += result.failures
            if result.error_message:
                provider_metrics["error_messages"].append(result.error_message)
            metrics["pages_requested"] += result.pages_requested
            metrics["releases_received"] += result.items_received
            metrics["releases_parsed"] += result.releases_normalized
            metrics["releases_with_series_metadata"] += result.releases_normalized
            metrics["releases_invalid"] += result.releases_ignored
            metrics["releases_matched"] += result.releases_normalized
            metrics["releases_inserted"] += result.releases_inserted
            metrics["releases_already_known"] += result.releases_already_known
        provider_metrics["stop_reason"] = (
            "error"
            if provider_metrics["failures"]
            else "end_of_results"
        )
        return ProviderExecution(metrics, provider_metrics, provider_metrics["error_messages"])


class WorkExternalRef:
    def __init__(self, provider, external_id):
        self.provider = _safe_text(provider)
        self.external_id = _safe_text(external_id)


def _resolve_work_refs(subscriptions, external_ref_repository):
    work_refs = {}
    for row in subscriptions:
        manga_id = row["manga_id"]
        refs = []
        if external_ref_repository is not None:
            refs.extend(external_ref_repository.list_external_refs(manga_id))
        work_code = _safe_text(row.get("work_code"))
        if work_code and not _has_provider(refs, "mangaupdates"):
            refs.append(WorkExternalRef("mangaupdates", work_code))
        work_refs[manga_id] = [
            ref
            for ref in refs
            if _safe_text(getattr(ref, "provider", None))
            and _safe_text(getattr(ref, "external_id", None))
        ]
    return work_refs


def _has_provider(refs, provider):
    return any(_safe_text(getattr(ref, "provider", None)) == provider for ref in refs)


def _merge_metrics(target, source):
    for key, value in source.items():
        if key in {"earliest_release_date", "latest_release_date", "stop_reason"}:
            continue
        target[key] += value
    if source["earliest_release_date"] is not None:
        target["earliest_release_date"] = (
            source["earliest_release_date"]
            if target["earliest_release_date"] is None
            else min(target["earliest_release_date"], source["earliest_release_date"])
        )
    if source["latest_release_date"] is not None:
        target["latest_release_date"] = (
            source["latest_release_date"]
            if target["latest_release_date"] is None
            else max(target["latest_release_date"], source["latest_release_date"])
        )


def _empty_metrics():
    return {
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


def _empty_provider_metrics():
    return {
        "works_consulted": 0,
        "pages_requested": 0,
        "releases_received": 0,
        "releases_normalized": 0,
        "releases_inserted": 0,
        "releases_already_known": 0,
        "failures": 0,
        "stop_reason": None,
        "error_messages": [],
    }


def _combined_stop_reason(provider_metrics):
    reasons = {
        metrics.get("stop_reason")
        for metrics in provider_metrics.values()
        if metrics.get("stop_reason") and metrics.get("works_consulted", 0)
    }
    if not reasons:
        return None
    if "error" in reasons:
        return "partial_error"
    if len(reasons) == 1:
        return reasons.pop()
    return "multi_provider_complete"


def _provider_error_message(provider_metrics):
    messages = []
    for provider, metrics in provider_metrics.items():
        for message in metrics.get("error_messages", []):
            messages.append(f"{provider}: {message}")
    return " ".join(messages)[:500] if messages else None


def _all_executed_providers_failed(provider_metrics):
    executed = [
        metrics
        for provider, metrics in provider_metrics.items()
        if provider != "unknown" and metrics.get("works_consulted", 0)
    ]
    return bool(executed) and all(metrics.get("failures", 0) for metrics in executed)


def _has_consulted_provider(provider_metrics, provider):
    metrics = provider_metrics.get(provider) or {}
    return bool(metrics.get("works_consulted", 0))


def _safe_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_error(error):
    text = str(error).strip()
    if not text:
        return "Falha inesperada ao consultar lançamentos."
    return text[:500]

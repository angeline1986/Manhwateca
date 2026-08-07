from datetime import datetime
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

from manhwateca.release_monitor.models import TIMEZONE
from manhwateca.release_monitor.repository import ReleaseMonitorRepository
from manhwateca.release_monitor.service import current_periods


class ReleaseMonitorRouteError(RuntimeError):
    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status


def dashboard_releases_summary():
    periods = current_periods()
    repository = ReleaseMonitorRepository()
    warning = None
    try:
        counts, latest = repository.release_summary(periods, TIMEZONE)
        monitoring = repository.monitoring_overview()
    except Exception as error:
        if _is_missing_monitor_table(error):
            counts, latest, monitoring = {}, None, {}
            warning = "As tabelas do monitor de lançamentos ainda não foram criadas. Execute as migrations."
        else:
            raise ReleaseMonitorRouteError(
                "Não foi possível carregar o resumo de lançamentos."
            ) from error
    payload = {
        "generated_at": datetime.now(ZoneInfo(TIMEZONE)).isoformat(timespec="seconds"),
        "timezone": TIMEZONE,
        "today": _period_payload(periods.today_start, periods.today_end, counts, "today"),
        "week": _period_payload(periods.week_start, periods.week_end, counts, "week"),
        "month": _period_payload(periods.month_start, periods.month_end, counts, "month"),
        "last_monitor_run": _run_payload(latest),
        "monitoring": _monitoring_payload(monitoring),
    }
    if warning:
        payload["warning"] = warning
    return payload


def releases_payload(query):
    args = parse_qs(query)
    period = _period(args.get("period", ["today"])[0])
    periods = current_periods()
    start, end = _range_for(periods, period)
    page = _int(args.get("page", ["1"])[0], 1)
    per_page = min(100, max(1, _int(args.get("per_page", ["20"])[0], 20)))
    warning = None
    try:
        result = ReleaseMonitorRepository().list_releases(
            start,
            end,
            search=(args.get("search", [""])[0] or "").strip() or None,
            unseen_only=args.get("unseen_only", ["false"])[0] in {"1", "true", "sim"},
            manga_id=_int(args.get("manga_id", ["0"])[0], 0) or None,
            page=page,
            per_page=per_page,
        )
    except Exception as error:
        if _is_missing_monitor_table(error):
            result = {"items": [], "total": 0}
            warning = "As tabelas do monitor de lançamentos ainda não foram criadas. Execute as migrations."
        else:
            raise ReleaseMonitorRouteError(
                "Não foi possível carregar a lista de lançamentos."
            ) from error
    payload = {
        "period": period,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "page": page,
        "per_page": per_page,
        "total": result["total"],
        "items": [_release_item(row) for row in result["items"]],
    }
    if warning:
        payload["warning"] = warning
    return payload


def release_status_payload():
    repository = ReleaseMonitorRepository()
    active = repository.active_run()
    latest = repository.latest_run()
    return {"active_run": _run_payload(active), "last_monitor_run": _run_payload(latest)}


def subscriptions_payload():
    return {
        "items": [
            _subscription_overview_payload(row)
            for row in ReleaseMonitorRepository().list_subscription_overview()
        ]
    }


def update_subscription_payload(payload):
    manga_id = _int(payload.get("manga_id"), 0)
    if not manga_id:
        return {"error": "manga_id é obrigatório."}, 400
    row = ReleaseMonitorRepository().update_subscription(
        manga_id,
        bool(payload.get("enabled")),
        payload.get("monitor_mode") or "releases",
    )
    return {"subscription": _subscription_payload(row)}, 200


def mark_viewed_payload(payload):
    repository = ReleaseMonitorRepository()
    release_id = _int(payload.get("release_id"), 0)
    if release_id:
        changed = repository.mark_viewed(release_id=release_id)
    else:
        period = _period(payload.get("period", "today"))
        periods = current_periods()
        start, end = _range_for(periods, period)
        changed = repository.mark_viewed(start_date=start, end_date=end)
    return {"changed": changed}


def _period_payload(start, end, counts, prefix):
    chapter_count = int(counts.get(f"{prefix}_chapters") or counts.get(f"{prefix}_releases") or 0)
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "chapter_count": chapter_count,
        "release_count": chapter_count,
        "work_count": int(counts.get(f"{prefix}_works") or 0),
        "unseen_count": int(counts.get(f"{prefix}_unseen") or 0),
    }


def _run_payload(row):
    if not row:
        return None
    return {
        "id": row.get("id"),
        "status": row.get("status"),
        "started_at": _iso(row.get("started_at")),
        "finished_at": _iso(row.get("finished_at")),
        "error_message": row.get("error_message"),
    }


def _release_item(row):
    return {
        "id": row.get("id"),
        "manga_id": row.get("manga_id"),
        "title": row.get("title"),
        "chapter": row.get("chapter"),
        "volume": row.get("volume"),
        "release_group": row.get("release_group"),
        "release_date": _iso(row.get("release_date")),
        "first_seen_at": _iso(row.get("first_seen_at")),
        "viewed_at": _iso(row.get("viewed_at")),
        "status": "Visualizado" if row.get("viewed_at") else "Novo",
        "source_url": row.get("source_url"),
    }


def _subscription_payload(row):
    return {
        key: _iso(value)
        for key, value in dict(row).items()
    }


def _subscription_overview_payload(row):
    return {
        key: _iso(value)
        for key, value in dict(row).items()
    }


def _monitoring_payload(row):
    return {
        "eligible_count": int(row.get("eligible_count") or 0),
        "monitored_count": int(row.get("monitored_count") or 0),
        "forced_count": int(row.get("forced_count") or 0),
        "disabled_count": int(row.get("disabled_count") or 0),
        "auto_count": int(row.get("auto_count") or 0),
    }


def _range_for(periods, period):
    return {
        "today": (periods.today_start, periods.today_end),
        "week": (periods.week_start, periods.week_end),
        "month": (periods.month_start, periods.month_end),
    }[period]


def _period(value):
    return value if value in {"today", "week", "month"} else "today"


def _int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def _is_missing_monitor_table(error):
    if error.__class__.__name__ == "UndefinedTable":
        return True
    text = str(error).casefold()
    return (
        "mangaupdates_releases" in text
        or "release_monitor_runs" in text
        or "release_monitor_subscriptions" in text
    ) and ("does not exist" in text or "undefinedtable" in text)

from dataclasses import dataclass
from datetime import date, datetime


TIMEZONE = "America/Sao_Paulo"


@dataclass(frozen=True)
class ExternalRelease:
    series_id: int
    chapter: str
    release_date: date
    volume: str | None = None
    group_name: str | None = None
    external_release_id: str | None = None
    source_url: str | None = None
    raw_payload: dict | None = None


@dataclass(frozen=True)
class ReleaseMonitorPeriods:
    today_start: date
    today_end: date
    week_start: date
    week_end: date
    month_start: date
    month_end: date

    @property
    def earliest_start(self) -> date:
        return min(self.today_start, self.week_start, self.month_start)


@dataclass(frozen=True)
class ReleaseMonitorResult:
    status: str
    run_id: int | None
    started_at: datetime | None
    finished_at: datetime | None
    pages_requested: int = 0
    monitored_series_count: int = 0
    releases_received: int = 0
    releases_parsed: int = 0
    releases_in_period: int = 0
    releases_with_series_metadata: int = 0
    releases_missing_series_metadata: int = 0
    releases_matched: int = 0
    releases_inserted: int = 0
    releases_already_known: int = 0
    releases_unmatched: int = 0
    releases_invalid: int = 0
    earliest_release_date: date | None = None
    latest_release_date: date | None = None
    stop_reason: str | None = None
    error_message: str | None = None

    @property
    def ok(self) -> bool:
        return self.status in {"success", "partial_success"}

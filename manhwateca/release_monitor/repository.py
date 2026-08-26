import re
from datetime import datetime

from manhwateca.database.connection import connect

try:
    from psycopg.types.json import Jsonb
except ModuleNotFoundError:
    Jsonb = None


def normalize_key(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def jsonb_payload(value):
    return Jsonb(value) if Jsonb is not None else value


STALE_RUNNING_MINUTES = 2
STALE_RUNNING_ERROR = (
    "Execução running recuperada automaticamente após exceder "
    f"{STALE_RUNNING_MINUTES} minutos sem finalizar."
)


class ReleaseMonitorRepository:
    def __init__(self, connection=None, *, connection_factory=None):
        self.connection = connection
        self.connection_factory = connection_factory or connect

    def start_run(self, reference_date, timezone) -> int | None:
        self.recover_stale_runs()
        if self.active_run():
            return None
        row = self._fetch_one(
            """
            INSERT INTO release_monitor_runs(reference_date, timezone, status)
            VALUES (%s, %s, 'running')
            RETURNING id
            """,
            (reference_date, timezone),
        )
        self._commit()
        return row["id"]

    def recover_stale_runs(self):
        self._execute(
            """
            UPDATE release_monitor_runs
            SET status = 'failed',
                finished_at = now(),
                error_message = %s
            WHERE status = 'running'
              AND started_at < now() - (%s * interval '1 minute')
            """,
            (STALE_RUNNING_ERROR, STALE_RUNNING_MINUTES),
        )
        self._commit()

    def active_run(self):
        return self._fetch_one(
            """
            SELECT *
            FROM release_monitor_runs
            WHERE status = 'running'
            ORDER BY started_at DESC
            LIMIT 1
            """
        )

    def finish_run(self, run_id, status, metrics, error_message=None):
        self._execute(
            """
            UPDATE release_monitor_runs
            SET status = %s,
                finished_at = now(),
                pages_requested = %s,
                releases_received = %s,
                releases_in_period = %s,
                releases_matched = %s,
                releases_inserted = %s,
                releases_already_known = %s,
                releases_unmatched = %s,
                error_message = %s
            WHERE id = %s
            """,
            (
                status,
                metrics.get("pages_requested", 0),
                metrics.get("releases_received", 0),
                metrics.get("releases_in_period", 0),
                metrics.get("releases_matched", 0),
                metrics.get("releases_inserted", 0),
                metrics.get("releases_already_known", 0),
                metrics.get("releases_unmatched", 0),
                error_message,
                run_id,
            ),
        )
        self._commit()

    def latest_run(self):
        return self._fetch_one(
            """
            SELECT *
            FROM release_monitor_runs
            ORDER BY COALESCE(finished_at, started_at) DESC, id DESC
            LIMIT 1
            """
        )

    def list_active_subscriptions(self, manga_id=None):
        filters = [
            "COALESCE(s.enabled, TRUE) = TRUE",
            """
            (
                (m.work_code IS NOT NULL AND btrim(m.work_code) <> '')
                OR s.enabled = TRUE
            )
            """,
        ]
        params = []
        if manga_id:
            filters.append("m.id = %s")
            params.append(manga_id)
        return self._fetch_all(
            f"""
            SELECT
                s.id,
                m.id AS manga_id,
                COALESCE(s.enabled, TRUE) AS enabled,
                COALESCE(s.monitor_mode, 'auto') AS monitor_mode,
                COALESCE(s.favorite, FALSE) AS favorite,
                s.last_checked_at,
                s.last_success_at,
                s.last_error_at,
                s.last_error_message,
                s.created_at,
                s.updated_at,
                m.work_code,
                m.title
            FROM mangas m
            LEFT JOIN release_monitor_subscriptions s
                ON s.manga_id = m.id
            WHERE {" AND ".join(filters)}
            ORDER BY m.title
            """,
            tuple(params),
        )

    def list_subscription_overview(self):
        return self._fetch_all(
            """
            SELECT
                m.id AS manga_id,
                m.title,
                m.work_code,
                s.id AS subscription_id,
                s.enabled AS explicit_enabled,
                COALESCE(s.enabled, TRUE) AS monitored,
                COALESCE(s.monitor_mode, 'auto') AS monitor_mode,
                COALESCE(s.favorite, FALSE) AS favorite,
                s.last_checked_at,
                s.last_success_at,
                latest.chapter AS latest_release_chapter,
                latest.release_date AS latest_release_date,
                latest.release_group AS latest_release_group,
                s.created_at,
                s.updated_at
            FROM mangas m
            LEFT JOIN release_monitor_subscriptions s
                ON s.manga_id = m.id
            LEFT JOIN LATERAL (
                SELECT r.chapter, r.release_date, r.release_group
                FROM external_releases r
                WHERE r.manga_id = m.id
                ORDER BY r.release_date DESC, r.first_seen_at DESC, r.id DESC
                LIMIT 1
            ) latest ON TRUE
            WHERE m.work_code IS NOT NULL
              AND btrim(m.work_code) <> ''
            ORDER BY m.title
            """
        )

    def monitoring_overview(self):
        row = self._fetch_one(
            """
            SELECT
                count(*) AS eligible_count,
                count(*) FILTER (WHERE COALESCE(s.enabled, TRUE) = TRUE) AS monitored_count,
                count(*) FILTER (WHERE s.enabled = TRUE) AS forced_count,
                count(*) FILTER (WHERE s.enabled = FALSE) AS disabled_count,
                count(*) FILTER (WHERE s.id IS NULL) AS auto_count
            FROM mangas m
            LEFT JOIN release_monitor_subscriptions s
                ON s.manga_id = m.id
            WHERE m.work_code IS NOT NULL
              AND btrim(m.work_code) <> ''
            """
        )
        return row or {
            "eligible_count": 0,
            "monitored_count": 0,
            "forced_count": 0,
            "disabled_count": 0,
            "auto_count": 0,
        }

    def update_subscription(self, manga_id, enabled, monitor_mode="releases"):
        row = self._fetch_one(
            """
            INSERT INTO release_monitor_subscriptions(manga_id, enabled, monitor_mode)
            VALUES (%s, %s, %s)
            ON CONFLICT (manga_id)
            DO UPDATE SET enabled = EXCLUDED.enabled,
                          monitor_mode = EXCLUDED.monitor_mode
            RETURNING *
            """,
            (manga_id, enabled, monitor_mode),
        )
        self._commit()
        return row

    def update_favorite(self, manga_id, favorite):
        row = self._fetch_one(
            """
            INSERT INTO release_monitor_subscriptions(manga_id, enabled, monitor_mode, favorite)
            VALUES (%s, TRUE, 'releases', %s)
            ON CONFLICT (manga_id)
            DO UPDATE SET favorite = EXCLUDED.favorite
            RETURNING manga_id, favorite
            """,
            (manga_id, favorite),
        )
        self._commit()
        return row

    def mark_subscriptions_checked(self, manga_ids, success=True, error_message=None):
        ids = [int(manga_id) for manga_id in manga_ids if manga_id]
        if not ids:
            return 0
        if success:
            set_clause = """
                last_checked_at = now(),
                last_success_at = now(),
                last_error_at = NULL,
                last_error_message = NULL
            """
            params = (ids,)
        else:
            set_clause = """
                last_checked_at = now(),
                last_error_at = now(),
                last_error_message = %s
            """
            params = (error_message, ids)
        self._execute(
            """
            INSERT INTO release_monitor_subscriptions(manga_id, enabled, monitor_mode)
            SELECT unnest(%s::bigint[]), TRUE, 'releases'
            ON CONFLICT (manga_id) DO NOTHING
            """,
            (ids,),
        )
        rows = self._fetch_all(
            f"""
            UPDATE release_monitor_subscriptions
            SET {set_clause}
            WHERE manga_id = ANY(%s::bigint[])
            RETURNING manga_id
            """,
            params,
        )
        self._commit()
        return len(rows)

    def upsert_release(self, release, manga_id):
        mangaupdates_series_id = _mangaupdates_series_id(release)
        params = (
            manga_id,
            mangaupdates_series_id,
            release.external_release_id,
            release.volume,
            release.chapter,
            normalize_key(release.volume),
            normalize_key(release.chapter),
            release.release_date,
            release.group_name,
            normalize_key(release.group_name),
            release.source_url,
            jsonb_payload(release.raw_payload or {}),
        )
        row = self._fetch_one(
            """
            INSERT INTO mangaupdates_releases(
                manga_id, mangaupdates_series_id, external_release_id, volume,
                chapter, normalized_volume, normalized_chapter, release_date,
                release_group, normalized_release_group, source_url, source_payload
            )
            VALUES (%s, %s, NULLIF(%s, ''), %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (mangaupdates_series_id, external_release_id)
            WHERE external_release_id IS NOT NULL AND btrim(external_release_id) <> ''
            DO UPDATE SET last_seen_at = now(),
                          manga_id = COALESCE(mangaupdates_releases.manga_id, EXCLUDED.manga_id),
                          source_payload = EXCLUDED.source_payload
            RETURNING id, (xmax = 0) AS inserted
            """,
            params,
        ) if release.external_release_id else None
        if row is None:
            row = self._fetch_one(
                """
                INSERT INTO mangaupdates_releases(
                    manga_id, mangaupdates_series_id, external_release_id, volume,
                    chapter, normalized_volume, normalized_chapter, release_date,
                    release_group, normalized_release_group, source_url, source_payload
                )
                VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (
                    mangaupdates_series_id, release_date, normalized_chapter,
                    normalized_release_group, normalized_volume
                )
                WHERE external_release_id IS NULL OR btrim(external_release_id) = ''
                DO UPDATE SET last_seen_at = now(),
                              manga_id = COALESCE(mangaupdates_releases.manga_id, EXCLUDED.manga_id),
                              source_payload = EXCLUDED.source_payload
                RETURNING id, (xmax = 0) AS inserted
                """,
                (params[0], params[1], *params[3:]),
            )
        self._commit()
        return bool(row["inserted"])

    def upsert_external_release(self, release, manga_id):
        params = (
            manga_id,
            release.provider,
            release.external_series_id,
            release.external_release_id,
            release.volume,
            release.chapter,
            normalize_key(release.volume),
            normalize_key(release.chapter),
            release.release_date,
            release.language,
            release.title,
            release.group_name,
            normalize_key(release.group_name),
            release.source_url,
            jsonb_payload(release.raw_payload or {}),
        )
        row = self._fetch_one(
            """
            INSERT INTO external_releases(
                manga_id, provider, external_series_id, external_release_id,
                volume, chapter, normalized_volume, normalized_chapter,
                release_date, language, title, release_group,
                normalized_release_group, source_url, raw_payload
            )
            VALUES (%s, %s, %s, NULLIF(%s, ''), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (provider, external_release_id)
            WHERE external_release_id IS NOT NULL AND btrim(external_release_id) <> ''
            DO UPDATE SET last_seen_at = now(),
                          manga_id = COALESCE(external_releases.manga_id, EXCLUDED.manga_id),
                          external_series_id = EXCLUDED.external_series_id,
                          volume = EXCLUDED.volume,
                          chapter = EXCLUDED.chapter,
                          normalized_volume = EXCLUDED.normalized_volume,
                          normalized_chapter = EXCLUDED.normalized_chapter,
                          release_date = EXCLUDED.release_date,
                          language = EXCLUDED.language,
                          title = EXCLUDED.title,
                          release_group = EXCLUDED.release_group,
                          normalized_release_group = EXCLUDED.normalized_release_group,
                          source_url = EXCLUDED.source_url,
                          raw_payload = EXCLUDED.raw_payload
            RETURNING id, (xmax = 0) AS inserted
            """,
            params,
        ) if release.external_release_id else None
        if row is None:
            row = self._fetch_one(
                """
                INSERT INTO external_releases(
                    manga_id, provider, external_series_id, external_release_id,
                    volume, chapter, normalized_volume, normalized_chapter,
                    release_date, language, title, release_group,
                    normalized_release_group, source_url, raw_payload
                )
                VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (
                    provider, external_series_id, release_date,
                    normalized_chapter, normalized_release_group, normalized_volume
                )
                WHERE external_release_id IS NULL OR btrim(external_release_id) = ''
                DO UPDATE SET last_seen_at = now(),
                              manga_id = COALESCE(external_releases.manga_id, EXCLUDED.manga_id),
                              volume = EXCLUDED.volume,
                              chapter = EXCLUDED.chapter,
                              language = EXCLUDED.language,
                              title = EXCLUDED.title,
                              release_group = EXCLUDED.release_group,
                              normalized_release_group = EXCLUDED.normalized_release_group,
                              source_url = EXCLUDED.source_url,
                              raw_payload = EXCLUDED.raw_payload
                RETURNING id, (xmax = 0) AS inserted
                """,
                (params[0], params[1], params[2], *params[4:]),
            )
        self._commit()
        return bool(row["inserted"])

    def release_summary(self, periods, timezone):
        row = self._fetch_one(
            """
            SELECT
                count(*) FILTER (WHERE release_date BETWEEN %(today_start)s AND %(today_end)s) AS today_chapters,
                count(*) FILTER (WHERE release_date BETWEEN %(today_start)s AND %(today_end)s) AS today_releases,
                count(DISTINCT manga_id) FILTER (WHERE release_date BETWEEN %(today_start)s AND %(today_end)s) AS today_works,
                count(*) FILTER (WHERE viewed_at IS NULL AND release_date BETWEEN %(today_start)s AND %(today_end)s) AS today_unseen,
                count(*) FILTER (WHERE release_date BETWEEN %(week_start)s AND %(week_end)s) AS week_chapters,
                count(*) FILTER (WHERE release_date BETWEEN %(week_start)s AND %(week_end)s) AS week_releases,
                count(DISTINCT manga_id) FILTER (WHERE release_date BETWEEN %(week_start)s AND %(week_end)s) AS week_works,
                count(*) FILTER (WHERE viewed_at IS NULL AND release_date BETWEEN %(week_start)s AND %(week_end)s) AS week_unseen,
                count(*) FILTER (WHERE release_date BETWEEN %(month_start)s AND %(month_end)s) AS month_chapters,
                count(*) FILTER (WHERE release_date BETWEEN %(month_start)s AND %(month_end)s) AS month_releases,
                count(DISTINCT manga_id) FILTER (WHERE release_date BETWEEN %(month_start)s AND %(month_end)s) AS month_works,
                count(*) FILTER (WHERE viewed_at IS NULL AND release_date BETWEEN %(month_start)s AND %(month_end)s) AS month_unseen
            FROM external_releases
            WHERE manga_id IS NOT NULL
            """,
            periods.__dict__,
        ) or {}
        latest = self.latest_run()
        return row, latest

    def list_releases(self, start_date, end_date, search=None, unseen_only=False, manga_id=None, page=1, per_page=20):
        filters = ["r.manga_id IS NOT NULL", "r.release_date BETWEEN %s AND %s"]
        params = [start_date, end_date]
        if search:
            filters.append("(m.title ILIKE %s OR m.alternative_title ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        if unseen_only:
            filters.append("r.viewed_at IS NULL")
        if manga_id:
            filters.append("r.manga_id = %s")
            params.append(manga_id)
        where = " AND ".join(filters)
        total = self._fetch_one(
            f"SELECT count(*) AS total FROM external_releases r JOIN mangas m ON m.id = r.manga_id WHERE {where}",
            tuple(params),
        )["total"]
        rows = self._fetch_all(
            f"""
            SELECT r.*, m.title
            FROM external_releases r
            JOIN mangas m ON m.id = r.manga_id
            WHERE {where}
            ORDER BY r.release_date DESC, r.first_seen_at DESC, m.title, r.normalized_chapter
            LIMIT %s OFFSET %s
            """,
            (*params, per_page, max(0, page - 1) * per_page),
        )
        return {"items": rows, "total": total}

    def mark_viewed(self, release_id=None, start_date=None, end_date=None):
        if release_id:
            params = (release_id,)
            where = "id = %s"
        else:
            params = (start_date, end_date)
            where = "release_date BETWEEN %s AND %s"
        row = self._fetch_one(
            f"""
            UPDATE external_releases
            SET viewed_at = COALESCE(viewed_at, now())
            WHERE {where}
            RETURNING count(*) OVER() AS changed
            """,
            params,
        )
        self._commit()
        return int(row["changed"]) if row else 0

    def _connection(self):
        if self.connection is None:
            self.connection = self.connection_factory()
        return self.connection

    def _fetch_one(self, sql, params=None):
        with self._connection().cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()

    def _fetch_all(self, sql, params=None):
        with self._connection().cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()

    def _execute(self, sql, params=None):
        with self._connection().cursor() as cursor:
            cursor.execute(sql, params or ())

    def _commit(self):
        if self.connection is not None:
            self.connection.commit()


def _mangaupdates_series_id(release) -> int:
    if release.provider != "mangaupdates":
        raise ValueError(f"Provider não suportado nesta tabela: {release.provider}")
    text = str(release.external_series_id or "").strip()
    if not text.isdigit():
        raise ValueError("ID externo MangaUpdates deve ser numérico.")
    return int(text)

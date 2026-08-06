import re
from datetime import datetime

from manhwateca.database.connection import connect


def normalize_key(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


class ReleaseMonitorRepository:
    def __init__(self, connection=None, *, connection_factory=None):
        self.connection = connection
        self.connection_factory = connection_factory or connect

    def start_run(self, reference_date, timezone) -> int | None:
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
            ORDER BY started_at DESC
            LIMIT 1
            """
        )

    def list_active_subscriptions(self):
        return self._fetch_all(
            """
            SELECT s.*, m.work_code, m.title
            FROM release_monitor_subscriptions s
            JOIN mangas m ON m.id = s.manga_id
            WHERE s.enabled = TRUE
              AND m.work_code IS NOT NULL
              AND btrim(m.work_code) <> ''
            ORDER BY m.title
            """
        )

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

    def upsert_release(self, release, manga_id):
        params = (
            manga_id,
            release.series_id,
            release.external_release_id,
            release.volume,
            release.chapter,
            normalize_key(release.volume),
            normalize_key(release.chapter),
            release.release_date,
            release.group_name,
            normalize_key(release.group_name),
            release.source_url,
            release.raw_payload or {},
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

    def release_summary(self, periods, timezone):
        row = self._fetch_one(
            """
            SELECT
                count(*) FILTER (WHERE release_date BETWEEN %(today_start)s AND %(today_end)s) AS today_releases,
                count(DISTINCT manga_id) FILTER (WHERE release_date BETWEEN %(today_start)s AND %(today_end)s) AS today_works,
                count(*) FILTER (WHERE viewed_at IS NULL AND release_date BETWEEN %(today_start)s AND %(today_end)s) AS today_unseen,
                count(*) FILTER (WHERE release_date BETWEEN %(week_start)s AND %(week_end)s) AS week_releases,
                count(DISTINCT manga_id) FILTER (WHERE release_date BETWEEN %(week_start)s AND %(week_end)s) AS week_works,
                count(*) FILTER (WHERE viewed_at IS NULL AND release_date BETWEEN %(week_start)s AND %(week_end)s) AS week_unseen,
                count(*) FILTER (WHERE release_date BETWEEN %(month_start)s AND %(month_end)s) AS month_releases,
                count(DISTINCT manga_id) FILTER (WHERE release_date BETWEEN %(month_start)s AND %(month_end)s) AS month_works,
                count(*) FILTER (WHERE viewed_at IS NULL AND release_date BETWEEN %(month_start)s AND %(month_end)s) AS month_unseen
            FROM mangaupdates_releases
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
            f"SELECT count(*) AS total FROM mangaupdates_releases r JOIN mangas m ON m.id = r.manga_id WHERE {where}",
            tuple(params),
        )["total"]
        rows = self._fetch_all(
            f"""
            SELECT r.*, m.title
            FROM mangaupdates_releases r
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
            UPDATE mangaupdates_releases
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

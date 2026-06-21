import json
from datetime import datetime

from manhwateca.database.connection import connect
from manhwateca.database.models import MangaRecord, manga_from_row
from manhwateca.notion_sync import statuses
from manhwateca.notion_sync.matching import normalize_title


class MangaRepository:
    def __init__(self, connection=None, *, connection_factory=None):
        self.connection = connection
        self.connection_factory = connection_factory or connect

    def list_mangas(self) -> list[MangaRecord]:
        rows = self._fetch_all(
            """
            SELECT *
            FROM vw_mangas
            ORDER BY title
            """
        )
        return [manga_from_row(row) for row in rows]

    def list_next_reads(self) -> list[MangaRecord]:
        rows = self._fetch_all(
            """
            SELECT *
            FROM vw_next_reads
            """
        )
        return [manga_from_row(row) for row in rows]

    def find_by_work_code(self, work_code) -> MangaRecord | None:
        if work_code is None or str(work_code).strip() == "":
            return None
        row = self._fetch_one(
            """
            SELECT *
            FROM vw_mangas
            WHERE work_code = %s
            LIMIT 1
            """,
            (str(work_code).strip(),),
        )
        return manga_from_row(row) if row else None

    def find_by_notion_page_id(self, page_id: str) -> MangaRecord | None:
        if not page_id:
            return None
        row = self._fetch_one(
            """
            SELECT *
            FROM vw_mangas
            WHERE notion_page_id = %s
            LIMIT 1
            """,
            (page_id,),
        )
        return manga_from_row(row) if row else None

    def find_by_normalized_title(self, title: str) -> MangaRecord | None:
        normalized = normalize_title(title)
        if not normalized:
            return None

        for manga in self.list_mangas():
            names = [manga.title, manga.alternative_title or ""]
            if normalized in {
                normalize_title(name)
                for value in names
                for name in str(value).split("|")
                if name.strip()
            }:
                return manga
        return None

    def save_catalog_mangas(self, mangas) -> int:
        saved = 0
        for manga in mangas:
            self.save_catalog_manga(manga)
            saved += 1
        return saved

    def save_catalog_manga(self, manga: dict) -> int:
        existing = self._find_catalog_match(manga)
        if existing:
            self._update_catalog_manga(existing.id, manga)
            return existing.id
        return self._insert_catalog_manga(manga)

    def get_or_create_theme(self, name: str) -> int:
        name = str(name or "").strip()
        if not name:
            raise ValueError("Nome da temática é obrigatório.")

        existing = self._fetch_one(
            """
            SELECT id
            FROM themes
            WHERE lower(name) = lower(%s)
            LIMIT 1
            """,
            (name,),
        )
        if existing:
            return existing["id"]

        row = self._fetch_one(
            """
            INSERT INTO themes (name)
            VALUES (%s)
            RETURNING id
            """,
            (name,),
        )
        return row["id"]

    def add_theme_to_manga(self, manga_id: int, theme_name: str) -> int:
        theme_id = self.get_or_create_theme(theme_name)
        self._execute(
            """
            INSERT INTO manga_themes (manga_id, theme_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (manga_id, theme_id),
        )
        return theme_id

    def replace_manga_themes(self, manga_id: int, theme_names) -> list[int]:
        self._execute(
            """
            DELETE FROM manga_themes
            WHERE manga_id = %s
            """,
            (manga_id,),
        )
        theme_ids = []
        for name in theme_names:
            if str(name or "").strip():
                theme_ids.append(self.add_theme_to_manga(manga_id, name))
        return theme_ids

    def update_editorial_fields(self, name: str, changes: dict) -> bool:
        manga = self.find_by_normalized_title(name)
        if manga is None:
            return False

        values = _editorial_values(changes)
        if values:
            assignments = ", ".join(f"{column} = %s" for column in values)
            self._execute(
                f"""
                UPDATE mangas
                SET {assignments}
                WHERE id = %s
                """,
                (*values.values(), manga.id),
            )

        themes = _theme_values(changes)
        if themes is not None:
            self.replace_manga_themes(manga.id, themes)

        return True

    def update_mangaupdates_fields(
        self,
        name: str,
        series_id,
        summary: dict,
    ) -> bool:
        manga = self.find_by_work_code(series_id)
        if manga is None:
            manga = self.find_by_normalized_title(name)
        if manga is None:
            return False

        self._execute(
            """
            UPDATE mangas
            SET
                work_code = COALESCE(work_code, %s),
                latest_mangaupdates_chapter = %s,
                mangaupdates_url = COALESCE(%s, mangaupdates_url),
                format = COALESCE(NULLIF(format, ''), %s)
            WHERE id = %s
            """,
            (
                _string_or_none(summary.get("series_id") or series_id),
                _empty_to_none(summary.get("latest_chapter")),
                _empty_to_none(summary.get("url")),
                _empty_to_none(summary.get("format")),
                manga.id,
            ),
        )

        themes = _mangaupdates_themes(summary)
        if themes:
            self.replace_manga_themes(manga.id, themes)

        return True

    def update_notion_sync_fields(
        self,
        name: str,
        *,
        page_id=None,
        status=statuses.SYNCED,
        synced_at=None,
    ) -> bool:
        statuses.validate_status(status)
        manga = self._find_notion_match(name, page_id)
        if manga is None:
            return False

        self._execute(
            """
            UPDATE mangas
            SET
                notion_page_id = COALESCE(%s, notion_page_id),
                notion_last_synced_at = %s,
                notion_sync_status = %s
            WHERE id = %s
            """,
            (
                _string_or_none(page_id),
                synced_at or datetime.now().astimezone(),
                status,
                manga.id,
            ),
        )
        return True

    def record_sync_event(
        self,
        name: str,
        *,
        event_type: str,
        status: str,
        page_id=None,
        message=None,
        payload=None,
    ) -> bool:
        statuses.validate_status(status)
        manga = self._find_notion_match(name, page_id)
        manga_id = manga.id if manga else None
        self._execute(
            """
            INSERT INTO sync_events (
                manga_id,
                notion_page_id,
                event_type,
                sync_status,
                message,
                payload
            )
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                manga_id,
                _string_or_none(page_id),
                event_type,
                status,
                message,
                json.dumps(payload or {}, ensure_ascii=False),
            ),
        )
        return True

    def _fetch_all(self, query, params=None):
        with self._cursor() as cursor:
            cursor.execute(query, params or ())
            return list(cursor.fetchall())

    def _fetch_one(self, query, params=None):
        with self._cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def _execute(self, query, params=None):
        with self._cursor() as cursor:
            cursor.execute(query, params or ())

    def _cursor(self):
        return self._connection().cursor()

    def _connection(self):
        if self.connection is None:
            self.connection = self.connection_factory()
        return self.connection

    def _find_catalog_match(self, manga: dict) -> MangaRecord | None:
        work_code = _work_code(manga)
        if work_code:
            match = self.find_by_work_code(work_code)
            if match:
                return match
        return self.find_by_normalized_title(manga.get("nome", ""))

    def _find_notion_match(self, name: str, page_id=None) -> MangaRecord | None:
        if page_id:
            match = self.find_by_notion_page_id(str(page_id))
            if match:
                return match
        return self.find_by_normalized_title(name)

    def _insert_catalog_manga(self, manga: dict) -> int:
        row = self._fetch_one(
            """
            INSERT INTO mangas (
                work_code,
                title,
                alternative_title,
                reading_status_v2,
                personal_rank,
                last_read_chapter,
                latest_available_chapter,
                size_label,
                count_status,
                latest_mangaupdates_chapter,
                mangaupdates_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                _work_code(manga),
                manga.get("nome"),
                _aliases(manga),
                "Quero Ler",
                "Normal",
                manga.get("ultimo_lido"),
                manga.get("main_caps"),
                manga.get("tamanho"),
                manga.get("count_status"),
                manga.get("mangaupdates_latest_chapter"),
                manga.get("mangaupdates_url"),
            ),
        )
        return row["id"]

    def _update_catalog_manga(self, manga_id: int, manga: dict) -> None:
        self._execute(
            """
            UPDATE mangas
            SET
                work_code = COALESCE(work_code, %s),
                title = %s,
                alternative_title = COALESCE(NULLIF(alternative_title, ''), %s),
                last_read_chapter = COALESCE(last_read_chapter, %s),
                latest_available_chapter = %s,
                size_label = %s,
                count_status = %s,
                latest_mangaupdates_chapter = %s,
                mangaupdates_url = COALESCE(%s, mangaupdates_url)
            WHERE id = %s
            """,
            (
                _work_code(manga),
                manga.get("nome"),
                _aliases(manga),
                manga.get("ultimo_lido"),
                manga.get("main_caps"),
                manga.get("tamanho"),
                manga.get("count_status"),
                manga.get("mangaupdates_latest_chapter"),
                manga.get("mangaupdates_url"),
                manga_id,
            ),
        )


def _work_code(manga: dict):
    value = manga.get("work_code") or manga.get("mangaupdates_id")
    if value is None or str(value).strip() == "":
        return None
    return str(value).strip()


def _aliases(manga: dict):
    aliases = manga.get("alias") or []
    if isinstance(aliases, str):
        return aliases.strip() or None
    cleaned = [str(alias).strip() for alias in aliases if str(alias).strip()]
    return " | ".join(cleaned) if cleaned else None


def _editorial_values(changes: dict):
    mapping = {
        "Status": ("reading_status_v2", _status_value),
        "Interesse": ("personal_rank", _rank_value),
        "Nota": ("score", _score_value),
        "Picância": ("spice_level", _plain_value),
        "Último lido": ("last_read_chapter", _plain_value),
        "Formato": ("format", _plain_value),
        "Alias": ("alternative_title", _plain_value),
    }
    values = {}
    for source, (target, transform) in mapping.items():
        if source in changes:
            values[target] = transform(changes[source])
    return values


def _theme_values(changes: dict):
    values = []
    for field in ("Temática", "Universo"):
        if field not in changes:
            continue
        values.extend(
            item.strip()
            for item in str(changes[field]).split("|")
            if item.strip()
        )
    return values or None


def _status_value(value):
    mapping = {
        "Quero ler": "Quero Ler",
        "Em espera": "Aguardando Atualização",
    }
    value = str(value or "").strip()
    return mapping.get(value, value)


def _rank_value(value):
    mapping = {
        "Topzera": "Topzera",
        "Legalzin": "Legalzin",
        "Despriorizado": "Despriorizado",
    }
    return mapping.get(str(value or "").strip(), "Normal")


def _score_value(value):
    mapping = {
        "Topzera": 10,
        "Legalzin": 8,
        "Ok": 6,
        "Meia boca": 4,
        "Ruim": 2,
    }
    value = str(value or "").strip()
    return mapping.get(value)


def _plain_value(value):
    value = str(value or "").strip()
    return value or None


def _string_or_none(value):
    if value is None or str(value).strip() == "":
        return None
    return str(value).strip()


def _empty_to_none(value):
    if value is None or str(value).strip() == "":
        return None
    return value


def _mangaupdates_themes(summary: dict):
    values = []
    for field in ("genres", "universe"):
        for value in summary.get(field, []) or []:
            if str(value or "").strip():
                values.append(str(value).strip())
    return values

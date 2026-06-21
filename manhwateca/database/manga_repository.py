from manhwateca.database.connection import connect
from manhwateca.database.models import MangaRecord, manga_from_row
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

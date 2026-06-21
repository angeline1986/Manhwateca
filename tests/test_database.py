import unittest

from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    connect,
    get_database_url,
)
from manhwateca.database.manga_repository import MangaRepository


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rows = []
        self.row = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, query, params=()):
        normalized = " ".join(query.split()).casefold()
        self.connection.queries.append((normalized, params))

        if normalized.startswith("set search_path"):
            return

        if "from vw_mangas" in normalized and "where work_code" in normalized:
            self.row = next(
                (
                    row
                    for row in self.connection.mangas
                    if row.get("work_code") == params[0]
                ),
                None,
            )
            return

        if "from vw_mangas" in normalized and "where notion_page_id" in normalized:
            self.row = next(
                (
                    row
                    for row in self.connection.mangas
                    if row.get("notion_page_id") == params[0]
                ),
                None,
            )
            return

        if "from vw_mangas" in normalized:
            self.rows = sorted(
                self.connection.mangas,
                key=lambda row: row.get("title", ""),
            )
            return

        if "from vw_next_reads" in normalized:
            self.rows = list(self.connection.next_reads)
            return

        if "from themes" in normalized:
            self.row = self.connection.themes.get(params[0].casefold())
            return

        if normalized.startswith("insert into themes"):
            theme_id = len(self.connection.themes) + 1
            self.connection.themes[params[0].casefold()] = {"id": theme_id}
            self.row = {"id": theme_id}
            return

        if normalized.startswith("insert into manga_themes"):
            self.connection.links.append(params)
            return

        if normalized.startswith("delete from manga_themes"):
            self.connection.deleted.append(params[0])
            return

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self):
        self.queries = []
        self.mangas = []
        self.next_reads = []
        self.themes = {}
        self.links = []
        self.deleted = []

    def cursor(self):
        return FakeCursor(self)


class DatabaseConnectionTests(unittest.TestCase):
    def test_database_url_is_required(self):
        with self.assertRaisesRegex(
            DatabaseConfigurationError,
            "DATABASE_URL",
        ):
            get_database_url({})

    def test_connect_wraps_connection_errors(self):
        def failing_connect(_url):
            raise OSError("database offline")

        with self.assertRaisesRegex(
            DatabaseConnectionError,
            "database offline",
        ):
            connect("postgresql://local/test", connect_fn=failing_connect)

    def test_connect_sets_search_path(self):
        connection = FakeConnection()

        result = connect(
            "postgresql://local/test",
            connect_fn=lambda _url: connection,
        )

        self.assertIs(result, connection)
        self.assertIn("set search_path", connection.queries[0][0])


class MangaRepositoryTests(unittest.TestCase):
    def test_reads_mangas_and_exposes_reading_status_alias(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 1,
            "work_code": "823",
            "title": "2020",
            "reading_status_v2": "Quero Ler",
            "personal_rank": "Topzera",
            "themes": ["Drama", "Romance"],
        }]

        mangas = MangaRepository(connection).list_mangas()

        self.assertEqual(1, len(mangas))
        self.assertEqual("2020", mangas[0].title)
        self.assertEqual("Quero Ler", mangas[0].reading_status)
        self.assertEqual(["Drama", "Romance"], mangas[0].themes)

    def test_reads_next_reads_view(self):
        connection = FakeConnection()
        connection.next_reads = [{"id": 2, "title": "Alpha Agenda"}]

        mangas = MangaRepository(connection).list_next_reads()

        self.assertEqual(["Alpha Agenda"], [manga.title for manga in mangas])

    def test_finds_by_work_code_and_notion_page_id(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 1,
            "work_code": "123",
            "title": "Alpha",
            "notion_page_id": "page-1",
        }]
        repository = MangaRepository(connection)

        self.assertEqual("Alpha", repository.find_by_work_code("123").title)
        self.assertEqual(
            "Alpha",
            repository.find_by_notion_page_id("page-1").title,
        )

    def test_finds_by_normalized_title_or_alias(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 1,
            "title": "The Secretive XX",
            "alternative_title": "XX Cheio de Segredos | Outro Nome",
        }]

        manga = MangaRepository(connection).find_by_normalized_title(
            "xx cheio de segredos",
        )

        self.assertEqual("The Secretive XX", manga.title)

    def test_theme_methods_are_centralized(self):
        connection = FakeConnection()
        repository = MangaRepository(connection)

        theme_id = repository.add_theme_to_manga(10, "Omegaverse")
        replaced = repository.replace_manga_themes(
            10,
            ["Omegaverse", "Drama"],
        )

        self.assertEqual(1, theme_id)
        self.assertEqual([1, 2], replaced)
        self.assertEqual([10], connection.deleted)
        self.assertIn((10, 1), connection.links)
        self.assertIn((10, 2), connection.links)


if __name__ == "__main__":
    unittest.main()

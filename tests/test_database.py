import unittest

from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    connect,
    get_database_url,
)
from manhwateca.database.manga_repository import (
    ConfirmedIdCorrectionResult,
    MangaRepository,
    select_alternative_title,
)


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

        if (
            ("from vw_mangas" in normalized or "from mangas" in normalized)
            and "where id = %s" in normalized
        ):
            self.row = next(
                (
                    row
                    for row in self.connection.mangas
                    if row.get("id") == params[0]
                ),
                None,
            )
            return

        if "from vw_mangas" in normalized and "where id = any" in normalized:
            ids = set(params[0])
            self.rows = sorted(
                [
                    row for row in self.connection.mangas
                    if row.get("id") in ids
                ],
                key=lambda row: row.get("title", ""),
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

        if normalized.startswith("insert into sync_events"):
            if self.connection.fail_sync_event:
                raise RuntimeError("sync event failed")
            self.connection.sync_events.append(params)
            return

        if "from information_schema.columns" in normalized:
            self.rows = [
                {"column_name": name, "data_type": data_type}
                for name, data_type in self.connection.decision_queue_schema
            ]
            return

        if (
            "from decision_queue" in normalized
            and normalized.startswith("select id from decision_queue")
        ):
            self.row = next(
                (
                    {"id": item["id"]}
                    for item in reversed(self.connection.decision_queue)
                    if item.get("decision_type") == params[0]
                    and item.get("title") == params[1]
                    and (
                        len(params) < 3
                        or "source" not in item
                        or item.get("source") == params[2]
                    )
                ),
                None,
            )
            return

        if "from decision_queue" in normalized:
            rows = list(self.connection.decision_queue)
            if params:
                rows = [
                    item for item in rows
                    if item.get("decision_type") == params[0]
                ]
            if len(params) > 1:
                rows = [
                    item for item in rows
                    if item.get("status") == params[1]
                ]
            self.rows = rows
            return

        if normalized.startswith("insert into decision_queue"):
            self.connection.decision_inserts.append((normalized, params))
            self.connection.decision_queue.append({
                "id": len(self.connection.decision_queue) + 1,
                "decision_type": params[0],
                "title": params[1],
                "payload": params[2],
                "source": params[3] if len(params) > 3 else None,
            })
            return

        if normalized.startswith("update decision_queue"):
            self.connection.decision_updates.append((normalized, params))
            return

        if normalized.startswith("insert into mangas"):
            manga_id = len(self.connection.mangas) + 1
            self.connection.inserted.append(params)
            self.row = {"id": manga_id}
            self.connection.mangas.append({
                "id": manga_id,
                "work_code": params[0],
                "title": params[1],
                "alternative_title": params[2],
                "reading_status_v2": params[3],
                "personal_rank": params[4],
            })
            return

        if normalized.startswith("update mangas"):
            if self.connection.fail_update_mangas:
                raise RuntimeError("update failed")
            self.connection.updated.append((normalized, params))
            return

        if normalized.startswith("delete from manga_themes"):
            if self.connection.fail_delete_themes:
                raise RuntimeError("delete themes failed")
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
        self.inserted = []
        self.updated = []
        self.sync_events = []
        self.commits = []
        self.rollbacks = []
        self.fail_update_mangas = False
        self.fail_delete_themes = False
        self.fail_sync_event = False
        self.decision_queue_schema = [
            ("id", "bigint"),
            ("decision_type", "character varying"),
            ("title", "character varying"),
            ("payload", "jsonb"),
            ("source", "character varying"),
            ("status", "character varying"),
            ("source_key", "character varying"),
            ("resolution", "jsonb"),
            ("resolved_at", "timestamp without time zone"),
        ]
        self.decision_queue = []
        self.decision_inserts = []
        self.decision_updates = []

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits.append(True)

    def rollback(self):
        self.rollbacks.append(True)


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
        self.assertIn('"manhwateca"', connection.queries[0][0])

    def test_connect_respects_configured_schema(self):
        connection = FakeConnection()

        connect(
            "postgresql://local/test",
            connect_fn=lambda _url: connection,
            schema="sandbox_schema",
        )

        self.assertIn('"sandbox_schema"', connection.queries[0][0])

    def test_connect_rejects_invalid_schema_name(self):
        connection = FakeConnection()

        with self.assertRaisesRegex(DatabaseConfigurationError, "Schema"):
            connect(
                "postgresql://local/test",
                connect_fn=lambda _url: connection,
                schema="unsafe;drop",
            )


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

    def test_lists_mangas_by_ids_with_parameterized_filter(self):
        connection = FakeConnection()
        connection.mangas = [
            {"id": 1, "title": "Alpha"},
            {"id": 2, "title": "Beta"},
            {"id": 3, "title": "Gamma"},
        ]

        mangas = MangaRepository(connection).list_mangas_by_ids([3, "1", 3, None])

        self.assertEqual(["Alpha", "Gamma"], [manga.title for manga in mangas])
        query, params = connection.queries[-1]
        self.assertIn("where id = any", query)
        self.assertEqual(([3, 1],), params)

    def test_list_mangas_by_ids_empty_does_not_query_database(self):
        connection = FakeConnection()

        mangas = MangaRepository(connection).list_mangas_by_ids([])

        self.assertEqual([], mangas)
        self.assertEqual([], connection.queries)

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

    def test_inserts_catalog_manga_with_technical_fields_only(self):
        connection = FakeConnection()
        repository = MangaRepository(connection)

        manga_id = repository.save_catalog_manga({
            "nome": "Alpha",
            "alias": ["Alfa"],
            "mangaupdates_id": 123,
            "ultimo_lido": 4,
            "main_caps": 12,
            "tamanho": "Curto",
            "count_status": "OK",
            "mangaupdates_latest_chapter": 13,
            "mangaupdates_url": "https://example.test/alpha",
            "cover_url": "https://cdn.example.test/alpha.jpg",
        })

        self.assertEqual(1, manga_id)
        self.assertEqual("123", connection.inserted[0][0])
        self.assertEqual("Alpha", connection.inserted[0][1])
        self.assertEqual("Alfa", connection.inserted[0][2])
        self.assertEqual("Quero Ler", connection.inserted[0][3])
        self.assertEqual("Normal", connection.inserted[0][4])
        self.assertEqual(
            "https://cdn.example.test/alpha.jpg",
            connection.inserted[0][11],
        )

    def test_updates_catalog_manga_without_touching_manual_fields(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 7,
            "work_code": "123",
            "title": "Alpha",
            "reading_status_v2": "Lendo",
            "personal_rank": "Topzera",
            "score": 10,
            "spice_level": "Alta",
        }]
        repository = MangaRepository(connection)

        manga_id = repository.save_catalog_manga({
            "nome": "Alpha",
            "mangaupdates_id": 123,
            "ultimo_lido": 4,
            "main_caps": 12,
            "tamanho": "Curto",
            "count_status": "OK",
            "cover_url": "https://cdn.example.test/alpha-new.jpg",
        })

        self.assertEqual(7, manga_id)
        query, params = connection.updated[0]
        self.assertNotIn("reading_status_v2", query)
        self.assertNotIn("personal_rank", query)
        self.assertNotIn("score", query)
        self.assertNotIn("spice_level", query)
        self.assertIn("cover_url", query)
        self.assertEqual("https://cdn.example.test/alpha-new.jpg", params[-2])
        self.assertEqual(7, params[-1])

    def test_updates_editorial_fields_and_themes(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 7,
            "title": "Official Alpha",
            "alternative_title": "Alfa",
        }]
        repository = MangaRepository(connection)

        updated = repository.update_editorial_fields("Alfa", {
            "Status": "Em espera",
            "Interesse": "Topzera",
            "Nota": "Legalzin",
            "Picância": "🔥 Alta",
            "Último lido": "12",
            "Alias": "Alfa Novo",
            "Temática": "Drama | Romance",
            "Universo": "Omegaverse",
        })

        self.assertTrue(updated)
        query, params = connection.updated[0]
        self.assertIn("reading_status_v2", query)
        self.assertIn("personal_rank", query)
        self.assertIn("score", query)
        self.assertIn("spice_level", query)
        self.assertEqual("Aguardando Atualização", params[0])
        self.assertEqual("Topzera", params[1])
        self.assertEqual(8, params[2])
        self.assertEqual("🔥 Alta", params[3])
        self.assertEqual("12", params[4])
        self.assertEqual("Alfa Novo", params[5])
        self.assertIn((7, 1), connection.links)
        self.assertIn((7, 2), connection.links)
        self.assertIn((7, 3), connection.links)

    def test_update_editorial_fields_returns_false_when_missing(self):
        connection = FakeConnection()

        updated = MangaRepository(connection).update_editorial_fields(
            "Ausente",
            {"Status": "Lendo"},
        )

        self.assertFalse(updated)

    def test_updates_mangaupdates_fields_and_themes(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 7,
            "title": "Beyond Memories",
        }]
        repository = MangaRepository(connection)

        updated = repository.update_mangaupdates_fields(
            "Beyond Memories",
            46829042951,
            {
                "series_id": 46829042951,
                "latest_chapter": 104,
                "url": "https://example.test/beyond",
                "cover_url": "https://cdn.example.test/beyond.jpg",
                "format": "Manhwa",
                "associated_titles": ["Beyond the Memories"],
                "genres": ["Drama", "Yaoi"],
                "universe": ["Omegaverse"],
            },
        )

        self.assertTrue(updated)
        query, params = connection.updated[0]
        self.assertIn("latest_mangaupdates_chapter", query)
        self.assertIn("mangaupdates_url", query)
        self.assertIn("format", query)
        self.assertNotIn("reading_status_v2", query)
        self.assertEqual("46829042951", params[0])
        self.assertEqual(104, params[1])
        self.assertEqual("https://example.test/beyond", params[2])
        self.assertEqual("https://cdn.example.test/beyond.jpg", params[3])
        self.assertEqual("Manhwa", params[4])
        self.assertEqual("Beyond the Memories", params[5])
        self.assertEqual(7, params[6])
        self.assertIn((7, 1), connection.links)
        self.assertIn((7, 2), connection.links)
        self.assertIn((7, 3), connection.links)

    def test_update_mangaupdates_fields_preserves_existing_alias(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 7,
            "title": "Beyond Memories",
            "alternative_title": "Alias Real",
        }]
        repository = MangaRepository(connection)

        updated = repository.update_mangaupdates_fields(
            "Beyond Memories",
            46829042951,
            {
                "series_id": 46829042951,
                "associated_titles": ["Novo Alias"],
            },
        )

        self.assertTrue(updated)
        query, params = connection.updated[0]
        self.assertIn("alternative_title = case", query)
        self.assertEqual("Novo Alias", params[5])
        self.assertEqual(7, params[6])

    def test_select_alternative_title_uses_first_valid_associated_title(self):
        self.assertEqual(
            "Outro Nome",
            select_alternative_title(
                ["", "  ", "Beyond Memories", "ID 46829042951", "Outro Nome"],
                "Beyond Memories",
                46829042951,
            ),
        )

    def test_select_alternative_title_returns_none_without_valid_alias(self):
        self.assertIsNone(select_alternative_title(None, "Alpha", 123))
        self.assertIsNone(select_alternative_title([], "Alpha", 123))
        self.assertIsNone(select_alternative_title("Alias", "Alpha", 123))
        self.assertIsNone(select_alternative_title(["Alpha"], "Alpha", 123))
        self.assertIsNone(select_alternative_title(["ID 123"], "Alpha", 123))
        self.assertIsNone(select_alternative_title([" ", ""], "Alpha", 123))

    def test_select_alternative_title_skips_duplicate_before_valid_alias(self):
        self.assertEqual(
            "Beta",
            select_alternative_title(
                ["Alpha", " alpha ", "Beta", "Beta"],
                "Alpha",
                123,
            ),
        )

    def test_select_alternative_title_accepts_non_ascii_alias(self):
        self.assertEqual(
            "드레스드 투 킬",
            select_alternative_title(
                [
                    "Dressed to kill ～華麗なる逃亡劇～",
                    "드레스드 투 킬",
                    "드레스드 투 킬(Dressed to Kill)",
                ],
                "Dressed_to_Kill",
                "38551408461",
            ),
        )

    def test_confirms_mangaupdates_id_without_touching_manual_fields(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 7,
            "title": "Alpha",
            "reading_status_v2": "Lendo",
            "personal_rank": "Topzera",
        }]
        repository = MangaRepository(connection)

        confirmed = repository.confirm_mangaupdates_id(
            "Alpha",
            123,
            found_title="Official Alpha",
        )

        self.assertTrue(confirmed)
        query, params = connection.updated[0]
        self.assertIn("work_code", query)
        self.assertIn("alternative_title", query)
        self.assertNotIn("reading_status_v2", query)
        self.assertNotIn("personal_rank", query)
        self.assertEqual("123", params[0])
        self.assertEqual("Official Alpha", params[1])
        self.assertEqual(7, params[2])
        self.assertEqual(1, len(connection.commits))

    def test_manual_confirmation_does_not_store_generated_id_as_alias(self):
        connection = FakeConnection()
        connection.mangas = [{"id": 7, "title": "Alpha"}]
        repository = MangaRepository(connection)

        confirmed = repository.confirm_mangaupdates_id(
            "Alpha",
            123,
            found_title="ID 123",
        )

        self.assertTrue(confirmed)
        query, params = connection.updated[0]
        self.assertIn("alternative_title", query)
        self.assertEqual("123", params[0])
        self.assertIsNone(params[1])
        self.assertEqual(7, params[2])

    def test_manual_confirmation_preserves_existing_real_alias(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 7,
            "title": "Alpha",
            "alternative_title": "Alfa Real",
        }]
        repository = MangaRepository(connection)

        confirmed = repository.confirm_mangaupdates_id(
            "Alpha",
            123,
            found_title="ID 123",
        )

        self.assertTrue(confirmed)
        query, params = connection.updated[0]
        self.assertIn("coalesce", query)
        self.assertEqual("123", params[0])
        self.assertIsNone(params[1])
        self.assertEqual(7, params[2])

    def test_confirms_mangaupdates_id_by_work_id_blocks_external_id_collision(self):
        connection = FakeConnection()
        connection.mangas = [
            {"id": 7, "title": "Target"},
            {"id": 9, "title": "Existing", "work_code": "123"},
        ]
        repository = MangaRepository(connection)

        confirmed = repository.confirm_mangaupdates_id_by_work_id(
            7,
            123,
            found_title="Official Target",
        )

        self.assertFalse(confirmed)
        self.assertEqual("external_id_already_assigned", confirmed.status)
        self.assertEqual(7, confirmed.work_id)
        self.assertEqual(9, confirmed.existing_work_id)
        self.assertEqual("Existing", confirmed.existing_title)
        self.assertEqual([], connection.updated)
        self.assertEqual([], connection.commits)

    def test_confirms_mangaupdates_id_by_work_id_is_idempotent_for_same_work(self):
        connection = FakeConnection()
        connection.mangas = [
            {"id": 7, "title": "Target", "work_code": "123"},
        ]
        repository = MangaRepository(connection)

        confirmed = repository.confirm_mangaupdates_id_by_work_id(
            7,
            123,
            found_title="Official Target",
        )

        self.assertTrue(confirmed)
        self.assertEqual("already_applied", confirmed.status)
        self.assertEqual(7, confirmed.work_id)
        self.assertEqual([], connection.updated)
        self.assertEqual([], connection.commits)

    def test_correct_confirmed_id_invalidates_derived_metadata(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 254,
            "title": "Mad for love",
            "work_code": "57487635157",
            "mangaupdates_url": "https://example.test/wrong",
            "cover_url": "https://example.test/wrong.jpg",
            "format": "Manhwa",
            "latest_mangaupdates_chapter": 0,
            "alternative_title": "Record of Mad Love",
            "notion_page_id": "page-254",
            "notion_sync_status": "synced",
        }]
        repository = MangaRepository(connection)

        result = repository.correct_confirmed_mangaupdates_id(
            254,
            "56302347523",
            expected_current_work_code="57487635157",
        )

        self.assertTrue(result)
        self.assertIsInstance(result, ConfirmedIdCorrectionResult)
        self.assertEqual("applied", result.status)
        self.assertEqual("57487635157", result.old_series_id)
        self.assertEqual("56302347523", result.new_series_id)
        self.assertEqual("pending", result.notion_sync_status)
        query, params = connection.updated[0]
        self.assertIn("work_code = %s", query)
        self.assertIn("mangaupdates_url = null", query)
        self.assertIn("cover_url = null", query)
        self.assertIn("format = null", query)
        self.assertIn("latest_mangaupdates_chapter = null", query)
        self.assertIn("alternative_title = null", query)
        self.assertIn("notion_sync_status = %s", query)
        self.assertEqual(("56302347523", "pending", 254), params)
        self.assertEqual([254], connection.deleted)
        event = connection.sync_events[0]
        self.assertEqual(254, event[0])
        self.assertEqual("page-254", event[1])
        self.assertEqual("mangaupdates_confirmed_id_corrected", event[2])
        self.assertEqual("pending", event[3])
        self.assertIn("ID MangaUpdates confirmado corrigido", event[4])
        self.assertIn("57487635157", event[5])
        self.assertIn("56302347523", event[5])
        self.assertEqual(1, len(connection.commits))

    def test_correct_confirmed_id_blocks_external_id_collision(self):
        connection = FakeConnection()
        connection.mangas = [
            {"id": 254, "title": "Mad for love", "work_code": "57487635157"},
            {"id": 300, "title": "Tuojiang", "work_code": "56302347523"},
        ]
        repository = MangaRepository(connection)

        result = repository.correct_confirmed_mangaupdates_id(
            254,
            "56302347523",
            expected_current_work_code="57487635157",
        )

        self.assertFalse(result)
        self.assertEqual("external_id_already_assigned", result.status)
        self.assertEqual(300, result.existing_work_id)
        self.assertEqual("Tuojiang", result.existing_title)
        self.assertEqual([], connection.updated)
        self.assertEqual([], connection.sync_events)
        self.assertEqual([], connection.commits)
        self.assertEqual([True], connection.rollbacks)

    def test_correct_confirmed_id_blocks_stale_preview_without_writes(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 254,
            "title": "Mad for love",
            "work_code": "12345678900",
        }]
        repository = MangaRepository(connection)

        result = repository.correct_confirmed_mangaupdates_id(
            254,
            "56302347523",
            expected_current_work_code="57487635157",
        )

        self.assertFalse(result)
        self.assertEqual("stale_preview", result.status)
        self.assertEqual("57487635157", result.expected_current_work_code)
        self.assertEqual("12345678900", result.actual_current_work_code)
        self.assertEqual([], connection.updated)
        self.assertEqual([], connection.deleted)
        self.assertEqual([], connection.sync_events)
        self.assertEqual([], connection.commits)
        self.assertEqual([True], connection.rollbacks)

    def test_correct_confirmed_id_rolls_back_when_audit_insert_fails(self):
        connection = FakeConnection()
        connection.fail_sync_event = True
        connection.mangas = [{
            "id": 254,
            "title": "Mad for love",
            "work_code": "57487635157",
            "notion_page_id": "page-254",
        }]
        repository = MangaRepository(connection)

        result = repository.correct_confirmed_mangaupdates_id(
            254,
            "56302347523",
            expected_current_work_code="57487635157",
        )

        self.assertFalse(result)
        self.assertEqual("persistence_error", result.status)
        self.assertEqual([], connection.commits)
        self.assertEqual([True], connection.rollbacks)

    def test_correct_confirmed_id_rolls_back_when_metadata_update_fails(self):
        connection = FakeConnection()
        connection.fail_update_mangas = True
        connection.mangas = [{
            "id": 254,
            "title": "Mad for love",
            "work_code": "57487635157",
            "mangaupdates_url": "https://example.test/wrong",
            "notion_sync_status": "synced",
        }]
        repository = MangaRepository(connection)

        result = repository.correct_confirmed_mangaupdates_id(
            254,
            "56302347523",
            expected_current_work_code="57487635157",
        )

        self.assertFalse(result)
        self.assertEqual("persistence_error", result.status)
        self.assertEqual([], connection.deleted)
        self.assertEqual([], connection.sync_events)
        self.assertEqual([], connection.commits)
        self.assertEqual([True], connection.rollbacks)

    def test_correct_confirmed_id_rolls_back_when_theme_cleanup_fails(self):
        connection = FakeConnection()
        connection.fail_delete_themes = True
        connection.mangas = [{
            "id": 254,
            "title": "Mad for love",
            "work_code": "57487635157",
            "mangaupdates_url": "https://example.test/wrong",
            "notion_sync_status": "synced",
        }]
        repository = MangaRepository(connection)

        result = repository.correct_confirmed_mangaupdates_id(
            254,
            "56302347523",
            expected_current_work_code="57487635157",
        )

        self.assertFalse(result)
        self.assertEqual("persistence_error", result.status)
        self.assertEqual(1, len(connection.updated))
        self.assertEqual([], connection.deleted)
        self.assertEqual([], connection.sync_events)
        self.assertEqual([], connection.commits)
        self.assertEqual([True], connection.rollbacks)

    def test_updates_notion_sync_fields_by_page_id(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 7,
            "title": "Alpha",
            "notion_page_id": "page-1",
        }]
        repository = MangaRepository(connection)

        updated = repository.update_notion_sync_fields(
            "Outro Nome",
            page_id="page-1",
            status="synced",
        )

        self.assertTrue(updated)
        query, params = connection.updated[0]
        self.assertIn("notion_page_id", query)
        self.assertIn("notion_last_synced_at", query)
        self.assertIn("notion_sync_status", query)
        self.assertEqual("page-1", params[0])
        self.assertEqual("synced", params[2])
        self.assertEqual(7, params[3])

    def test_records_sync_event_with_payload(self):
        connection = FakeConnection()
        connection.mangas = [{
            "id": 7,
            "title": "Alpha",
            "notion_page_id": "page-1",
        }]
        repository = MangaRepository(connection)

        recorded = repository.record_sync_event(
            "Alpha",
            event_type="update",
            status="synced",
            page_id="page-1",
            message="ok",
            payload={"nome": "Alpha"},
        )

        self.assertTrue(recorded)
        self.assertEqual(1, len(connection.sync_events))
        params = connection.sync_events[0]
        self.assertEqual(7, params[0])
        self.assertEqual("page-1", params[1])
        self.assertEqual("update", params[2])
        self.assertEqual("synced", params[3])
        self.assertEqual("ok", params[4])
        self.assertIn('"nome": "Alpha"', params[5])
        self.assertEqual(1, len(connection.commits))

    def test_updates_notion_sync_fields_by_id(self):
        connection = FakeConnection()
        repository = MangaRepository(connection)

        updated = repository.update_notion_sync_fields_by_id(
            7,
            page_id="page-1",
            status="synced",
            synced_at="2026-01-01T00:00:00",
        )

        self.assertTrue(updated)
        query, params = connection.updated[0]
        self.assertIn("where id = %s", query)
        self.assertEqual("page-1", params[0])
        self.assertEqual("2026-01-01T00:00:00", params[1])
        self.assertEqual("synced", params[2])
        self.assertEqual(7, params[3])

    def test_update_notion_sync_fields_by_id_preserves_timestamp_without_synced_at(self):
        connection = FakeConnection()
        repository = MangaRepository(connection)

        repository.update_notion_sync_fields_by_id(
            7,
            page_id="page-1",
            status="error",
            synced_at=None,
        )

        query, params = connection.updated[0]
        self.assertIn("coalesce(%s, notion_last_synced_at)", query)
        self.assertIsNone(params[1])
        self.assertEqual("error", params[2])

    def test_records_sync_event_by_id_with_payload(self):
        connection = FakeConnection()
        repository = MangaRepository(connection)

        recorded = repository.record_sync_event_by_id(
            7,
            event_type="notion_metadata_sync",
            status="conflict",
            page_id="page-1",
            message="stale",
            payload={"code": "stale_notion_page"},
        )

        self.assertTrue(recorded)
        params = connection.sync_events[0]
        self.assertEqual(7, params[0])
        self.assertEqual("page-1", params[1])
        self.assertEqual("notion_metadata_sync", params[2])
        self.assertEqual("conflict", params[3])
        self.assertEqual("stale", params[4])
        self.assertIn('"code": "stale_notion_page"', params[5])
        self.assertEqual(1, len(connection.commits))

    def test_enqueues_mangaupdates_decision(self):
        connection = FakeConnection()
        repository = MangaRepository(connection)

        queued = repository.enqueue_decision(
            decision_type="mangaupdates_match",
            source="mangaupdates",
            title="Alpha",
            source_key="Alpha",
            payload={"candidatos": [{"id": 1}]},
        )

        self.assertTrue(queued)
        query, params = connection.decision_inserts[0]
        self.assertIn("insert into decision_queue", query)
        self.assertIn("%s::jsonb", query)
        self.assertEqual("mangaupdates_match", params[0])
        self.assertEqual("Alpha", params[1])
        self.assertIn('"candidatos"', params[2])

    def test_resolves_existing_decision(self):
        connection = FakeConnection()
        connection.decision_queue = [{
            "id": 1,
            "decision_type": "mangaupdates_match",
            "title": "Alpha",
            "source": "mangaupdates",
            "status": "pending",
        }]
        repository = MangaRepository(connection)

        resolved = repository.resolve_decision(
            decision_type="mangaupdates_match",
            source="mangaupdates",
            title="Alpha",
            resolution={"id": 123},
        )

        self.assertTrue(resolved)
        query, params = connection.decision_updates[0]
        self.assertIn("update decision_queue", query)
        self.assertIn("resolution = %s::jsonb", query)
        self.assertEqual("resolved", params[0])
        self.assertIn('"id": 123', params[1])

    def test_lists_pending_decisions(self):
        connection = FakeConnection()
        connection.decision_queue = [
            {
                "id": 1,
                "decision_type": "mangaupdates_match",
                "title": "Alpha",
                "source": "mangaupdates",
                "payload": {"candidatos": [{"id": 1}]},
                "status": "pending",
            },
            {
                "id": 2,
                "decision_type": "mangaupdates_match",
                "title": "Beta",
                "source": "mangaupdates",
                "payload": {},
                "status": "resolved",
            },
        ]
        repository = MangaRepository(connection)

        decisions = repository.list_decisions(
            decision_type="mangaupdates_match",
            status="pending",
        )

        self.assertEqual(1, len(decisions))
        self.assertEqual("Alpha", decisions[0]["title"])


if __name__ == "__main__":
    unittest.main()

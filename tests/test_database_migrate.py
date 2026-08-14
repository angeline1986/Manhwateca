import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from manhwateca.database import migrate


class DatabaseMigrateTests(unittest.TestCase):
    def test_migration_files_are_sorted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "002_second.sql").write_text("SELECT 2;", encoding="utf-8")
            (root / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")

            self.assertEqual(
                ["001_first.sql", "002_second.sql"],
                [path.name for path in migrate.migration_files(root)],
            )

    def test_apply_migrations_executes_each_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
            (root / "002_second.sql").write_text("SELECT 2;", encoding="utf-8")
            connection = FakeConnection()

            with patch.object(migrate, "transaction", fake_transaction(connection)):
                applied = migrate.apply_migrations(
                    database_url="postgresql://example",
                    migrations_dir=root,
                )

            self.assertEqual(["001_first.sql", "002_second.sql"], applied)
            self.assertEqual(["SELECT 1;", "SELECT 2;"], connection.executed)

    def test_manga_external_refs_migration_is_idempotent(self):
        sql = (
            migrate.MIGRATIONS_DIR / "013_manga_external_refs.sql"
        ).read_text(encoding="utf-8").casefold()

        self.assertIn("create table if not exists manhwateca.manga_external_refs", sql)
        self.assertIn("external_id text not null", sql)
        self.assertIn("unique (manga_id, provider)", sql)
        self.assertIn("unique (provider, external_id)", sql)
        self.assertIn("references manhwateca.mangas(id)", sql)
        self.assertIn("metadata jsonb not null default '{}'::jsonb", sql)
        self.assertIn("on conflict do nothing", sql)

    def test_manga_external_refs_migration_can_be_executed_twice_by_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            migration_sql = (
                migrate.MIGRATIONS_DIR / "013_manga_external_refs.sql"
            ).read_text(encoding="utf-8")
            (root / "013_manga_external_refs.sql").write_text(
                migration_sql,
                encoding="utf-8",
            )
            connection = FakeConnection()

            with patch.object(migrate, "transaction", fake_transaction(connection)):
                first = migrate.apply_migrations(
                    database_url="postgresql://example",
                    migrations_dir=root,
                )
                second = migrate.apply_migrations(
                    database_url="postgresql://example",
                    migrations_dir=root,
                )

            self.assertEqual(["013_manga_external_refs.sql"], first)
            self.assertEqual(["013_manga_external_refs.sql"], second)
            self.assertEqual(2, len(connection.executed))

    def test_external_releases_migration_is_idempotent(self):
        sql = (
            migrate.MIGRATIONS_DIR / "014_external_releases.sql"
        ).read_text(encoding="utf-8").casefold()

        self.assertIn("create table if not exists manhwateca.external_releases", sql)
        self.assertIn("external_series_id text not null", sql)
        self.assertIn("external_release_id text", sql)
        self.assertIn("chapter text", sql)
        self.assertIn("raw_payload jsonb not null default '{}'::jsonb", sql)
        self.assertIn("references manhwateca.mangas(id)", sql)
        self.assertIn("create unique index if not exists uq_external_releases_external_id", sql)
        self.assertIn("provider, external_release_id", sql)
        self.assertIn("create unique index if not exists uq_external_releases_fallback", sql)
        self.assertIn("provider,\n    external_series_id", sql)

    def test_external_releases_migration_can_be_executed_twice_by_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            migration_sql = (
                migrate.MIGRATIONS_DIR / "014_external_releases.sql"
            ).read_text(encoding="utf-8")
            (root / "014_external_releases.sql").write_text(
                migration_sql,
                encoding="utf-8",
            )
            connection = FakeConnection()

            with patch.object(migrate, "transaction", fake_transaction(connection)):
                first = migrate.apply_migrations(
                    database_url="postgresql://example",
                    migrations_dir=root,
                )
                second = migrate.apply_migrations(
                    database_url="postgresql://example",
                    migrations_dir=root,
                )

            self.assertEqual(["014_external_releases.sql"], first)
            self.assertEqual(["014_external_releases.sql"], second)
            self.assertEqual(2, len(connection.executed))

    def test_dashboard_cutover_migration_backfills_mangaupdates_idempotently(self):
        sql = (
            migrate.MIGRATIONS_DIR / "015_external_releases_dashboard_cutover.sql"
        ).read_text(encoding="utf-8").casefold()

        self.assertIn("add column if not exists release_group text", sql)
        self.assertIn("add column if not exists normalized_release_group", sql)
        self.assertIn("drop index if exists manhwateca.uq_external_releases_fallback", sql)
        self.assertIn("normalized_release_group", sql)
        self.assertIn("from manhwateca.mangaupdates_releases", sql)
        self.assertIn("'mangaupdates'", sql)
        self.assertIn("on conflict (provider, external_release_id)", sql)
        self.assertIn("on conflict (\n    provider,\n    external_series_id", sql)
        self.assertIn("coalesce(manhwateca.external_releases.viewed_at, excluded.viewed_at)", sql)

    def test_dashboard_cutover_migration_can_be_executed_twice_by_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            migration_sql = (
                migrate.MIGRATIONS_DIR / "015_external_releases_dashboard_cutover.sql"
            ).read_text(encoding="utf-8")
            (root / "015_external_releases_dashboard_cutover.sql").write_text(
                migration_sql,
                encoding="utf-8",
            )
            connection = FakeConnection()

            with patch.object(migrate, "transaction", fake_transaction(connection)):
                first = migrate.apply_migrations(
                    database_url="postgresql://example",
                    migrations_dir=root,
                )
                second = migrate.apply_migrations(
                    database_url="postgresql://example",
                    migrations_dir=root,
                )

            self.assertEqual(["015_external_releases_dashboard_cutover.sql"], first)
            self.assertEqual(["015_external_releases_dashboard_cutover.sql"], second)
            self.assertEqual(2, len(connection.executed))


class fake_transaction:
    def __init__(self, connection):
        self.connection = connection

    def __call__(self, *_args, **_kwargs):
        return self

    def __enter__(self):
        return self.connection

    def __exit__(self, *_args):
        return False


class FakeConnection:
    def __init__(self):
        self.executed = []

    def cursor(self):
        return FakeCursor(self)


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql):
        self.connection.executed.append(sql)


if __name__ == "__main__":
    unittest.main()

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

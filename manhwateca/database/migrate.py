from pathlib import Path

from dotenv import load_dotenv

from manhwateca.database.connection import transaction


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def migration_files(migrations_dir=MIGRATIONS_DIR):
    return sorted(Path(migrations_dir).glob("*.sql"))


def apply_migrations(database_url=None, migrations_dir=MIGRATIONS_DIR) -> list[str]:
    applied = []
    with transaction(database_url) as connection:
        with connection.cursor() as cursor:
            for path in migration_files(migrations_dir):
                cursor.execute(path.read_text(encoding="utf-8"))
                applied.append(path.name)
    return applied


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    applied = apply_migrations()
    if applied:
        print("Migrations aplicadas:")
        for name in applied:
            print(f"- {name}")
    else:
        print("Nenhuma migration encontrada.")


if __name__ == "__main__":
    main()

import os
import re
from contextlib import contextmanager


DEFAULT_SCHEMA = "manhwateca"


class DatabaseConfigurationError(RuntimeError):
    pass


class DatabaseConnectionError(RuntimeError):
    pass


def get_database_url(env=None) -> str:
    env = os.environ if env is None else env
    value = env.get("DATABASE_URL", "").strip()
    if not value:
        raise DatabaseConfigurationError(
            "DATABASE_URL não foi definido. Configure o .env antes de usar "
            "PostgreSQL."
        )
    return value


def _load_psycopg():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ModuleNotFoundError as error:
        raise DatabaseConnectionError(
            "Dependência psycopg não instalada. Execute "
            "`pip install -r requirements.txt`."
        ) from error
    return psycopg, dict_row


def connect(database_url=None, *, connect_fn=None, schema=DEFAULT_SCHEMA):
    database_url = database_url or get_database_url()
    if connect_fn is None:
        psycopg, dict_row = _load_psycopg()
        connect_fn = lambda url: psycopg.connect(url, row_factory=dict_row)

    try:
        connection = connect_fn(database_url)
        _set_search_path(connection, schema)
        return connection
    except DatabaseConfigurationError:
        raise
    except DatabaseConnectionError:
        raise
    except Exception as error:
        raise DatabaseConnectionError(
            f"Não foi possível conectar ao PostgreSQL: {error}"
        ) from error


def _set_search_path(connection, schema: str) -> None:
    if not schema:
        return

    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {_quote_identifier(schema)}, public")


def _quote_identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise DatabaseConfigurationError(
            f"Schema PostgreSQL inválido: {value!r}"
        )
    return f'"{value}"'


@contextmanager
def transaction(database_url=None, *, connect_fn=None, schema=DEFAULT_SCHEMA):
    connection = connect(
        database_url,
        connect_fn=connect_fn,
        schema=schema,
    )
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

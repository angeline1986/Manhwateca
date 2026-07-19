from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
)
from manhwateca.database.manga_repository import MangaRepository


class MangaUpdatesStatusUnavailable(RuntimeError):
    pass


def mangaupdates_status(
    project_root,
    *,
    ttl_days=30,
    batch_size=10,
    repository_factory=MangaRepository,
):
    try:
        return _database_status(
            repository_factory(),
            batch_size=batch_size,
            ttl_days=ttl_days,
        )
    except (DatabaseConfigurationError, DatabaseConnectionError) as error:
        raise MangaUpdatesStatusUnavailable(
            "Não foi possível carregar o status do MangaUpdates."
        ) from error


def _database_status(repository, *, batch_size, ttl_days):
    records = repository.list_mangas()
    confirmed = [
        record for record in records
        if getattr(record, "work_code", None)
    ]
    missing_details = [
        record for record in confirmed
        if (
            not getattr(record, "mangaupdates_url", None)
            or not getattr(record, "cover_url", None)
        )
    ]
    calls = [_public_record(record) for record in missing_details]
    forced_calls = [_public_record(record) for record in confirmed]
    return {
        "source": {
            "kind": "postgresql",
            "label": "PostgreSQL",
            "detail": "vw_mangas",
        },
        "summary": {
            "confirmed_ids": len(confirmed),
            "cached_ids": len(confirmed) - len(missing_details),
            "calls_needed": len(calls),
            "next_batch": len(calls[:batch_size]),
            "force_refresh_calls": len(forced_calls),
            "force_refresh_batch": len(forced_calls[:batch_size]),
            "batch_size": batch_size,
            "ttl_days": ttl_days,
        },
        "next_batch": calls[:batch_size],
        "force_refresh_batch": forced_calls[:batch_size],
    }


def _public_record(record):
    return {
        "name": record.title,
        "id": record.work_code,
        "title": record.title,
    }

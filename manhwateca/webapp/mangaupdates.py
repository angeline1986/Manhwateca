import json
from pathlib import Path

from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
)
from manhwateca.database.manga_repository import MangaRepository
from manhwateca.mangaupdates_service.review.data import (
    CONFIRMED_STATUSES,
    consolidate_review_items,
)
from manhwateca.mangaupdates_service.review.decisions import (
    apply_decisions,
    load_items,
)


IDS_PATH = Path("reports/integrations/buscaIds.json")
CSV_PATH = Path("reports/integrations/manhwateca_import.csv")
METADATA_PATH = Path("config/catalog_metadata.json")


def review_payload(project_root, repository_factory=MangaRepository):
    root = Path(project_root)
    database_payload = _database_review_payload(repository_factory)
    if database_payload is not None:
        return database_payload

    return _legacy_review_payload(root)


def _database_review_payload(repository_factory):
    try:
        repository = repository_factory()
        decisions = repository.list_decisions(
            decision_type="mangaupdates_match",
            status="pending",
        )
        confirmed = sum(
            bool(getattr(record, "work_code", None))
            for record in repository.list_mangas()
        )
    except (DatabaseConfigurationError, DatabaseConnectionError):
        return None

    if not decisions:
        return None

    items = [_decision_to_item(decision) for decision in decisions]
    review = [
        item for item in items
        if item.get("Status") == "Revisar"
    ]
    return {
        "source": {
            "kind": "postgresql",
            "label": "PostgreSQL",
            "detail": "decision_queue",
            "role": "fila de revisão de IDs",
        },
        "summary": {
            "total": len(items),
            "review": len(review),
            "confirmed": confirmed,
            "pending": 0,
        },
        "items": [_public_item(item) for item in review],
    }


def _legacy_review_payload(root):
    path = root / IDS_PATH
    items = load_items(path) if path.is_file() else []
    review = consolidate_review_items(
        items,
        csv_path=root / CSV_PATH,
        metadata_path=root / METADATA_PATH,
    )
    return {
        "source": {
            "kind": "json",
            "label": "JSON legado",
            "detail": str(IDS_PATH),
            "role": "staging de revisão de IDs",
        },
        "summary": {
            "total": len(items),
            "review": len(review),
            "confirmed": sum(
                item.get("Status") in CONFIRMED_STATUSES for item in items
            ),
            "pending": sum(not item.get("Status") for item in items),
        },
        "items": [_public_item(item) for item in review],
    }


def apply_review_decisions(
    project_root,
    decisions,
    repository_factory=MangaRepository,
):
    root = Path(project_root)
    path = root / IDS_PATH
    repository = _optional_repository(repository_factory)
    database_items = _pending_decision_items(repository)
    if database_items:
        return apply_decisions(
            decisions,
            _merge_json_mirror(path, database_items),
            path if path.exists() else None,
            decision_repository=repository,
        )
    items = load_items(path)
    return apply_decisions(
        decisions,
        items,
        path,
        decision_repository=repository,
    )


def _optional_repository(repository_factory=MangaRepository):
    try:
        return repository_factory()
    except (DatabaseConfigurationError, DatabaseConnectionError):
        return None


def _pending_decision_items(repository):
    if repository is None:
        return []
    try:
        decisions = repository.list_decisions(
            decision_type="mangaupdates_match",
            status="pending",
        )
    except Exception:
        return []
    return [_decision_to_item(decision) for decision in decisions]


def _merge_json_mirror(path, database_items):
    if not path.exists():
        return database_items
    try:
        legacy = load_items(path)
    except (OSError, ValueError):
        return database_items
    by_name = {item.get("Nome"): item for item in legacy}
    for item in database_items:
        by_name[item.get("Nome")] = item
    return list(by_name.values())


def _decision_to_item(decision):
    payload = _payload_dict(
        decision.get("payload")
        or decision.get("data")
        or decision.get("metadata")
    )
    name = (
        payload.get("nome")
        or decision.get("title")
        or decision.get("name")
        or decision.get("manga_title")
        or decision.get("work_title")
    )
    return {
        "Nome": name,
        "Nome decisão": name,
        "Status": "Revisar",
        "IDs": payload.get("candidatos") or payload.get("IDs") or [],
        "Nomes relacionados": payload.get("nomes_relacionados", []),
    }


def _payload_dict(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            data = json.loads(value)
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}
    return {}


def _public_item(item):
    candidates = [
        _public_candidate(candidate)
        for candidate in item.get("IDs", [])
        if float(candidate.get("pontuacao") or 0) > 0.70
        and candidate.get("bl") is not False
    ]
    return {
        "nome": item.get("Nome"),
        "nome_decisao": item.get("Nome decisão") or item.get("Nome"),
        "relacionados": item.get("Nomes relacionados", []),
        "candidates": candidates,
    }


def _public_candidate(candidate):
    return {
        key: candidate.get(key)
        for key in (
            "id", "titulo", "tipo", "ano", "url", "descricao",
            "pontuacao", "generos", "bl",
        )
    }

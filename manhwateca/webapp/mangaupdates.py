import json

from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    connect,
)
from manhwateca.database.manga_repository import MangaRepository
from manhwateca.webapp.candidate_filters import ranked_unique_candidates
from manhwateca.webapp.mangaupdates_review import flow_candidates_review_payload
from manhwateca.mangaupdates_service.review.decisions import (
    apply_decisions,
)


class MangaUpdatesReviewUnavailable(RuntimeError):
    pass


def review_payload(
    project_root,
    repository_factory=MangaRepository,
    connection_factory=connect,
):
    flow_payload = flow_candidates_review_payload(connection_factory)
    if flow_payload is not None and flow_payload["items"]:
        return flow_payload

    database_payload = _database_review_payload(repository_factory)
    if database_payload is not None:
        return database_payload

    raise MangaUpdatesReviewUnavailable(
        "Não foi possível carregar a fila de revisão."
    )

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


def apply_review_decisions(
    project_root,
    decisions,
    repository_factory=MangaRepository,
    connection_factory=connect,
):
    repository = _require_repository(repository_factory)
    flow_items = _flow_review_items(connection_factory)
    database_items = flow_items or _pending_decision_items(repository)
    return apply_decisions(
        decisions,
        database_items,
        None,
        decision_repository=repository,
    )


def _flow_review_items(connection_factory):
    payload = flow_candidates_review_payload(connection_factory)
    if payload is None or not payload.get("items"):
        return []
    return [
        {
            "Nome": item.get("localTitle") or item.get("nome"),
            "Nome decisão": item.get("nome_decisao") or item.get("localTitle") or item.get("nome"),
            "Status": "Revisar",
            "IDs": item.get("candidates") or [],
            "Nomes relacionados": item.get("alternativeTitles") or [],
        }
        for item in payload.get("items", [])
    ]


def _optional_repository(repository_factory=MangaRepository):
    try:
        repository = repository_factory()
        repository.list_decisions(
            decision_type="mangaupdates_match",
            status="pending",
        )
        return repository
    except (DatabaseConfigurationError, DatabaseConnectionError):
        return None


def _require_repository(repository_factory=MangaRepository):
    repository = _optional_repository(repository_factory)
    if repository is None:
        raise MangaUpdatesReviewUnavailable(
            "Não foi possível carregar a fila de revisão."
        )
    return repository


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
        for candidate in ranked_unique_candidates(item.get("IDs", []))
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

from pathlib import Path

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


def review_payload(project_root):
    root = Path(project_root)
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


def apply_review_decisions(project_root, decisions):
    path = Path(project_root) / IDS_PATH
    items = load_items(path)
    return apply_decisions(decisions, items, path)


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

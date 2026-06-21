import csv
import json
from pathlib import Path

from manhwateca.mangaupdates_service.candidates import CONFIRMED_STATUSES
from manhwateca.notion_sync.matching import normalize_title
from manhwateca.webapp.data_source import active_catalog_source
from manhwateca.webapp.notion import notion_status
from manhwateca.webapp.notion_metadata import metadata_status


CATALOG_PATH = Path("data/mangas.json")
CSV_PATH = Path("reports/integrations/manhwateca_import.csv")
IDS_PATH = Path("reports/integrations/buscaIds.json")
SYNC_STATE_PATH = Path("reports/integrations/sync_state.json")


def pending_payload(project_root):
    root = Path(project_root)
    source = active_catalog_source(root)
    items = []
    items.extend(_catalog_pending(root))
    items.extend(_mangaupdates_pending(root))
    if source["kind"] != "postgresql":
        items.extend(_csv_pending(root))
    items.extend(_notion_pending(root))
    return {
        "total": len(items),
        "source": {
            key: value
            for key, value in source.items()
            if key != "mangas"
        },
        "items": items,
        "empty_message": (
            "Nenhuma pendência acionável encontrada."
            if not items
            else None
        ),
    }


def _catalog_pending(root):
    status = notion_status(root)
    uncataloged = status.get("summary", {}).get("uncataloged", 0)
    if uncataloged:
        return [_item(
            "catalog",
            "Catalogar biblioteca",
            f"{uncataloged} obra(s) no Drive ainda não estão em data/mangas.json.",
            "catalog_scan",
            "library",
        )]
    return []


def _mangaupdates_pending(root):
    path = root / IDS_PATH
    if not path.is_file():
        return []
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [_item(
            "mangaupdates",
            "Revisar IDs",
            "buscaIds.json está inválido e precisa de revisão.",
            None,
            "mangaupdates",
            severity="warning",
        )]
    review = sum(1 for item in items if item.get("Status") == "Revisar")
    confirmed_without_cache = _confirmed_without_cache(root, items)
    pending = []
    if review:
        pending.append(_item(
            "mangaupdates",
            "Revisar correspondências",
            f"{review} obra(s) precisam de decisão de ID.",
            None,
            "mangaupdates",
        ))
    if confirmed_without_cache:
        pending.append(_item(
            "mangaupdates",
            "Consultar detalhes na API",
            f"{confirmed_without_cache} ID(s) confirmados ainda não têm cache.",
            "mangaupdates_details",
            "mangaupdates",
        ))
    return pending


def _csv_pending(root):
    catalog_names = _catalog_names(root / CATALOG_PATH)
    csv_rows = _csv_rows(root / CSV_PATH)
    csv_names = _csv_names_from_rows(csv_rows)
    missing = catalog_names - csv_names
    orphaned = [
        row for row in csv_rows
        if row.get("Correspondência API") == "Fora do catálogo local"
    ]
    items = []
    if missing:
        items.append(_item(
            "csv",
            "Atualizar CSV",
            f"{len(missing)} obra(s) catalogadas ainda não aparecem no CSV.",
            "mangaupdates_csv",
            "mangaupdates",
        ))
    if orphaned:
        items.append(_item(
            "csv",
            "Revisar obras fora do catálogo",
            f"{len(orphaned)} linha(s) do CSV não aparecem mais no catálogo local.",
            None,
            "mangaupdates",
            severity="warning",
        ))
    return items


def _notion_pending(root):
    status = notion_status(root)
    metadata = metadata_status(root)
    items = []
    summary = status.get("summary", {})
    if summary.get("pending"):
        items.append(_item(
            "notion",
            "Importar próximo lote",
            f"{summary['pending']} página(s) ainda precisam ser criadas.",
            "notion_simulate_batch",
            "notion",
        ))
    if status.get("stale"):
        items.append(_item(
            "notion",
            "Simular catálogo no Notion",
            "O status do Notion está desatualizado em relação ao catálogo.",
            "notion_simulate_batch",
            "notion",
        ))
    meta_summary = metadata.get("summary", {})
    if meta_summary.get("updates"):
        items.append(_item(
            "notion",
            "Aplicar metadados",
            f"{meta_summary['updates']} página(s) têm metadados pendentes.",
            "notion_csv_preview",
            "notion",
        ))
    items.extend(_sync_state_pending(root))
    return items


def _sync_state_pending(root):
    path = root / SYNC_STATE_PATH
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    statuses = {}
    for item in data.get("works", {}).values():
        status = item.get("status")
        statuses[status] = statuses.get(status, 0) + 1
    pending = statuses.get("pendente", 0)
    missing = statuses.get("ausente_no_notion", 0)
    duplicate = statuses.get("duplicado", 0)
    items = []
    if pending:
        items.append(_item(
            "notion",
            "Aplicar sincronização pendente",
            f"{pending} obra(s) simuladas ainda não foram aplicadas.",
            "notion_csv_apply",
            "notion",
        ))
    if missing:
        items.append(_item(
            "notion",
            "Resolver ausentes no Notion",
            f"{missing} obra(s) do CSV não foram encontradas no Notion.",
            "notion_csv_preview",
            "notion",
            severity="warning",
        ))
    if duplicate:
        items.append(_item(
            "notion",
            "Resolver duplicadas no Notion",
            f"{duplicate} obra(s) têm páginas duplicadas no Notion.",
            None,
            "notion",
            severity="danger",
        ))
    return items


def _confirmed_without_cache(root, items):
    cache_path = root / "data/mangaupdates.json"
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        cache = {}
    return sum(
        1
        for item in items
        if item.get("Status") in CONFIRMED_STATUSES
        and item.get("ID")
        and str(item["ID"]) not in cache
    )


def _catalog_names(path):
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {
        normalize_title(item.get("nome"))
        for item in catalog
        if isinstance(item, dict) and item.get("nome")
    }


def _csv_rows(path):
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _csv_names_from_rows(rows):
    names = set()
    for row in rows:
        for value in (row.get("Nome"), row.get("Alias")):
            for title in (value or "").split("|"):
                if title.strip():
                    names.add(normalize_title(title))
    return names


def _item(kind, title, detail, action, page, severity="info"):
    return {
        "kind": kind,
        "title": title,
        "detail": detail,
        "action": action,
        "page": page,
        "severity": severity,
    }

import json
from pathlib import Path

from manhwateca.notion_sync.sync_plan import build_sync_result


STATUS_PATH = Path("reports/integrations/notion_csv_status.json")
CSV_PATH = Path("reports/integrations/manhwateca_import.csv")
SYNC_STATE_PATH = Path("reports/integrations/sync_state.json")


def metadata_status(project_root):
    root = Path(project_root)
    path = root / STATUS_PATH
    if not path.is_file():
        return _empty(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty(root, "O status dos metadados está inválido.")
    summary = data.get("resumo", {})
    return {
        "available": True,
        "csv_available": (root / CSV_PATH).is_file(),
        "source": data.get("fonte") or _source(root),
        "updated_at": data.get("atualizado_em"),
        "mode": data.get("modo"),
        "summary": {
            "updates": summary.get("atualizacoes", 0),
            "unchanged": summary.get("sem_alteracao", 0),
            "missing": summary.get("ausentes", 0),
            "duplicates": summary.get("duplicadas", 0),
        },
        "updates": data.get("atualizacoes", []),
        "unchanged": data.get("sem_alteracao", []),
        "missing": data.get("ausentes", []),
        "duplicates": data.get("duplicadas", []),
        "sync": _sync_payload(data),
        "sync_state": _sync_state(root),
        "error": None,
    }


def _empty(root, error=None):
    return {
        "available": False,
        "csv_available": (root / CSV_PATH).is_file(),
        "source": _source(root),
        "updated_at": None,
        "mode": None,
        "summary": {
            "updates": 0,
            "unchanged": 0,
            "missing": 0,
            "duplicates": 0,
        },
        "updates": [],
        "unchanged": [],
        "missing": [],
        "duplicates": [],
        "sync": _sync_payload({"resumo": {}}, error) if error else None,
        "sync_state": _sync_state(root),
        "error": error,
    }


def _sync_payload(data, error=None):
    summary = data.get("resumo", {})
    sync_summary = {
        "updates": data.get(
            "atualizacoes",
            summary.get("atualizacoes", summary.get("updates", 0)),
        ),
        "updated": summary.get("atualizacoes", summary.get("updates", 0)),
        "unchanged": data.get(
            "sem_alteracao",
            summary.get("sem_alteracao", summary.get("unchanged", 0)),
        ),
        "missing": _item_or_positive_count(data, summary, "ausentes", "missing"),
        "duplicates": _item_or_positive_count(
            data,
            summary,
            "duplicadas",
            "duplicates",
        ),
    }
    if error:
        sync_summary["error"] = error
    evidence = "unavailable" if error else "legacy_report"
    source_label = "Indisponível" if error else "Relatório legado"
    return _serialize_sync_result(
        build_sync_result(sync_summary),
        evidence=evidence,
        source_label=source_label,
    )


def _item_or_positive_count(data, summary, item_key, fallback_key):
    if item_key in data:
        return data[item_key]
    count = summary.get(item_key, summary.get(fallback_key, 0))
    return count if count else None


def _serialize_sync_result(result, evidence, source_label):
    return {
        "status": result.status.value,
        "next_action": result.next_action.value,
        "evidence": evidence,
        "validated_against_notion": False,
        "source_label": source_label,
        "created_count": result.created_count,
        "updated_count": result.updated_count,
        "missing_count": result.missing_count,
        "duplicate_count": result.duplicate_count,
        "unchanged_count": result.unchanged_count,
        "blockers": [
            {
                "code": blocker.code,
                "work_id": blocker.work_id,
                "work_title": blocker.work_title,
                "message": blocker.message,
                "severity": blocker.severity.value,
                "next_action": blocker.next_action.value,
            }
            for blocker in result.blockers
        ],
    }


def _source(root):
    return {
        "kind": "csv",
        "label": "CSV legado",
        "detail": str(CSV_PATH),
        "available": (root / CSV_PATH).is_file(),
    }


def _sync_state(root):
    path = root / SYNC_STATE_PATH
    if not path.is_file():
        return {
            "available": False,
            "updated_at": None,
            "total": 0,
            "statuses": {},
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "available": False,
            "updated_at": None,
            "total": 0,
            "statuses": {},
        }
    works = data.get("works", {})
    statuses = {}
    for item in works.values():
        status = item.get("status", "desconhecido")
        statuses[status] = statuses.get(status, 0) + 1
    return {
        "available": True,
        "updated_at": data.get("updated_at"),
        "total": len(works),
        "statuses": statuses,
    }

import json
from pathlib import Path


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
        "sync_state": _sync_state(root),
        "error": error,
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

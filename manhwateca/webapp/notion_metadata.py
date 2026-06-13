import json
from pathlib import Path


STATUS_PATH = Path("reports/integrations/notion_csv_status.json")
CSV_PATH = Path("reports/integrations/manhwateca_import.csv")


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
        "updated_at": data.get("atualizado_em"),
        "mode": data.get("modo"),
        "summary": {
            "updates": summary.get("atualizacoes", 0),
            "missing": summary.get("ausentes", 0),
            "duplicates": summary.get("duplicadas", 0),
        },
        "updates": data.get("atualizacoes", []),
        "missing": data.get("ausentes", []),
        "duplicates": data.get("duplicadas", []),
        "error": None,
    }


def _empty(root, error=None):
    return {
        "available": False,
        "csv_available": (root / CSV_PATH).is_file(),
        "updated_at": None,
        "mode": None,
        "summary": {"updates": 0, "missing": 0, "duplicates": 0},
        "updates": [],
        "missing": [],
        "duplicates": [],
        "error": error,
    }

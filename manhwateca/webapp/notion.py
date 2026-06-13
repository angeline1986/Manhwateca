import json
from pathlib import Path


STATUS_PATH = Path("reports/integrations/notion_import_status.json")


def notion_status(project_root):
    path = Path(project_root) / STATUS_PATH
    if not path.is_file():
        return _empty_status()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_status(error="O arquivo de status está inválido.")
    summary = data.get("resumo", {})
    return {
        "available": True,
        "updated_at": data.get("atualizado_em"),
        "mode": data.get("modo"),
        "summary": {
            "catalog": summary.get("total_catalogo", 0),
            "imported": summary.get("total_importadas", 0),
            "current_batch": summary.get("importadas_neste_lote", 0),
            "pending": summary.get("total_pendentes", 0),
            "duplicates": summary.get("total_duplicadas", 0),
        },
        "current_batch": data.get("importadas_neste_lote", []),
        "pending": data.get("pendentes", []),
        "duplicates": data.get("duplicadas", []),
        "error": None,
    }


def _empty_status(error=None):
    return {
        "available": False,
        "updated_at": None,
        "mode": None,
        "summary": {
            "catalog": 0,
            "imported": 0,
            "current_batch": 0,
            "pending": 0,
            "duplicates": 0,
        },
        "current_batch": [],
        "pending": [],
        "duplicates": [],
        "error": error,
    }

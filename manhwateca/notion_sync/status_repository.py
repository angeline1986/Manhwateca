import json
from datetime import datetime

from manhwateca.notion_sync.matching import normalize_title


def write_import_status(summary, mode, applied=False, path=None):
    created_titles = summary["created_titles"] if applied else []
    pending_titles = list(summary["pending_titles"])
    if not applied:
        pending_titles.extend(summary["created_titles"])
    pending_titles = sorted(set(pending_titles), key=normalize_title)
    imported = sorted(
        set(summary["matched_titles"] + created_titles),
        key=normalize_title,
    )
    payload = {
        "atualizado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "modo": mode,
        "resumo": {
            "total_catalogo": summary["catalog_total"],
            "total_importadas": len(imported),
            "importadas_neste_lote": len(created_titles),
            "total_pendentes": len(pending_titles),
            "total_duplicadas": len(summary["duplicate_titles"]),
        },
        "importadas_neste_lote": created_titles,
        "importadas": imported,
        "pendentes": pending_titles,
        "duplicadas": summary["duplicate_titles"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)

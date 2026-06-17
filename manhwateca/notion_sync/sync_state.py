import hashlib
import json
from datetime import datetime

from manhwateca.notion_sync.matching import normalize_title


def row_hash(row):
    return _hash(row)


def catalog_hash(item):
    return _hash(item) if item else None


def build_state_records(summary, rows, catalog=None, applied=False):
    catalog = catalog or {}
    records = {}
    by_name = {row.get("Nome", "").strip(): row for row in rows}
    for item in summary.get("updates", []):
        name = item["name"]
        records[name] = _record(
            name,
            by_name.get(name),
            catalog.get(normalize_title(name)),
            item.get("page_id"),
            "sincronizado" if applied else "pendente",
        )
    for item in summary.get("unchanged", []):
        name = item["name"] if isinstance(item, dict) else item
        page_id = item.get("page_id") if isinstance(item, dict) else None
        records[name] = _record(
            name,
            by_name.get(name),
            catalog.get(normalize_title(name)),
            page_id,
            "sincronizado",
        )
    for name in summary.get("missing", []):
        records[name] = _record(
            name,
            by_name.get(name),
            catalog.get(normalize_title(name)),
            None,
            "ausente_no_notion",
        )
    for name in summary.get("duplicates", []):
        records[name] = _record(
            name,
            by_name.get(name),
            catalog.get(normalize_title(name)),
            None,
            "duplicado",
        )
    return records


def write_sync_state(records, path):
    payload = {
        "updated_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "works": records,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return payload


def _record(name, row, catalog_item, page_id, status):
    return {
        "nome": name,
        "notion_page_id": page_id,
        "csv_hash": row_hash(row or {}),
        "catalog_hash": catalog_hash(catalog_item),
        "status": status,
    }


def _hash(value):
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

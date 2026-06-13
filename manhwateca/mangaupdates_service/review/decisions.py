import json
import shutil
from datetime import datetime


def load_items(path):
    with path.open(encoding="utf-8") as file:
        items = json.load(file)
    if not isinstance(items, list):
        raise ValueError(f"Formato inválido em {path}: era esperada uma lista.")
    return items


def load_decisions(path):
    with path.open(encoding="utf-8") as file:
        decisions = json.load(file)
    if not isinstance(decisions, list):
        raise ValueError(
            f"Formato inválido em {path}: era esperada uma lista de decisões."
        )
    return decisions


def backup_path(path):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return path.with_name(f"{path.stem}.backup-{timestamp}{path.suffix}")


def import_decisions(decisions_path, ids_path):
    items = load_items(ids_path)
    decisions = load_decisions(decisions_path)
    return apply_decisions(decisions, items, ids_path)


def apply_decisions(decisions, items, ids_path):
    by_name, duplicate_names = _index_items(items)
    applied = []
    rejected = []
    seen = set()

    for decision in decisions:
        validated, error = _validate_decision(
            decision,
            items,
            by_name,
            duplicate_names,
            seen,
        )
        if error:
            rejected.append(error)
            continue

        name, series_id, candidate_title = validated
        item = items[by_name[name]]
        item["Status"] = "Confirmado manualmente"
        item["ID"] = series_id
        item["Nome encontrado"] = candidate_title
        item.pop("IDs", None)
        applied.append(name)

    backup = _persist_changes(items, ids_path) if applied else None
    return applied, rejected, backup


def _index_items(items):
    by_name = {}
    duplicate_names = set()
    for position, item in enumerate(items):
        name = str(item.get("Nome") or "").strip()
        if name in by_name:
            duplicate_names.add(name)
        by_name[name] = position
    return by_name, duplicate_names


def _validate_decision(
    decision,
    items,
    by_name,
    duplicate_names,
    seen,
):
    if not isinstance(decision, dict):
        return None, "Decisão inválida: era esperado um objeto."

    name = str(decision.get("Nome") or "").strip()
    series_id = decision.get("ID")
    selected_title = str(decision.get("Nome encontrado") or "").strip()
    manual_id = decision.get("Origem") == "ID informado manualmente"

    if not name or series_id in (None, ""):
        return None, "Decisão sem Nome ou ID."
    try:
        series_id = int(series_id)
    except (TypeError, ValueError):
        return None, f"{name}: ID inválido."
    if series_id <= 0:
        return None, f"{name}: ID deve ser um número positivo."
    if name in seen:
        return None, f"{name}: decisão duplicada no arquivo."
    seen.add(name)
    if name in duplicate_names:
        return None, f"{name}: nome duplicado no buscaIds.json."
    position = by_name.get(name)
    if position is None:
        return None, f"{name}: obra não encontrada no buscaIds.json."

    item = items[position]
    candidate = next(
        (
            candidate
            for candidate in item.get("IDs") or []
            if str(candidate.get("id")) == str(series_id)
        ),
        None,
    )
    if candidate is None and not manual_id:
        return None, (
            f"{name}: ID {series_id} não pertence aos candidatos exibidos."
        )

    candidate_title = (
        selected_title or f"ID {series_id}"
        if manual_id
        else str(candidate.get("titulo") or "").strip()
    )
    if (
        candidate
        and not manual_id
        and selected_title
        and selected_title != candidate_title
    ):
        return None, (
            f"{name}: título selecionado não corresponde ao candidato."
        )
    return (name, series_id, candidate_title), None


def _persist_changes(items, ids_path):
    backup = backup_path(ids_path)
    shutil.copy2(ids_path, backup)
    temporary = ids_path.with_suffix(f"{ids_path.suffix}.tmp")
    temporary.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(ids_path)
    return backup

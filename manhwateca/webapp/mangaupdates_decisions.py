from uuid import uuid4


def validate_decisions_payload(decisions, repository=None):
    blocked = []
    seen_ids = {}
    for decision in decisions:
        name = _name(decision)
        if not _valid_decision(decision):
            blocked.append({"name": name, "reason": "ID inválido ou ausente"})
            continue
        if isinstance(decision, str):
            continue
        if decision.get("Tipo") == "sem_correspondencia":
            if repository is not None and _target_work(repository, decision) is None:
                blocked.append({"name": name, "reason": "Obra local não encontrada no catálogo."})
            continue
        series_id = str(int(decision["ID"]))
        if series_id in seen_ids:
            blocked.append({
                "name": name,
                "reason": f"ID {series_id} também selecionado para {seen_ids[series_id]}.",
            })
            continue
        seen_ids[series_id] = name
        if repository is None:
            continue
        target = _target_work(repository, decision)
        if target is None:
            blocked.append({"name": name, "reason": "Obra local não encontrada no catálogo."})
            continue
        existing = repository.find_by_work_code(series_id)
        if existing is not None and int(existing.id) != int(target.id):
            blocked.append({
                "name": name,
                "reason": f"ID {series_id} já está associado a {existing.title}.",
            })
    return {
        "ready": len(decisions) - len(blocked),
        "blocked": len(blocked),
        "valid": not blocked and bool(decisions),
        "error": "Existem decisões bloqueadas." if blocked else None,
        "items": [
            {
                "name": _name(decision),
                "id": _id(decision),
                "origin": _origin(decision),
            }
            for decision in decisions
        ],
        "blocks": blocked,
    }


def apply_decisions_payload(project_root, decisions, apply_callback):
    validation = validate_decisions_payload(decisions)
    if not validation["valid"]:
        return {
            "jobId": None,
            "accepted": validation["ready"],
            "blocked": validation["blocked"],
            "validation": validation,
            "rejected": validation["blocks"],
        }, 422
    applied, rejected, backup = apply_callback(project_root, decisions)
    return {
        "jobId": f"mangaupdates-apply-{uuid4().hex[:10]}",
        "accepted": len(applied),
        "blocked": len(rejected),
        "applied": applied,
        "rejected": rejected,
        "backup": str(backup.relative_to(project_root)) if backup else None,
        "status": "completed" if not rejected else "completed_with_warnings",
    }, 200 if not rejected else 422


def _valid_id(value):
    try:
        normalized = str(value).strip()
        return normalized.isdecimal() and int(normalized) > 0
    except (TypeError, ValueError, OverflowError):
        return False


def _queue_id_contract(decisions):
    return all(isinstance(decision, str) for decision in decisions)


def _valid_decision(decision):
    if isinstance(decision, str):
        return bool(decision.strip())
    if not isinstance(decision, dict):
        return False
    if decision.get("Tipo") == "sem_correspondencia":
        return bool(_name(decision).strip())
    return _valid_id(decision.get("ID"))


def _name(decision):
    if isinstance(decision, str):
        return decision
    if not isinstance(decision, dict):
        return "Decisão inválida"
    return decision.get("Nome") or "Obra sem título"


def _id(decision):
    if isinstance(decision, str):
        return decision
    if not isinstance(decision, dict):
        return None
    if decision.get("Tipo") == "sem_correspondencia":
        return None
    return decision.get("ID")


def _origin(decision):
    if isinstance(decision, str):
        return "Fila de decisões"
    if not isinstance(decision, dict):
        return "Decisão inválida"
    return decision.get("Origem") or "Candidato selecionado"


def _target_work(repository, decision):
    queue_id = str(decision.get("queueId") or "")
    if queue_id.startswith("flow_"):
        try:
            return repository.find_by_id(int(queue_id.removeprefix("flow_")))
        except ValueError:
            return None
    return repository.find_by_normalized_title(_name(decision))

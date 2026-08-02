from uuid import uuid4


def validate_decisions_payload(decisions):
    blocked = [
        {
            "name": _name(decision),
            "reason": "ID inválido ou ausente",
        }
        for decision in decisions
        if not _valid_decision(decision)
    ]
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
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def _queue_id_contract(decisions):
    return all(isinstance(decision, str) for decision in decisions)


def _valid_decision(decision):
    if isinstance(decision, str):
        return bool(decision.strip())
    if decision.get("Tipo") == "sem_correspondencia":
        return bool(_name(decision).strip())
    return _valid_id(decision.get("ID"))


def _name(decision):
    if isinstance(decision, str):
        return decision
    return decision.get("Nome") or "Obra sem título"


def _id(decision):
    if isinstance(decision, str):
        return decision
    if decision.get("Tipo") == "sem_correspondencia":
        return None
    return decision.get("ID")


def _origin(decision):
    if isinstance(decision, str):
        return "Fila de decisões"
    return decision.get("Origem") or "Candidato selecionado"

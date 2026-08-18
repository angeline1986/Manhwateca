import json
from pathlib import Path

from manhwateca.database.connection import transaction
from manhwateca.database.manga_repository import MangaRepository
from manhwateca.webapp.catalog import load_catalog

from manhwateca.library_organizer.discovery import (
    find_manga_folders,
    is_manga_folder,
)
from manhwateca.library_organizer.grouping import (
    get_current_group,
    get_group,
    is_group_folder,
    is_legacy_container,
)
from manhwateca.library_organizer.planning import (
    build_plan,
    detect_conflicts,
    determine_status,
)
from manhwateca.shared.duplicates import detect_duplicates_organize
from manhwateca.shared.paths import get_required_path_env
from manhwateca.file_normalizer import workflow as rename_workflow


def structure_review_payload(manga_root=None):
    root = Path(manga_root or get_required_path_env("MANGA_ROOT")).resolve()

    def detector(path):
        return is_manga_folder(path, is_group_folder, is_legacy_container)

    folders = find_manga_folders(root, is_group_folder, detector)
    plan = build_plan(
        folders,
        root,
        get_group,
        lambda path: get_current_group(path, root),
    )
    conflicts = detect_conflicts(plan)
    duplicates = detect_duplicates_organize(plan)
    return serialize_structure_review(plan, conflicts, duplicates, root)


def serialize_structure_review(plan, conflicts, duplicates, root):
    root = Path(root).resolve()
    duplicate_by_source = {}
    for duplicate in duplicates:
        for entry in duplicate.get("entries", []):
            duplicate_by_source[str(entry.get("source"))] = duplicate

    conflict_by_source = {}
    for conflict in conflicts:
        for item in conflict.get("items", []):
            conflict_by_source.setdefault(str(item["source"]), []).append(conflict)

    items = []
    seen_duplicates = set()

    for plan_item in plan:
        source_key = str(plan_item["source"])
        duplicate = duplicate_by_source.get(source_key)

        if duplicate:
            duplicate_key = duplicate.get("normalized") or source_key
            if duplicate_key in seen_duplicates:
                continue
            seen_duplicates.add(duplicate_key)
            related = [
                item for item in plan
                if str(item["source"]) in {
                    str(entry.get("source"))
                    for entry in duplicate.get("entries", [])
                }
            ]
            items.append(_duplicate_item(duplicate, related, root))
            continue

        item_conflicts = conflict_by_source.get(source_key, [])
        if item_conflicts:
            items.append(_conflict_item(plan_item, item_conflicts, root))
            continue

        items.append(_ok_item(plan_item, conflicts, duplicates, root))

    items.sort(key=lambda item: item["title"].casefold())
    summary = {
        "total": len(items),
        "divergences": sum(item["category"] == "divergence" for item in items),
        "duplicates": sum(item["category"] == "duplicate" for item in items),
        "ok": sum(item["category"] == "ok" for item in items),
    }
    return {
        "summary": summary,
        "items": items,
    }


def _duplicate_item(duplicate, related, root):
    sources = [
        _display_path(Path(entry["source"]), root)
        for entry in duplicate.get("entries", [])
    ]
    destinations = [
        _display_path(Path(entry["destination"]), root)
        for entry in duplicate.get("entries", [])
    ]
    destination = destinations[0] if destinations else ""
    files = sum(int(item.get("total_caps", 0) or 0) for item in related)
    title = related[0]["name"] if related else (
        duplicate.get("entries", [{}])[0].get("original") or "Obra"
    )

    return {
        "id": f"duplicate:{duplicate.get('normalized') or title}",
        "title": title,
        "category": "duplicate",
        "status": "Duplicado suspeito",
        "badge": "Duplicidade encontrada",
        "current_structure": f"{len(sources)} pastas",
        "expected_structure": "1 pasta",
        "files": files,
        "current_paths": sources,
        "expected_path": destination,
        "issue_title": "Duplicidade identificada",
        "issue_description": (
            f"A obra foi encontrada em {len(sources)} pastas que convergem "
            "para o mesmo destino esperado."
        ),
        "current_group": "",
        "expected_group": related[0].get("group", "") if related else "",
        "movement_required": any(not item.get("is_correct") for item in related),
        "action": "preview",
    }


def _conflict_item(item, item_conflicts, root):
    source = Path(item["source"])
    destination = Path(item["destination"])
    paths = [_display_path(source, root)]
    if destination.exists():
        destination_display = _display_path(destination, root)
        if destination_display not in paths:
            paths.append(destination_display)

    reasons = sorted({
        conflict.get("reason", "conflito")
        for conflict in item_conflicts
    })
    description = _conflict_description(reasons)

    return {
        "id": f"conflict:{source}",
        "title": item["name"],
        "category": "divergence",
        "status": "Conflito",
        "badge": "Revisão necessária",
        "current_structure": f"{len(paths)} pasta(s)",
        "expected_structure": "1 pasta",
        "files": int(item.get("total_caps", 0) or 0),
        "current_paths": paths,
        "expected_path": _display_path(destination, root),
        "issue_title": "Divergência identificada",
        "issue_description": description,
        "current_group": item.get("current_group") or "",
        "expected_group": item.get("group") or "",
        "movement_required": not bool(item.get("is_correct")),
        "action": "preview",
    }


def _ok_item(item, conflicts, duplicates, root):
    status = determine_status(item, conflicts, duplicates)
    movement_required = not bool(item.get("is_correct"))
    if movement_required:
        description = (
            "Nenhum conflito estrutural foi identificado. A pasta pode precisar "
            "de movimentação alfabética, que será tratada em Organizar pastas."
        )
    else:
        description = "A estrutura atual não possui conflito estrutural."

    return {
        "id": f"ok:{item['source']}",
        "title": item["name"],
        "category": "ok",
        "status": status,
        "badge": "Estrutura conforme",
        "current_structure": "1 pasta",
        "expected_structure": "1 pasta",
        "files": int(item.get("total_caps", 0) or 0),
        "current_paths": [_display_path(Path(item["source"]), root)],
        "expected_path": _display_path(Path(item["destination"]), root),
        "issue_title": "Estrutura sem conflito",
        "issue_description": description,
        "current_group": item.get("current_group") or "",
        "expected_group": item.get("group") or "",
        "movement_required": movement_required,
        "action": "none",
    }


def _conflict_description(reasons):
    if "both" in reasons:
        return (
            "O destino esperado já existe e mais de uma pasta converge para "
            "esse mesmo destino."
        )
    if "destino_duplicado" in reasons:
        return "Mais de uma pasta converge para o mesmo destino esperado."
    if "destino_existente" in reasons:
        return (
            "O destino esperado já existe e é diferente da pasta encontrada."
        )
    return "O planner identificou um conflito estrutural que precisa de revisão."


def _display_path(path, root):
    path = Path(path)
    try:
        relative = path.resolve().relative_to(root)
    except (OSError, ValueError):
        return str(path)
    if str(relative) == ".":
        return root.name
    return str(Path(root.name) / relative)


def naming_review_payload():
    plan = rename_workflow.build_plan()
    conflicts = rename_workflow.detect_conflicts(plan)
    duplicates = rename_workflow.detect_duplicates(plan)
    return serialize_naming_review(plan, conflicts, duplicates)


def serialize_naming_review(plan, conflicts, duplicates):
    conflict_keys = {
        (conflict.get("manga"), conflict.get("conflict_name"))
        for conflict in conflicts
    }
    duplicate_mangas = {
        entry.get("original")
        for duplicate in duplicates
        for entry in duplicate.get("entries", [])
    }

    works = []
    for group, mangas in plan.items():
        for manga, files in mangas.items():
            changes = []
            for index, item in enumerate(files):
                conflict = (manga, item.get("new_name")) in conflict_keys
                blocked = conflict or manga in duplicate_mangas
                ambiguous = bool(item.get("multiple_images"))
                category = "blocked" if blocked else ("review" if ambiguous else "suggested")
                changes.append({
                    "id": f"{group}:{manga}:{index}:{item.get('old_name', '')}",
                    "kind": item.get("kind", "arquivo"),
                    "old_name": item.get("old_name", ""),
                    "new_name": item.get("new_name", ""),
                    "old_path": item.get("old_path", ""),
                    "new_path": item.get("new_path", ""),
                    "category": category,
                })

            if not changes:
                continue

            blocked_count = sum(change["category"] == "blocked" for change in changes)
            review_count = sum(change["category"] == "review" for change in changes)
            suggested_count = sum(change["category"] == "suggested" for change in changes)

            if blocked_count:
                category = "blocked"
                badge = "Bloqueio encontrado"
                reason = (
                    f"{blocked_count} arquivo(s) possuem conflito ou duplicidade e precisam "
                    "ser revisados antes da aplicação."
                )
            elif review_count:
                category = "review"
                badge = "Revisão necessária"
                reason = (
                    f"{review_count} arquivo(s) possuem ambiguidade e precisam de revisão."
                )
            else:
                category = "suggested"
                badge = "Sugestão disponível"
                reason = (
                    f"{suggested_count} arquivo(s) desta obra possuem sugestões de padronização."
                )

            works.append({
                "id": f"{group}:{manga}",
                "title": manga,
                "work": manga,
                "group": group,
                "category": category,
                "badge": badge,
                "reason": reason,
                "files_count": len(changes),
                "suggestions_count": suggested_count,
                "review_count": review_count,
                "blocked_count": blocked_count,
                "changes": changes,
            })

    works.sort(key=lambda item: item["work"].casefold())
    return {
        "summary": {
            "suggested": sum(item["category"] == "suggested" for item in works),
            "review": sum(item["category"] == "review" for item in works),
            "blocked": sum(item["category"] == "blocked" for item in works),
            "total": len(works),
        },
        "items": works,
    }



def folder_organization_payload(manga_root=None):
    root = Path(manga_root or get_required_path_env("MANGA_ROOT")).resolve()

    def detector(path):
        return is_manga_folder(path, is_group_folder, is_legacy_container)

    folders = find_manga_folders(root, is_group_folder, detector)
    plan = build_plan(
        folders,
        root,
        get_group,
        lambda path: get_current_group(path, root),
    )
    conflicts = detect_conflicts(plan)
    duplicates = detect_duplicates_organize(plan)
    return serialize_folder_organization(plan, conflicts, duplicates, root)


def serialize_folder_organization(plan, conflicts, duplicates, root):
    root = Path(root).resolve()

    conflict_sources = {
        str(item["source"])
        for conflict in conflicts
        for item in conflict.get("items", [])
    }
    duplicate_sources = {
        str(entry.get("source"))
        for duplicate in duplicates
        for entry in duplicate.get("entries", [])
    }

    items = []
    for plan_item in plan:
        source = Path(plan_item["source"])
        destination = Path(plan_item["destination"])
        source_key = str(source)

        blocked = source_key in conflict_sources or source_key in duplicate_sources
        movement_required = not bool(plan_item.get("is_correct"))

        if blocked:
            category = "review"
            badge = "Revisão necessária"
            reason = (
                "Há conflito ou duplicidade no destino esperado. "
                "A movimentação não deve ser aplicada automaticamente."
            )
        elif movement_required:
            category = "move"
            badge = "Movimento seguro"
            reason = (
                "A obra está fora da pasta esperada e pode ser movimentada "
                "na aplicação final."
            )
        else:
            category = "keep"
            badge = "Local correto"
            reason = "A obra já está na estrutura esperada."

        items.append({
            "id": f"folder:{source}",
            "title": plan_item["name"],
            "group": plan_item.get("group") or "",
            "category": category,
            "badge": badge,
            "source": _display_path(source, root),
            "destination": _display_path(destination, root),
            "conflicts": 1 if blocked else 0,
            "movement_required": movement_required,
            "reason": reason,
        })

    items.sort(key=lambda item: item["title"].casefold())

    return {
        "summary": {
            "move": sum(item["category"] == "move" for item in items),
            "review": sum(item["category"] == "review" for item in items),
            "keep": sum(item["category"] == "keep" for item in items),
            "total": len(items),
        },
        "items": items,
    }


ORGANIZATION_DECISION_TYPE = "organization_local"


def chapter_review_payload(project_root):
    mangas = load_catalog(project_root)
    return serialize_chapter_review(mangas)


def serialize_chapter_review(mangas):
    items = []

    for index, manga in enumerate(mangas or []):
        title = str(manga.get("nome") or "Obra sem título")
        gaps = [str(value) for value in (manga.get("missing_ranges") or []) if str(value).strip()]
        issues = [str(value) for value in (manga.get("count_issues") or []) if str(value).strip()]
        unparsed = [str(value) for value in (manga.get("unparsed_files") or []) if str(value).strip()]
        duplicate_issues = [
            issue for issue in issues
            if "sobrepos" in issue.casefold() or "duplic" in issue.casefold()
        ]
        other_issues = [
            issue for issue in issues
            if issue not in duplicate_issues and issue.casefold() != "lacunas"
        ]

        has_gap = bool(gaps) or any(issue.casefold() == "lacunas" for issue in issues)
        has_duplicate = bool(duplicate_issues)
        has_other = bool(other_issues or unparsed)
        status = str(manga.get("count_status") or "OK")
        status_problem = status.casefold() not in {"ok", "correto", "conforme"}
        has_divergence = has_gap or has_duplicate or has_other or status_problem

        filters = []
        if has_divergence:
            filters.append("Divergências")
        if has_gap:
            filters.append("Lacunas")
        if has_duplicate:
            filters.append("Duplicados")
        if not filters:
            filters.append("OK")

        if has_gap:
            badge = "Lacuna encontrada"
            issue_title = "Capítulo ausente"
            issue_description = (
                "Foram identificadas lacunas na sequência: "
                + (", ".join(gaps) if gaps else "verifique a auditoria detalhada.")
            )
            suggested = "Confirmar se a lacuna é intencional ou corrigir a origem."
        elif has_duplicate:
            badge = "Duplicidade encontrada"
            issue_title = "Capítulos sobrepostos"
            issue_description = " · ".join(duplicate_issues)
            suggested = "Comparar os arquivos sobrepostos antes de manter ou remover qualquer versão."
        elif has_other or status_problem:
            badge = "Revisão necessária"
            issue_title = "Divergência identificada"
            details = other_issues + [f"Arquivo não interpretado: {name}" for name in unparsed]
            issue_description = " · ".join(details) or f"Status da contagem: {status}."
            suggested = "Revisar a origem antes de qualquer alteração."
        else:
            badge = "Sequência válida"
            issue_title = "Sequência consistente"
            issue_description = "Nenhuma lacuna, duplicidade ou arquivo não interpretado foi informado."
            suggested = "Nenhuma correção necessária."

        latest = manga.get("main_caps", 0)
        gap_text = ", ".join(gaps) if gaps else "nenhuma"
        sequence = f"1–{latest} · lacunas: {gap_text}" if latest else f"Lacunas: {gap_text}"

        items.append({
            "id": f"chapter:{index}:{title}",
            "title": title,
            "category": "divergence" if has_divergence else "ok",
            "filters": filters,
            "badge": badge,
            "chapters": int(manga.get("chapters_found") or 0),
            "latest": manga.get("main_caps", 0),
            "gaps": gaps,
            "gap_count": len(gaps) if gaps else (1 if has_gap else 0),
            "duplicate_issues": duplicate_issues,
            "duplicate_count": len(duplicate_issues),
            "unparsed_files": unparsed,
            "status": status,
            "issue_title": issue_title,
            "issue_description": issue_description,
            "sequence": sequence,
            "suggested_action": suggested,
            "source_key": f"chapter:{title}",
        })

    items.sort(key=lambda item: item["title"].casefold())
    return {
        "summary": {
            "divergences": sum(item["category"] == "divergence" for item in items),
            "gaps": sum("Lacunas" in item["filters"] for item in items),
            "duplicates": sum("Duplicados" in item["filters"] for item in items),
            "total": len(items),
        },
        "items": items,
    }


def enqueue_organization_decision(payload):
    title = str(payload.get("title") or "").strip()
    source = str(payload.get("source") or "").strip()
    source_key = str(payload.get("source_key") or "").strip()
    if not title or not source:
        raise ValueError("Título e origem da pendência são obrigatórios.")

    review_category = str(payload.get("review_category") or "review").strip()
    decision_payload = {
        "review_category": review_category,
        "kind": payload.get("kind") or "Pendência",
        "detail": payload.get("detail") or "",
        "impact": payload.get("impact") or "",
        "suggested_action": payload.get("suggested_action") or "",
        "origin_label": payload.get("origin_label") or source,
        "metadata": payload.get("metadata") or {},
    }

    with transaction() as connection:
        repository = MangaRepository(connection=connection)
        saved = repository.enqueue_decision(
            decision_type=ORGANIZATION_DECISION_TYPE,
            source=source,
            title=title,
            source_key=source_key or None,
            payload=decision_payload,
            manga_name=title,
            status="pending",
        )

    if not saved:
        raise RuntimeError("A decision_queue não está disponível para registrar a pendência.")

    return {
        "status": "pending",
        "title": title,
        "source": source,
        "source_key": source_key,
    }


def resolve_organization_decision(payload):
    title = str(payload.get("title") or "").strip()
    source = str(payload.get("source") or "").strip()
    resolution = str(payload.get("resolution") or "").strip()
    if not title or not source or not resolution:
        raise ValueError("Título, origem e resolução são obrigatórios.")

    with transaction() as connection:
        repository = MangaRepository(connection=connection)
        resolved = repository.resolve_decision(
            decision_type=ORGANIZATION_DECISION_TYPE,
            source=source,
            title=title,
            resolution={
                "resolution": resolution,
                "note": payload.get("note") or "",
            },
            status="resolved",
        )

    if not resolved:
        raise ValueError("Pendência não encontrada ou já resolvida.")

    return {
        "status": "resolved",
        "title": title,
        "source": source,
        "resolution": resolution,
    }


def organization_pending_review_payload(repository_factory=MangaRepository):
    try:
        repository = repository_factory()
        rows = repository.list_decisions(
            decision_type=ORGANIZATION_DECISION_TYPE,
            status="pending",
        )
    except Exception as error:
        return {
            "summary": {"correct": 0, "decide": 0, "review": 0, "total": 0},
            "items": [],
            "warning": str(error),
        }

    items = []
    for row in rows:
        payload = _decision_payload(row)
        category = str(payload.get("review_category") or "review")
        if category not in {"correct", "decide", "review"}:
            category = "review"

        title = (
            row.get("title")
            or row.get("name")
            or row.get("manga_title")
            or row.get("work_title")
            or "Pendência"
        )
        source = row.get("source") or "organization"
        source_key = row.get("source_key") or ""

        items.append({
            "id": f"decision:{row.get('id') or source_key or title}",
            "title": title,
            "source": source,
            "source_key": source_key,
            "category": category,
            "kind": payload.get("kind") or "Pendência",
            "detail": payload.get("detail") or "",
            "impact": payload.get("impact") or "Requer revisão",
            "suggested_action": payload.get("suggested_action") or "",
            "origin_label": payload.get("origin_label") or source,
            "metadata": payload.get("metadata") or {},
        })

    items.sort(key=lambda item: item["title"].casefold())
    return {
        "summary": {
            "correct": sum(item["category"] == "correct" for item in items),
            "decide": sum(item["category"] == "decide" for item in items),
            "review": sum(item["category"] == "review" for item in items),
            "total": len(items),
        },
        "items": items,
    }


def _decision_payload(row):
    value = (
        row.get("payload")
        or row.get("data")
        or row.get("metadata")
        or {}
    )
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return decoded if isinstance(decoded, dict) else {}
    return {}

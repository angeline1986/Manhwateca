from manhwateca.mangaupdates_service.candidates import (
    add_catalog_titles_to_id_searches,
    apply_candidate_result,
    clean_confirmed_candidates,
    incomplete_review_items,
    load_id_searches,
    matches_initial_filter,
    normalize_initial_filter,
)


def fill_ids_file(
    path,
    metadata,
    search_candidates,
    save_function,
    wait_function,
    delay=3.0,
    limit=None,
    per_page=10,
    retry_review=False,
    catalog_path=None,
    initials="",
    decision_repository=None,
):
    items = load_id_searches(path)
    added = add_catalog_titles_to_id_searches(items, catalog_path)
    if added:
        save_function(path, items)
        print(f"[CATÁLOGO] {added} nova(s) obra(s) adicionada(s) ao JSON.")

    if clean_confirmed_candidates(items):
        save_function(path, items)

    processed = 0
    initial_filter = normalize_initial_filter(initials)
    for item in items:
        if item.get("ID"):
            continue
        if not matches_initial_filter(item["Nome"], initial_filter):
            continue
        if item.get("Status") == "Revisar" and not retry_review:
            continue
        if limit is not None and processed >= limit:
            break

        name = item["Nome"].strip()
        print(f"[BUSCAR ID] {name}")
        candidates, search_term = search_candidates(
            item,
            metadata,
            per_page=per_page,
        )
        selected = apply_candidate_result(item, candidates, search_term)
        if selected:
            print(
                f"[CONFIRMADO] {selected['id']} | "
                f"{selected['titulo']} | {selected['pontuacao']:.2f}"
            )
        else:
            print(f"[REVISAR] {name}: {len(candidates)} candidato(s)")
            _enqueue_match_decision(
                decision_repository,
                item,
                candidates,
                search_term,
            )

        save_function(path, items)
        processed += 1
        wait_function(delay)

    return items, processed


def refresh_incomplete_candidates(
    path,
    metadata,
    search_candidates,
    save_function,
    wait_function,
    delay=3.0,
    limit=10,
    per_page=10,
    decision_repository=None,
):
    items = load_id_searches(path)
    pending = incomplete_review_items(items)
    selected = pending[:limit] if limit is not None else pending

    for item in selected:
        name = item["Nome"].strip()
        print(f"[ATUALIZAR CANDIDATOS] {name}")
        candidates, search_term = search_candidates(
            item,
            metadata,
            per_page=per_page,
        )
        apply_candidate_result(item, candidates, search_term)
        if item.get("Status") == "Revisar":
            _enqueue_match_decision(
                decision_repository,
                item,
                candidates,
                search_term,
            )
        save_function(path, items)
        wait_function(delay)

    return len(selected), len(pending) - len(selected)


def _enqueue_match_decision(repository, item, candidates, search_term):
    if repository is None:
        return False
    name = str(item.get("Nome") or "").strip()
    if not name:
        return False
    try:
        return repository.enqueue_decision(
            decision_type="mangaupdates_match",
            source="mangaupdates",
            title=name,
            manga_name=name,
            source_key=str(search_term or name),
            payload={
                "nome": name,
                "termo_busca": search_term,
                "candidatos": candidates,
            },
        )
    except Exception:
        return False

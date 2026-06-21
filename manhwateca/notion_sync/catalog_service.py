from manhwateca.notion_sync.catalog_properties import build_properties
from manhwateca.notion_sync.matching import (
    catalog_title_candidates,
    normalize_title,
)
from manhwateca.notion_sync.pages import load_existing_pages
from manhwateca.notion_sync import statuses


def sync(
    notion,
    database_id,
    mangas,
    apply=False,
    title_aliases=None,
    create_limit=None,
    update_existing=True,
    print_actions=True,
    property_builder=build_properties,
    result_repository=None,
):
    existing = load_existing_pages(notion, database_id)
    title_aliases = title_aliases or {}
    summary = _new_summary(mangas, existing)
    for manga in sorted(mangas, key=lambda item: normalize_title(item["nome"])):
        _sync_manga(
            notion,
            database_id,
            manga,
            existing,
            title_aliases,
            summary,
            apply,
            create_limit,
            update_existing,
            print_actions,
            property_builder,
            result_repository,
        )
    return summary


def _new_summary(mangas, existing):
    page_ids = {
        page["id"] for page_list in existing.values() for page in page_list
    }
    return {
        "catalog_total": len(mangas),
        "existing": len(page_ids),
        "created": 0,
        "updated": 0,
        "pending": 0,
        "duplicates": 0,
        "matched_titles": [],
        "created_titles": [],
        "pending_titles": [],
        "duplicate_titles": [],
    }


def _sync_manga(
    notion,
    database_id,
    manga,
    existing,
    title_aliases,
    summary,
    apply,
    create_limit,
    update_existing,
    print_actions,
    property_builder,
    result_repository,
):
    name = manga["nome"].strip()
    matches = _find_matches(manga, existing, title_aliases)
    if len(matches) > 1:
        summary["duplicates"] += 1
        summary["duplicate_titles"].append(name)
        _mark_status(
            result_repository,
            manga,
            status=statuses.CONFLICT,
        )
        _record_event(
            result_repository,
            manga,
            event_type="duplicate",
            status=statuses.CONFLICT,
            message=f"{len(matches)} páginas encontradas no Notion",
        )
        if print_actions:
            print(f"[DUPLICADO] {name}: {len(matches)} páginas no Notion")
        return
    if matches:
        _update_match(
            notion, manga, name, matches[0], summary, apply,
            update_existing, print_actions, property_builder,
            result_repository
        )
        return
    _create_or_defer(
        notion, database_id, manga, name, summary, apply,
        create_limit, print_actions, result_repository
    )


def _find_matches(manga, existing, title_aliases):
    page_id = str(manga.get("notion_page_id") or "").strip()
    if page_id:
        page = _find_page_by_id(page_id, existing)
        if page:
            return [page]

    matches = {}
    for candidate in catalog_title_candidates(manga, title_aliases):
        for page in existing.get(candidate, []):
            matches[page["id"]] = page
    return list(matches.values())


def _find_page_by_id(page_id, existing):
    for pages in existing.values():
        for page in pages:
            if page.get("id") == page_id:
                return page
    return None


def _update_match(
    notion,
    manga,
    name,
    page,
    summary,
    apply,
    update_existing,
    print_actions,
    property_builder,
    result_repository,
):
    summary["matched_titles"].append(name)
    if not update_existing:
        _mark_status(
            result_repository,
            manga,
            status=statuses.SYNCED,
            page_id=page["id"],
        )
        _record_event(
            result_repository,
            manga,
            event_type="matched",
            status=statuses.SYNCED,
            page_id=page["id"],
            message="Página existente reconhecida sem atualização.",
        )
        return
    summary["updated"] += 1
    if print_actions:
        print(f"[ATUALIZAR] {name}")
    if apply:
        try:
            notion.pages.update(
                page_id=page["id"],
                properties=property_builder(manga),
            )
            _mark_synced(
                result_repository,
                manga,
                page_id=page["id"],
                event_type="update",
            )
        except Exception as error:
            _mark_error(
                result_repository,
                manga,
                page_id=page["id"],
                event_type="update",
                error=error,
            )
            raise
    else:
        _record_event(
            result_repository,
            manga,
            event_type="simulate_update",
            status=statuses.PENDING,
            page_id=page["id"],
        )


def _create_or_defer(
    notion,
    database_id,
    manga,
    name,
    summary,
    apply,
    create_limit,
    print_actions,
    result_repository,
):
    can_create = create_limit is None or summary["created"] < create_limit
    if not can_create:
        summary["pending"] += 1
        summary["pending_titles"].append(name)
        _mark_status(
            result_repository,
            manga,
            status=statuses.PENDING,
        )
        _record_event(
            result_repository,
            manga,
            event_type="defer_create",
            status=statuses.PENDING,
            message="Fora do limite do lote atual.",
        )
        return
    summary["created"] += 1
    summary["created_titles"].append(name)
    if print_actions:
        print(f"[CRIAR] {name}")
    if apply:
        try:
            page = notion.pages.create(
                parent={"database_id": database_id},
                properties=build_properties(manga),
            )
            _mark_synced(
                result_repository,
                manga,
                page_id=(page or {}).get("id"),
                event_type="create",
            )
        except Exception as error:
            _mark_error(
                result_repository,
                manga,
                event_type="create",
                error=error,
            )
            raise
    else:
        _record_event(
            result_repository,
            manga,
            event_type="simulate_create",
            status=statuses.PENDING,
        )


def _mark_synced(repository, manga, *, page_id=None, event_type):
    if repository is None:
        return
    _mark_status(
        repository,
        manga,
        page_id=page_id or manga.get("notion_page_id"),
        status=statuses.SYNCED,
    )
    _record_event(
        repository,
        manga,
        event_type=event_type,
        status=statuses.SYNCED,
        page_id=page_id or manga.get("notion_page_id"),
    )


def _mark_error(repository, manga, *, event_type, error, page_id=None):
    if repository is None:
        return
    _mark_status(
        repository,
        manga,
        page_id=page_id or manga.get("notion_page_id"),
        status=statuses.ERROR,
    )
    _record_event(
        repository,
        manga,
        event_type=event_type,
        status=statuses.ERROR,
        page_id=page_id or manga.get("notion_page_id"),
        message=str(error),
    )


def _mark_status(repository, manga, *, status, page_id=None):
    if repository is None:
        return
    repository.update_notion_sync_fields(
        manga["nome"].strip(),
        page_id=page_id or manga.get("notion_page_id"),
        status=status,
    )


def _record_event(
    repository,
    manga,
    *,
    event_type,
    status,
    page_id=None,
    message=None,
):
    if repository is None:
        return
    repository.record_sync_event(
        manga["nome"].strip(),
        event_type=event_type,
        status=status,
        page_id=page_id or manga.get("notion_page_id"),
        message=message,
        payload={"nome": manga.get("nome")},
    )

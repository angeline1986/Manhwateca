from manhwateca.notion_sync.catalog_properties import build_properties
from manhwateca.notion_sync.matching import (
    catalog_title_candidates,
    normalize_title,
)
from manhwateca.notion_sync.pages import load_existing_pages


def sync(
    notion,
    database_id,
    mangas,
    apply=False,
    title_aliases=None,
    create_limit=None,
    update_existing=True,
    print_actions=True,
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
):
    name = manga["nome"].strip()
    matches = _find_matches(manga, existing, title_aliases)
    if len(matches) > 1:
        summary["duplicates"] += 1
        summary["duplicate_titles"].append(name)
        if print_actions:
            print(f"[DUPLICADO] {name}: {len(matches)} páginas no Notion")
        return
    if matches:
        _update_match(
            notion, manga, name, matches[0], summary, apply,
            update_existing, print_actions
        )
        return
    _create_or_defer(
        notion, database_id, manga, name, summary, apply,
        create_limit, print_actions
    )


def _find_matches(manga, existing, title_aliases):
    matches = {}
    for candidate in catalog_title_candidates(manga, title_aliases):
        for page in existing.get(candidate, []):
            matches[page["id"]] = page
    return list(matches.values())


def _update_match(
    notion, manga, name, page, summary, apply, update_existing, print_actions
):
    summary["matched_titles"].append(name)
    if not update_existing:
        return
    summary["updated"] += 1
    if print_actions:
        print(f"[ATUALIZAR] {name}")
    if apply:
        notion.pages.update(
            page_id=page["id"],
            properties=build_properties(manga),
        )


def _create_or_defer(
    notion, database_id, manga, name, summary, apply, create_limit, print_actions
):
    can_create = create_limit is None or summary["created"] < create_limit
    if not can_create:
        summary["pending"] += 1
        summary["pending_titles"].append(name)
        return
    summary["created"] += 1
    summary["created_titles"].append(name)
    if print_actions:
        print(f"[CRIAR] {name}")
    if apply:
        notion.pages.create(
            parent={"database_id": database_id},
            properties=build_properties(manga),
        )

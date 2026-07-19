from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from manhwateca.database import MangaRepository
from manhwateca.notion_sync.csv_properties import (
    build_metadata_properties,
    split_values,
)
from manhwateca.notion_sync.matching import normalize_title
from manhwateca.notion_sync.pages import extract_title
from manhwateca.notion_sync.property_diff import changed_properties
from manhwateca.notion_sync.sync_plan import (
    NextAction,
    NotionBlocker,
    NotionSyncResult,
    SyncStatus,
    build_sync_result,
)


OFFICIAL_METADATA_PROPERTIES = {
    "Alias",
    "Cap MangaUpdates",
    "MangaUpdates",
    "ID da obra",
    "Temática",
    "Formato",
    "Universo",
}


@dataclass(frozen=True)
class NotionPageUpdatePlan:
    work_id: int
    work_title: str
    page_id: str
    expected_last_edited_time: str | None
    properties: dict


@dataclass(frozen=True)
class OfficialNotionSyncPlan:
    result: NotionSyncResult
    updates: tuple[NotionPageUpdatePlan, ...] = ()
    unchanged: tuple[NotionPageUpdatePlan, ...] = ()


def plan_official_metadata_sync(notion, database_id, repository=None):
    return OfficialNotionSyncPlanner(
        notion,
        database_id,
        repository=repository,
    ).plan_metadata_sync()


class OfficialNotionSyncPlanner:
    """Planeja o sync oficial PostgreSQL-first sem escrever no Notion."""

    def __init__(self, notion, database_id, repository=None):
        self.notion = notion
        self.database_id = database_id
        self.repository = repository or MangaRepository()
        self._pages_by_name = None

    def plan_metadata_sync(self):
        try:
            records = self.repository.list_mangas()
        except Exception as error:
            return _error_plan(error)
        return self._plan_records(records)

    def plan_metadata_sync_for_ids(self, work_ids):
        work_ids = _normalize_work_ids(work_ids)
        if not work_ids:
            return OfficialNotionSyncPlan(
                result=NotionSyncResult(
                    status=SyncStatus.SYNCED,
                    next_action=NextAction.NONE,
                )
            )
        try:
            records = self.repository.list_mangas_by_ids(work_ids)
        except Exception as error:
            return _error_plan(error)
        plan = self._plan_records(records)
        found_ids = {
            int(record.id) for record in records
            if getattr(record, "id", None) is not None
        }
        missing_ids = tuple(work_id for work_id in work_ids if work_id not in found_ids)
        if not missing_ids:
            return plan
        blockers = (
            *plan.result.blockers,
            *(
                NotionBlocker(
                    code="scope_work_missing",
                    work_id=work_id,
                    message="Obra do escopo incremental não encontrada no PostgreSQL.",
                    next_action=NextAction.REVIEW_BLOCKERS,
                )
                for work_id in missing_ids
            ),
        )
        return OfficialNotionSyncPlan(
            result=NotionSyncResult(
                status=SyncStatus.BLOCKED,
                next_action=NextAction.REVIEW_BLOCKERS,
                created_count=plan.result.created_count,
                updated_count=plan.result.updated_count,
                missing_count=plan.result.missing_count,
                duplicate_count=plan.result.duplicate_count,
                unchanged_count=plan.result.unchanged_count,
                blockers=blockers,
            ),
            updates=plan.updates,
            unchanged=plan.unchanged,
        )

    def _plan_records(self, records):
        summary = {
            "updates": [],
            "unchanged": [],
            "missing": [],
            "duplicates": [],
            "errors": [],
        }
        updates = []
        unchanged = []
        try:
            for record in records:
                self._plan_record(record, summary, updates, unchanged)
        except Exception as error:
            summary["errors"].append({"message": str(error)})
        return OfficialNotionSyncPlan(
            result=build_sync_result(summary),
            updates=tuple(updates),
            unchanged=tuple(unchanged),
        )

    def _plan_record(self, record, summary, updates, unchanged):
        page = self._find_page(record, summary)
        if page is None:
            return
        row = _record_to_sync_row(record)
        expected = _expected_metadata_properties(record, page)
        properties = changed_properties(page, expected)
        item = _summary_item(record, page)
        if not properties:
            summary["unchanged"].append(item)
            unchanged.append(_page_update_plan(record, page, {}))
            return
        item["properties"] = sorted(properties)
        summary["updates"].append(item)
        updates.append(_page_update_plan(record, page, properties))

    def _find_page(self, record, summary):
        if record.notion_page_id:
            return self._retrieve_page(record, summary)
        matches = self._matches_by_name(record, summary)
        if matches is None:
            return None
        if len(matches) == 1:
            return matches[0]
        if not matches:
            summary["missing"].append({
                "work_id": record.id,
                "work_title": record.title,
                "message": "Página não encontrada no Notion.",
            })
            return None
        summary["duplicates"].append({
            "work_id": record.id,
            "work_title": record.title,
            "message": "Mais de uma página corresponde à obra.",
        })
        return None

    def _retrieve_page(self, record, summary):
        try:
            return self.notion.pages.retrieve(page_id=record.notion_page_id)
        except Exception as error:
            summary["errors"].append({
                "work_id": record.id,
                "work_title": record.title,
                "message": str(error),
            })
            return None

    def _matches_by_name(self, record, summary):
        pages_by_name = self._load_pages_by_name(summary)
        if pages_by_name is None:
            return None
        matches = {}
        for candidate in _record_title_candidates(record):
            for page in pages_by_name.get(candidate, ()):
                matches[page["id"]] = page
        return tuple(matches.values())

    def _load_pages_by_name(self, summary):
        if self._pages_by_name is not None:
            return self._pages_by_name
        pages_by_name = {}
        cursor = None
        try:
            while True:
                request = {"database_id": self.database_id, "page_size": 100}
                if cursor:
                    request["start_cursor"] = cursor
                response = self.notion.databases.query(**request)
                for page in response.get("results", []):
                    title = extract_title(page)
                    if title:
                        pages_by_name.setdefault(
                            normalize_title(title),
                            [],
                        ).append(page)
                if not response.get("has_more"):
                    break
                cursor = response.get("next_cursor")
        except Exception as error:
            summary["errors"].append({"message": str(error)})
            return None
        self._pages_by_name = pages_by_name
        return self._pages_by_name


def _record_title_candidates(record):
    names = [record.title, *split_values(record.alternative_title)]
    return {
        normalize_title(name)
        for name in names
        if str(name or "").strip()
    }


def _error_plan(error):
    return OfficialNotionSyncPlan(
        result=build_sync_result({"errors": [{"message": str(error)}]})
    )


def _normalize_work_ids(values):
    if not values:
        return []
    ordered = []
    seen = set()
    for value in values:
        try:
            work_id = int(value)
        except (TypeError, ValueError):
            continue
        if work_id <= 0 or work_id in seen:
            continue
        ordered.append(work_id)
        seen.add(work_id)
    return ordered


def _record_to_sync_row(record):
    return {
        "ID da obra": _text(record.work_code),
        "Nome": _text(record.title),
        "Alias": _text(record.alternative_title),
        "Capítulo MangaUpdates": _text(record.latest_mangaupdates_chapter),
        "MangaUpdates": _text(record.mangaupdates_url),
        "Temática": "|".join(record.themes or []),
        "Formato": _text(record.format),
        "Universo": "",
    }


def _expected_metadata_properties(record, page):
    expected = build_metadata_properties(_record_to_sync_row(record))
    expected = {
        name: value
        for name, value in expected.items()
        if name in OFFICIAL_METADATA_PROPERTIES
    }
    _merge_alias_property(expected, record, page)
    return expected


def _merge_alias_property(expected, record, page):
    aliases = _merged_aliases(
        _current_aliases(page),
        split_values(record.alternative_title),
    )
    if aliases:
        expected["Alias"] = {
            "rich_text": [{"text": {"content": ", ".join(aliases)}}]
        }
    else:
        expected.pop("Alias", None)


def _current_aliases(page):
    value = page.get("properties", {}).get("Alias", {})
    if value.get("type") != "rich_text":
        return []
    text = "".join(
        item.get("plain_text")
        or item.get("text", {}).get("content", "")
        for item in value.get("rich_text", [])
    )
    return _split_aliases(text)


def _split_aliases(value):
    return [
        item.strip()
        for chunk in str(value or "").split("|")
        for item in chunk.split(",")
        if item.strip()
    ]


def _merged_aliases(existing, local):
    aliases = []
    seen = set()
    for alias in [*existing, *local]:
        normalized = normalize_title(alias)
        if not normalized or normalized in seen:
            continue
        aliases.append(alias.strip())
        seen.add(normalized)
    return aliases


def _summary_item(record, page):
    return {
        "work_id": record.id,
        "work_title": record.title,
        "page_id": page.get("id"),
    }


def _page_update_plan(record, page, properties):
    return NotionPageUpdatePlan(
        work_id=record.id,
        work_title=record.title,
        page_id=page.get("id"),
        expected_last_edited_time=page.get("last_edited_time"),
        properties=properties,
    )


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return str(int(value)) if value == value.to_integral() else str(value)
    return str(value)

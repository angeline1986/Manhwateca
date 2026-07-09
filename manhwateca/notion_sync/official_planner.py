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
from manhwateca.notion_sync.sync_plan import build_sync_result


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
        summary = {
            "updates": [],
            "unchanged": [],
            "missing": [],
            "duplicates": [],
            "errors": [],
        }
        try:
            records = self.repository.list_mangas()
            for record in records:
                self._plan_record(record, summary)
        except Exception as error:
            summary["errors"].append({"message": str(error)})
        return build_sync_result(summary)

    def _plan_record(self, record, summary):
        page = self._find_page(record, summary)
        if page is None:
            return
        row = _record_to_sync_row(record)
        expected = build_metadata_properties(row)
        properties = changed_properties(page, expected)
        item = _summary_item(record, page)
        if not properties:
            summary["unchanged"].append(item)
            return
        item["properties"] = sorted(properties)
        summary["updates"].append(item)

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
        "Picância": _text(record.spice_level),
        "Interesse": _text(record.personal_rank),
    }


def _summary_item(record, page):
    return {
        "work_id": record.id,
        "work_title": record.title,
        "page_id": page.get("id"),
    }


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return str(int(value)) if value == value.to_integral() else str(value)
    return str(value)

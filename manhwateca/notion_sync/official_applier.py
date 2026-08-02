from dataclasses import dataclass
from datetime import datetime

from manhwateca.notion_sync import statuses
from manhwateca.notion_sync.official_planner import (
    OFFICIAL_METADATA_PROPERTIES,
    OfficialNotionSyncPlan,
    official_metadata_properties,
)
from manhwateca.notion_sync.property_diff import changed_properties
from manhwateca.notion_sync.sync_plan import (
    BlockerSeverity,
    NextAction,
    NotionBlocker,
    SyncStatus,
)


@dataclass(frozen=True)
class NotionApplyResult:
    status: SyncStatus
    next_action: NextAction
    applied_count: int = 0
    unchanged_count: int = 0
    failed_count: int = 0
    blockers: tuple[NotionBlocker, ...] = ()


class OfficialNotionSyncApplier:
    def __init__(self, notion, repository):
        self.notion = notion
        self.repository = repository

    def apply(self, plan: OfficialNotionSyncPlan) -> NotionApplyResult:
        blockers = _blocking_blockers(plan)
        if blockers:
            return NotionApplyResult(
                status=SyncStatus.BLOCKED,
                next_action=plan.result.next_action,
                unchanged_count=len(plan.unchanged),
                blockers=blockers,
            )

        property_blockers = _property_blockers(plan)
        if property_blockers:
            return NotionApplyResult(
                status=SyncStatus.BLOCKED,
                next_action=NextAction.REVIEW_BLOCKERS,
                unchanged_count=len(plan.unchanged),
                blockers=property_blockers,
            )

        stale_blockers = self._prevalidate(plan)
        if stale_blockers:
            return NotionApplyResult(
                status=SyncStatus.BLOCKED,
                next_action=NextAction.REVIEW_BLOCKERS,
                unchanged_count=len(plan.unchanged),
                blockers=stale_blockers,
            )

        applied = 0
        for item in plan.updates:
            try:
                self.notion.pages.update(
                    page_id=item.page_id,
                    properties=item.properties,
                )
            except Exception as error:
                blocker = NotionBlocker(
                    code="api_error",
                    work_id=item.work_id,
                    work_title=item.work_title,
                    message=str(error),
                    next_action=NextAction.RETRY,
                )
                self._record_error(item, blocker)
                return NotionApplyResult(
                    status=SyncStatus.ERROR,
                    next_action=NextAction.RETRY,
                    applied_count=applied,
                    unchanged_count=len(plan.unchanged),
                    failed_count=1,
                    blockers=(blocker,),
                )
            try:
                synced_at = datetime.now().astimezone()
                self.repository.update_notion_sync_fields_by_id(
                    item.work_id,
                    page_id=item.page_id,
                    status=statuses.SYNCED,
                    synced_at=synced_at,
                )
                self.repository.record_sync_event_by_id(
                    item.work_id,
                    event_type="notion_metadata_sync",
                    status=statuses.SYNCED,
                    page_id=item.page_id,
                    message="Metadados sincronizados no Notion.",
                    payload={
                        "properties": sorted(item.properties),
                        "code": "notion_metadata_synced",
                    },
                )
                applied += 1
            except Exception as error:
                blocker = NotionBlocker(
                    code="local_persistence_error",
                    work_id=item.work_id,
                    work_title=item.work_title,
                    message=str(error),
                    next_action=NextAction.RETRY,
                )
                self._record_error(item, blocker)
                return NotionApplyResult(
                    status=SyncStatus.ERROR,
                    next_action=NextAction.RETRY,
                    applied_count=applied + 1,
                    unchanged_count=len(plan.unchanged),
                    failed_count=1,
                    blockers=(blocker,),
                )

        return NotionApplyResult(
            status=SyncStatus.SYNCED,
            next_action=NextAction.NONE,
            applied_count=applied,
            unchanged_count=len(plan.unchanged),
        )

    def create_missing_page(self, record, database_id) -> NotionApplyResult:
        properties = _create_page_properties(record)
        property_blockers = _unsafe_property_blockers(
            record.id,
            record.title,
            properties,
            extra_allowed={"Nome"},
        )
        if property_blockers:
            return NotionApplyResult(
                status=SyncStatus.BLOCKED,
                next_action=NextAction.REVIEW_BLOCKERS,
                blockers=property_blockers,
            )
        try:
            page = self.notion.pages.create(
                parent={"database_id": database_id},
                properties=properties,
            )
        except Exception as error:
            return NotionApplyResult(
                status=SyncStatus.ERROR,
                next_action=NextAction.RETRY,
                failed_count=1,
                blockers=(
                    NotionBlocker(
                        code="api_error",
                        work_id=record.id,
                        work_title=record.title,
                        message=str(error),
                        next_action=NextAction.RETRY,
                    ),
                ),
            )
        page_id = page.get("id")
        try:
            synced_at = datetime.now().astimezone()
            self.repository.update_notion_sync_fields_by_id(
                record.id,
                page_id=page_id,
                status=statuses.SYNCED,
                synced_at=synced_at,
            )
            self.repository.record_sync_event_by_id(
                record.id,
                event_type="notion_metadata_sync",
                status=statuses.SYNCED,
                page_id=page_id,
                message="Página criada e metadados sincronizados no Notion.",
                payload={
                    "properties": sorted(properties),
                    "code": "notion_metadata_page_created",
                },
            )
        except Exception as error:
            return NotionApplyResult(
                status=SyncStatus.ERROR,
                next_action=NextAction.RETRY,
                applied_count=1,
                failed_count=1,
                blockers=(
                    NotionBlocker(
                        code="local_persistence_error",
                        work_id=record.id,
                        work_title=record.title,
                        message=str(error),
                        next_action=NextAction.RETRY,
                    ),
                ),
            )
        return NotionApplyResult(
            status=SyncStatus.SYNCED,
            next_action=NextAction.NONE,
            applied_count=1,
        )

    def _prevalidate(self, plan):
        blockers = []
        for item in plan.updates:
            try:
                page = self.notion.pages.retrieve(page_id=item.page_id)
            except Exception as error:
                blockers.append(_api_blocker(item, error))
                continue
            if page.get("last_edited_time") != item.expected_last_edited_time:
                blockers.append(_stale_blocker(item))
                continue
            current = changed_properties(page, item.properties)
            if current != item.properties:
                blockers.append(_stale_blocker(item))
        return tuple(blockers)

    def _record_error(self, item, blocker):
        try:
            self.repository.update_notion_sync_fields_by_id(
                item.work_id,
                page_id=item.page_id,
                status=statuses.ERROR,
                synced_at=None,
            )
            self.repository.record_sync_event_by_id(
                item.work_id,
                event_type="notion_metadata_sync",
                status=statuses.ERROR,
                page_id=item.page_id,
                message=blocker.message,
                payload={"code": blocker.code},
            )
        except Exception:
            pass


def _blocking_blockers(plan):
    return tuple(
        blocker
        for blocker in plan.result.blockers
        if blocker.severity == BlockerSeverity.BLOCKING
    )


def _property_blockers(plan):
    blockers = []
    for item in plan.updates:
        blockers.extend(_unsafe_property_blockers(
            item.work_id,
            item.work_title,
            item.properties,
        ))
    return tuple(blockers)


def _unsafe_property_blockers(work_id, work_title, properties, *, extra_allowed=None):
    allowed = set(OFFICIAL_METADATA_PROPERTIES)
    allowed.update(extra_allowed or set())
    forbidden = sorted(set(properties) - allowed)
    if not forbidden:
        return []
    return [
        NotionBlocker(
            code="unsafe_property",
            work_id=work_id,
            work_title=work_title,
            message=", ".join(forbidden),
        )
    ]


def _create_page_properties(record):
    return {
        "Nome": {"title": [{"text": {"content": record.title}}]},
        **official_metadata_properties(record),
    }


def _stale_blocker(item):
    return NotionBlocker(
        code="stale_notion_page",
        work_id=item.work_id,
        work_title=item.work_title,
        message="A página foi alterada depois do planejamento.",
        next_action=NextAction.REVIEW_BLOCKERS,
    )


def _api_blocker(item, error):
    return NotionBlocker(
        code="api_error",
        work_id=item.work_id,
        work_title=item.work_title,
        message=str(error),
        next_action=NextAction.RETRY,
    )

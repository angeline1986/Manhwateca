from dataclasses import dataclass
from datetime import datetime

from manhwateca.notion_sync import statuses
from manhwateca.notion_sync.official_planner import (
    OFFICIAL_METADATA_PROPERTIES,
    OfficialNotionSyncPlan,
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
        forbidden = sorted(set(item.properties) - OFFICIAL_METADATA_PROPERTIES)
        if forbidden:
            blockers.append(
                NotionBlocker(
                    code="unsafe_property",
                    work_id=item.work_id,
                    work_title=item.work_title,
                    message=", ".join(forbidden),
                )
            )
    return tuple(blockers)


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

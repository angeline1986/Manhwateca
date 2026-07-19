import unittest
from types import SimpleNamespace

from manhwateca.notion_sync.flow_integration import OfficialNotionFlowIntegration
from manhwateca.notion_sync.official_applier import NotionApplyResult
from manhwateca.notion_sync.official_planner import (
    NotionPageUpdatePlan,
    OfficialNotionSyncPlan,
)
from manhwateca.notion_sync.sync_plan import (
    NextAction,
    NotionBlocker,
    NotionSyncResult,
    SyncStatus,
)


class OfficialNotionFlowIntegrationTests(unittest.TestCase):
    def test_blocked_plan_does_not_call_applier(self):
        blocker = NotionBlocker(
            code="missing_page",
            work_id=258,
            work_title="Boredom",
            next_action=NextAction.REVIEW_MISSING,
        )
        plan = OfficialNotionSyncPlan(
            result=NotionSyncResult(
                status=SyncStatus.BLOCKED,
                next_action=NextAction.REVIEW_MISSING,
                missing_count=1,
                blockers=(blocker,),
            )
        )
        applier = FakeApplier()

        result = integration(plan=plan, applier=applier).sync_page(work_ids=[1])

        self.assertEqual(0, applier.calls)
        self.assertEqual(0, result.updated)
        self.assertEqual(1, result.skipped)
        self.assertEqual(0, result.failed)
        self.assertEqual("blocked", result.metrics["status"])
        self.assertEqual("review_missing", result.metrics["next_action"])
        self.assertEqual(1, result.metrics["missing_count"])
        self.assertEqual(1, result.metrics["blocker_count"])
        self.assertEqual("missing_page", result.metrics["blockers"][0]["code"])

    def test_without_scope_blocks_without_planning(self):
        planner = FakePlanner(synced_plan())
        applier = FakeApplier()

        result = OfficialNotionFlowIntegration(
            object(),
            "database_id",
            repository=object(),
            planner=planner,
            applier=applier,
        ).sync_page()

        self.assertEqual(0, planner.calls)
        self.assertEqual(0, planner.scoped_calls)
        self.assertEqual(0, applier.calls)
        self.assertEqual("blocked", result.metrics["status"])
        self.assertTrue(result.metrics["scope_missing"])

    def test_invalid_scope_blocks_before_planner(self):
        planner = FakePlanner(synced_plan())
        applier = FakeApplier()

        result = OfficialNotionFlowIntegration(
            object(),
            "database_id",
            repository=FakeRepository([]),
            planner=planner,
            applier=applier,
        ).sync_page(work_ids=[259])

        self.assertEqual(0, planner.calls)
        self.assertEqual(0, planner.scoped_calls)
        self.assertEqual(0, applier.calls)
        self.assertEqual("blocked", result.metrics["status"])
        self.assertEqual("scope_work_missing", result.metrics["blockers"][0]["code"])

    def test_not_eligible_scope_blocks_before_planner(self):
        planner = FakePlanner(synced_plan())
        applier = FakeApplier()

        result = OfficialNotionFlowIntegration(
            object(),
            "database_id",
            repository=FakeRepository([
                SimpleNamespace(id=259, title="Dressed_to_Kill", work_code=None)
            ]),
            planner=planner,
            applier=applier,
        ).sync_page(work_ids=[259])

        self.assertEqual(0, planner.scoped_calls)
        self.assertEqual(0, applier.calls)
        self.assertEqual("blocked", result.metrics["status"])
        self.assertEqual("scope_work_not_eligible", result.metrics["blockers"][0]["code"])

    def test_planning_error_does_not_call_applier(self):
        blocker = NotionBlocker(
            code="api_error",
            message="Rate limit",
            next_action=NextAction.RETRY,
        )
        plan = OfficialNotionSyncPlan(
            result=NotionSyncResult(
                status=SyncStatus.ERROR,
                next_action=NextAction.RETRY,
                blockers=(blocker,),
            )
        )
        applier = FakeApplier()

        result = integration(plan=plan, applier=applier).sync_page(work_ids=[1])

        self.assertEqual(0, applier.calls)
        self.assertEqual(0, result.updated)
        self.assertEqual(1, result.failed)
        self.assertEqual("error", result.metrics["status"])
        self.assertEqual(0, result.metrics["applied_count"])
        self.assertEqual(1, result.metrics["failed_count"])
        self.assertEqual("Rate limit", result.metrics["blockers"][0]["message"])

    def test_synced_plan_without_updates_reports_no_changes(self):
        plan = OfficialNotionSyncPlan(
            result=NotionSyncResult(
                status=SyncStatus.SYNCED,
                next_action=NextAction.NONE,
                unchanged_count=2,
            ),
            unchanged=(update_plan(work_id=1), update_plan(work_id=2),),
        )
        applier = FakeApplier()

        result = integration(plan=plan, applier=applier).sync_page(work_ids=[1])

        self.assertEqual(0, applier.calls)
        self.assertEqual(0, result.updated)
        self.assertEqual(0, result.failed)
        self.assertEqual("synced", result.metrics["status"])
        self.assertEqual(2, result.metrics["unchanged_count"])
        self.assertEqual("Nenhuma alteração técnica necessária no Notion.", result.metrics["message"])

    def test_safe_plan_calls_applier_and_maps_success(self):
        plan = OfficialNotionSyncPlan(
            result=NotionSyncResult(
                status=SyncStatus.PAUSED,
                next_action=NextAction.APPLY,
                updated_count=1,
                unchanged_count=1,
            ),
            updates=(update_plan(work_id=4),),
            unchanged=(update_plan(work_id=1),),
        )
        applier = FakeApplier(
            NotionApplyResult(
                status=SyncStatus.SYNCED,
                next_action=NextAction.NONE,
                applied_count=1,
                unchanged_count=1,
            )
        )

        result = integration(plan=plan, applier=applier).sync_page(work_ids=[1])

        self.assertEqual(1, applier.calls)
        self.assertIs(plan, applier.last_plan)
        self.assertEqual(1, result.updated)
        self.assertEqual(0, result.failed)
        self.assertEqual("synced", result.metrics["status"])
        self.assertEqual(1, result.metrics["applied_count"])
        self.assertEqual(1, result.metrics["unchanged_count"])
        self.assertEqual("1 obra(s) atualizada(s) no Notion.", result.metrics["message"])

    def test_applier_partial_error_is_preserved(self):
        blocker = NotionBlocker(
            code="api_error",
            work_id=9,
            message="Timeout",
            next_action=NextAction.RETRY,
        )
        plan = OfficialNotionSyncPlan(
            result=NotionSyncResult(
                status=SyncStatus.PAUSED,
                next_action=NextAction.APPLY,
                updated_count=2,
            ),
            updates=(update_plan(work_id=4), update_plan(work_id=9),),
        )
        applier = FakeApplier(
            NotionApplyResult(
                status=SyncStatus.ERROR,
                next_action=NextAction.RETRY,
                applied_count=1,
                failed_count=1,
                blockers=(blocker,),
            )
        )

        result = integration(plan=plan, applier=applier).sync_page(work_ids=[1])

        self.assertEqual(1, applier.calls)
        self.assertEqual(1, result.updated)
        self.assertEqual(1, result.failed)
        self.assertEqual("error", result.metrics["status"])
        self.assertTrue(result.metrics["partial"])
        self.assertEqual(1, result.metrics["applied_count"])
        self.assertEqual("Timeout", result.metrics["blockers"][0]["message"])

    def test_validate_does_not_expose_sensitive_values(self):
        result = OfficialNotionFlowIntegration(
            None,
            None,
            repository=object(),
            planner=FakePlanner(synced_plan()),
            applier=FakeApplier(),
        ).check_status()

        self.assertFalse(result.available)
        self.assertEqual("Integração com Notion indisponível.", result.message)
        self.assertNotIn("secret", str(result))


class FakePlanner:
    def __init__(self, plan):
        self.plan = plan
        self.calls = 0
        self.scoped_calls = 0
        self.last_work_ids = None

    def plan_metadata_sync(self):
        self.calls += 1
        return self.plan

    def plan_metadata_sync_for_ids(self, work_ids):
        self.scoped_calls += 1
        self.last_work_ids = work_ids
        return self.plan


class FakeApplier:
    def __init__(self, result=None):
        self.result = result
        self.calls = 0
        self.last_plan = None

    def apply(self, plan):
        self.calls += 1
        self.last_plan = plan
        return self.result or NotionApplyResult(
            status=SyncStatus.SYNCED,
            next_action=NextAction.NONE,
        )


class FakeRepository:
    def __init__(self, records):
        self.records = records
        self.list_by_ids_calls = []

    def list_mangas_by_ids(self, work_ids):
        self.list_by_ids_calls.append(list(work_ids))
        wanted = {int(work_id) for work_id in work_ids}
        return [record for record in self.records if int(record.id) in wanted]


def integration(plan, applier=None):
    return OfficialNotionFlowIntegration(
        object(),
        "database_id",
        repository=object(),
        planner=FakePlanner(plan),
        applier=applier or FakeApplier(),
    )


def synced_plan():
    return OfficialNotionSyncPlan(
        result=NotionSyncResult(
            status=SyncStatus.SYNCED,
            next_action=NextAction.NONE,
        )
    )


def update_plan(work_id=4):
    return NotionPageUpdatePlan(
        work_id=work_id,
        work_title=f"Obra {work_id}",
        page_id=f"page-{work_id}",
        expected_last_edited_time="2026-06-18T21:32:00.000Z",
        properties={"Alias": {"rich_text": []}},
    )


if __name__ == "__main__":
    unittest.main()

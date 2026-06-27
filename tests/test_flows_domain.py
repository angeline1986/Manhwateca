import unittest

from manhwateca.flows.domain import (
    OFFICIAL_STAGE_DEFINITIONS,
    FlowWarning,
    Progress,
    StageExecution,
    StageId,
    StageResult,
    StageStatus,
    WorkflowExecution,
    WorkflowStatus,
    official_stage_ids,
)


class FlowsDomainTests(unittest.TestCase):
    def test_official_stage_order_matches_documentation(self):
        self.assertEqual(
            (
                StageId.ORGANIZE_LIBRARY,
                StageId.CATALOG_WORKS,
                StageId.RESOLVE_IDS,
                StageId.UPDATE_METADATA,
                StageId.SYNC_NOTION,
            ),
            official_stage_ids(),
        )
        self.assertEqual(
            [1, 2, 3, 4, 5],
            [stage.order for stage in OFFICIAL_STAGE_DEFINITIONS],
        )

    def test_stage_dependencies_follow_fixed_sequence(self):
        dependencies = {
            stage.id: stage.depends_on
            for stage in OFFICIAL_STAGE_DEFINITIONS
        }
        self.assertIsNone(dependencies[StageId.ORGANIZE_LIBRARY])
        self.assertEqual(
            StageId.ORGANIZE_LIBRARY,
            dependencies[StageId.CATALOG_WORKS],
        )
        self.assertEqual(StageId.CATALOG_WORKS, dependencies[StageId.RESOLVE_IDS])
        self.assertEqual(StageId.RESOLVE_IDS, dependencies[StageId.UPDATE_METADATA])
        self.assertEqual(StageId.UPDATE_METADATA, dependencies[StageId.SYNC_NOTION])

    def test_domain_uses_only_documented_statuses(self):
        self.assertEqual(
            {
                "idle",
                "validating",
                "running",
                "cancelling",
                "cancelled",
                "completed",
                "completed_with_warnings",
                "failed",
            },
            {status.value for status in WorkflowStatus},
        )
        self.assertEqual(
            {
                "waiting",
                "validating",
                "running",
                "completed",
                "completed_with_warnings",
                "skipped",
                "failed",
                "cancelled",
            },
            {status.value for status in StageStatus},
        )

    def test_progress_percent_is_bounded(self):
        self.assertEqual(0, Progress(current=0, total=0).percent)
        self.assertEqual(50, Progress(current=1, total=2).percent)
        self.assertEqual(100, Progress(current=3, total=2).percent)
        self.assertEqual(0, Progress(current=-1, total=2).percent)

    def test_workflow_progress_counts_finished_stages(self):
        execution = WorkflowExecution(
            status=WorkflowStatus.RUNNING,
            stages=(
                StageExecution(
                    StageId.ORGANIZE_LIBRARY,
                    status=StageStatus.COMPLETED,
                ),
                StageExecution(
                    StageId.CATALOG_WORKS,
                    status=StageStatus.COMPLETED_WITH_WARNINGS,
                ),
                StageExecution(
                    StageId.RESOLVE_IDS,
                    status=StageStatus.RUNNING,
                ),
            ),
        )

        self.assertEqual(2, execution.progress.current)
        self.assertEqual(3, execution.progress.total)
        self.assertEqual(67, execution.progress.percent)
        self.assertEqual(StageId.RESOLVE_IDS, execution.current_stage.stage_id)

    def test_warning_result_marks_workflow_with_warnings(self):
        execution = WorkflowExecution(
            stages=(
                StageExecution(
                    StageId.ORGANIZE_LIBRARY,
                    status=StageStatus.COMPLETED_WITH_WARNINGS,
                    result=StageResult(
                        warnings=(FlowWarning("Pendências registradas."),)
                    ),
                ),
            ),
        )

        self.assertTrue(execution.has_warnings)
        self.assertFalse(execution.has_errors)


if __name__ == "__main__":
    unittest.main()

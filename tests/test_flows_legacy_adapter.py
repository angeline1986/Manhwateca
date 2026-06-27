import unittest

from manhwateca.flows.domain import StageId, StageStatus, WorkflowStatus
from manhwateca.flows.legacy_adapter import LegacyWorkflowAdapter


class LegacyWorkflowAdapterTests(unittest.TestCase):
    def test_status_maps_legacy_manual_state_to_documented_warning(self):
        adapter = LegacyWorkflowAdapter(
            ".",
            manager=FakeManager({
                "run": {
                    "status": "waiting_manual",
                    "started_at": "2026-06-27T10:00:00-03:00",
                    "finished_at": "2026-06-27T10:01:00-03:00",
                    "notification": "Revise pendências.",
                    "results": {
                        "previews": {"status": "completed", "messages": []},
                        "organize": {
                            "status": "manual",
                            "messages": [],
                            "note": "Revise pendências.",
                        },
                    },
                }
            }),
        )

        execution = adapter.status()

        self.assertEqual(
            WorkflowStatus.COMPLETED_WITH_WARNINGS,
            execution.status,
        )
        self.assertEqual(
            StageStatus.COMPLETED_WITH_WARNINGS,
            execution.stages[0].status,
        )
        self.assertEqual("Revise pendências.", execution.warnings[0].message)

    def test_start_stage_selects_only_mapped_legacy_steps(self):
        manager = FakeManager({"run": {"status": "idle", "results": {}}})
        adapter = LegacyWorkflowAdapter(".", manager=manager)

        adapter.start(StageId.RESOLVE_IDS)

        self.assertEqual(["ids", "review_ids"], manager.selected)

    def test_legacy_failures_map_to_documented_failed_state(self):
        adapter = LegacyWorkflowAdapter(
            ".",
            manager=FakeManager({
                "run": {
                    "status": "interrupted",
                    "notification": "Execução anterior interrompida.",
                    "results": {
                        "details": {
                            "status": "interrupted",
                            "messages": [],
                        },
                    },
                }
            }),
        )

        execution = adapter.status()

        self.assertEqual(WorkflowStatus.FAILED, execution.status)
        metadata = [
            stage for stage in execution.stages
            if stage.stage_id == StageId.UPDATE_METADATA
        ][0]
        self.assertEqual(StageStatus.FAILED, metadata.status)
        self.assertTrue(execution.has_errors)


class FakeManager:
    def __init__(self, payload):
        self.payload = {
            "steps": [],
            **payload,
        }
        self.selected = None

    def status(self):
        return self.payload

    def start(self, selected=None):
        self.selected = selected
        return self.payload


if __name__ == "__main__":
    unittest.main()

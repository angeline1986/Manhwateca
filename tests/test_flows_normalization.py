import tempfile
import unittest
from pathlib import Path

from manhwateca.flows.domain import WorkflowExecution, WorkflowStatus
from manhwateca.flows.integrations import FileNormalizationPlan
from manhwateca.flows.normalization import (
    FileNormalizationService,
    LocalFileNormalizationIntegration,
)


class LocalFileNormalizationIntegrationTests(unittest.TestCase):
    def test_preview_detects_file_renames_without_changing_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "N" / "Nice to See You"
            work.mkdir(parents=True)
            source = work / "Nice to See You capítulo 01=07.pdf"
            source.write_text("pdf", encoding="utf-8")

            plan = LocalFileNormalizationIntegration(root).generate_preview("wf_1")

            self.assertEqual("ready", plan.status)
            self.assertEqual({"rename_file", "move_folder"}, {
                item.operation for item in plan.items
            })
            file_item = _item(plan, "rename_file")
            self.assertEqual("ready", file_item.status)
            self.assertTrue(source.exists())
            self.assertFalse((work / "Nice to See You cap 1-7.pdf").exists())

    def test_apply_renames_file_from_persisted_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "N" / "Nice to See You"
            work.mkdir(parents=True)
            source = work / "Nice to See You capítulo 01=07.pdf"
            source.write_text("pdf", encoding="utf-8")
            integration = LocalFileNormalizationIntegration(root)
            plan = integration.generate_preview("wf_1")

            applied = integration.apply_plan(plan)

            self.assertEqual("applied", applied.status)
            self.assertFalse(source.exists())
            renamed = next(root.rglob("Nice to See You cap 1-7.pdf"), None)
            self.assertIsNotNone(renamed)
            self.assertEqual("applied", _item(applied, "rename_file").status)

    def test_apply_blocks_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "N" / "Nice to See You"
            work.mkdir(parents=True)
            source = work / "Nice to See You capítulo 01=07.pdf"
            destination = work / "Nice to See You cap 1-7.pdf"
            source.write_text("pdf", encoding="utf-8")
            destination.write_text("existing", encoding="utf-8")

            plan = LocalFileNormalizationIntegration(root).generate_preview("wf_1")

            self.assertEqual("blocked", plan.status)
            self.assertEqual("conflict", plan.items[0].status)
            self.assertTrue(source.exists())
            self.assertEqual("existing", destination.read_text(encoding="utf-8"))


class FileNormalizationServiceTests(unittest.TestCase):
    def test_preview_and_apply_use_repository_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "N" / "Nice to See You"
            work.mkdir(parents=True)
            (work / "Nice to See You capítulo 01=07.pdf").write_text(
                "pdf",
                encoding="utf-8",
            )
            repository = FakeRepository()
            service = FileNormalizationService(
                repository,
                LocalFileNormalizationIntegration(root),
            )

            preview = service.generate_preview()
            applied = service.apply_latest()

            self.assertEqual("wf_1", preview.execution_id)
            self.assertEqual("applied", applied.status)
            self.assertEqual(["save", "update"], repository.calls)


class FakeRepository:
    def __init__(self):
        self.calls = []
        self.plan = None

    def latest_execution(self):
        return WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.COMPLETED_WITH_WARNINGS,
        )

    def save_normalization_plan(self, plan):
        self.calls.append("save")
        saved_items = tuple(
            type(item)(**{**item.__dict__, "item_id": index})
            for index, item in enumerate(plan.items, start=1)
        )
        self.plan = FileNormalizationPlan(
            execution_id=plan.execution_id,
            status=plan.status,
            items=saved_items,
            plan_id=1,
            total_conflicts=plan.total_conflicts,
            total_errors=plan.total_errors,
            error_message=plan.error_message,
        )
        return self.plan

    def latest_normalization_plan(self):
        return self.plan

    def update_normalization_plan(self, plan):
        self.calls.append("update")
        self.plan = plan
        return plan


def _item(plan, operation):
    return next(item for item in plan.items if item.operation == operation)


if __name__ == "__main__":
    unittest.main()

import unittest

from manhwateca.flows.domain import (
    FlowMessage,
    FlowWarning,
    Progress,
    StageExecution,
    StageId,
    StageResult,
    StageStatus,
    WorkflowExecution,
    WorkflowStatus,
)
from manhwateca.flows.repository import FlowLogRecord, FlowRepository
from manhwateca.flows.integrations import (
    FileNormalizationItem,
    FileNormalizationPlan,
    LibraryInventoryItem,
)


class FlowRepositoryTests(unittest.TestCase):
    def test_save_execution_persists_workflow_stage_and_messages(self):
        connection = FakeConnection()
        repository = FlowRepository(connection)
        execution = WorkflowExecution(
            execution_id="wf_1",
            status=WorkflowStatus.RUNNING,
            started_at="2026-06-27T10:00:00-03:00",
            stages=(
                StageExecution(
                    StageId.ORGANIZE_LIBRARY,
                    status=StageStatus.COMPLETED_WITH_WARNINGS,
                    progress=Progress(current=8, total=10),
                    started_at="2026-06-27T10:01:00-03:00",
                    finished_at="2026-06-27T10:02:00-03:00",
                    result=StageResult(
                        processed=8,
                        skipped=2,
                        warnings=(FlowWarning("Pendência registrada."),),
                        metrics={"works": 10},
                    ),
                    messages=(FlowMessage("Biblioteca validada."),),
                ),
            ),
        )

        repository.save_execution(execution)

        self.assertTrue(connection.committed)
        self.assertIn("wf_1", connection.executions)
        self.assertEqual("running", connection.executions["wf_1"]["status"])
        self.assertEqual(1, len(connection.stages))
        self.assertEqual("organize_library", connection.stages[0]["stage"])
        self.assertEqual("completed_with_warnings", connection.stages[0]["status"])
        self.assertEqual(2, len(connection.messages))
        self.assertEqual(
            {"info", "warning"},
            {message["severity"] for message in connection.messages},
        )

    def test_load_execution_rebuilds_domain_model(self):
        connection = FakeConnection()
        connection.executions["wf_1"] = {
            "execution_id": "wf_1",
            "status": "completed",
            "started_at": "2026-06-27T10:00:00-03:00",
            "finished_at": "2026-06-27T10:05:00-03:00",
        }
        connection.stages.append({
            "execution_id": "wf_1",
            "stage": "catalog_works",
            "status": "completed",
            "progress_current": 1,
            "progress_total": 1,
            "elapsed_seconds": 10,
            "estimated_remaining_seconds": None,
            "current_item": None,
            "started_at": "2026-06-27T10:01:00-03:00",
            "finished_at": "2026-06-27T10:02:00-03:00",
            "processed": 3,
            "skipped": 0,
            "metrics": {"created": 3},
        })
        connection.messages.append({
            "execution_id": "wf_1",
            "stage": "catalog_works",
            "severity": "info",
            "code": None,
            "message": "Catalogação concluída.",
            "details": {},
        })

        execution = FlowRepository(connection).load_execution("wf_1")

        self.assertEqual(WorkflowStatus.COMPLETED, execution.status)
        self.assertEqual(StageId.CATALOG_WORKS, execution.stages[0].stage_id)
        self.assertEqual(3, execution.stages[0].result.processed)
        self.assertEqual({"created": 3}, execution.stages[0].result.metrics)
        self.assertEqual("2026-06-27T10:01:00-03:00", execution.stages[0].started_at)
        self.assertEqual("2026-06-27T10:02:00-03:00", execution.stages[0].finished_at)

    def test_append_log_and_summary_use_database_tables(self):
        connection = FakeConnection()
        repository = FlowRepository(connection)

        repository.append_log(FlowLogRecord(
            execution_id="wf_1",
            stage=StageId.RESOLVE_IDS,
            operation="execute",
            status="completed",
            processed=12,
        ))
        repository.save_summary(
            "wf_1",
            {"ids_resolved": 12},
            warnings_count=1,
        )

        self.assertEqual(1, len(connection.logs))
        self.assertEqual("resolve_ids", connection.logs[0]["stage"])
        self.assertEqual({"ids_resolved": 12}, connection.summaries["wf_1"]["metrics"])
        self.assertEqual(2, connection.commit_count)

    def test_save_and_load_inventory(self):
        connection = FakeConnection()
        repository = FlowRepository(connection)

        repository.save_inventory("wf_1", (
            LibraryInventoryItem(
                name="Obra A",
                source_path="/library/A",
                destination_path="/library/O/Obra A",
                group="O",
                main_chapters=10,
                total_chapters=11,
            ),
        ))

        inventory = repository.load_inventory("wf_1")

        self.assertEqual(1, len(inventory))
        self.assertEqual("Obra A", inventory[0].name)
        self.assertEqual(10, inventory[0].main_chapters)
        self.assertEqual("wf_1", repository.latest_inventory_execution_id())

    def test_save_load_and_update_normalization_plan(self):
        connection = FakeConnection()
        repository = FlowRepository(connection)

        saved = repository.save_normalization_plan(FileNormalizationPlan(
            execution_id="wf_1",
            status="ready",
            items=(
                FileNormalizationItem(
                    work_title="Obra A",
                    original_path="/library/Obra A/capitulo 01.pdf",
                    proposed_path="/library/Obra A/Obra A cap 1.pdf",
                    operation="rename_file",
                    status="ready",
                ),
            ),
        ))
        updated = repository.update_normalization_plan(FileNormalizationPlan(
            execution_id="wf_1",
            plan_id=saved.plan_id,
            status="applied",
            items=(
                FileNormalizationItem(
                    item_id=saved.items[0].item_id,
                    work_title="Obra A",
                    original_path="/library/Obra A/capitulo 01.pdf",
                    proposed_path="/library/Obra A/Obra A cap 1.pdf",
                    operation="rename_file",
                    status="applied",
                    message="Padronização aplicada.",
                ),
            ),
        ))

        latest = repository.latest_normalization_plan()

        self.assertEqual("applied", updated.status)
        self.assertEqual(saved.plan_id, latest.plan_id)
        self.assertEqual("applied", latest.items[0].status)
        self.assertEqual("Padronização aplicada.", latest.items[0].message)

    def test_recover_stale_execution_marks_running_stage_failed(self):
        connection = FakeConnection()
        connection.executions["wf_stale"] = {
            "execution_id": "wf_stale",
            "status": "running",
            "started_at": "2026-06-28T13:00:00-03:00",
            "finished_at": None,
            "current_stage": "resolve_ids",
            "error_message": None,
            "summary": {"status": "running"},
        }
        connection.stages.append({
            "execution_id": "wf_stale",
            "stage": "resolve_ids",
            "status": "running",
            "progress_current": 0,
            "progress_total": 10,
            "started_at": "2026-06-28T13:01:00-03:00",
            "finished_at": None,
            "error_message": None,
        })
        connection.stale_execution = ("wf_stale", "resolve_ids")

        recovered = FlowRepository(connection).recover_stale_execution(
            timeout_minutes=15,
            reason="Sem atividade recente.",
        )

        self.assertTrue(recovered)
        self.assertEqual("failed", connection.executions["wf_stale"]["status"])
        self.assertEqual("failed", connection.stages[0]["status"])
        self.assertEqual("Sem atividade recente.", connection.stages[0]["error_message"])
        self.assertEqual("FLOW_STALE_EXECUTION", connection.messages[0]["code"])
        self.assertEqual("stale_recovery", connection.logs[0]["operation"])


class FakeConnection:
    def __init__(self):
        self.executions = {}
        self.stages = []
        self.messages = []
        self.logs = []
        self.summaries = {}
        self.inventory = []
        self.normalization_plans = []
        self.normalization_items = []
        self.stale_execution = None
        self.committed = False
        self.commit_count = 0

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.committed = True
        self.commit_count += 1


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.result = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=()):
        normalized = " ".join(query.split()).lower()
        if normalized.startswith("insert into flow_executions"):
            (
                execution_id,
                status,
                started_at,
                finished_at,
                current_stage,
                progress,
                error_message,
                summary,
            ) = params
            self.connection.executions[execution_id] = {
                "execution_id": execution_id,
                "status": status,
                "started_at": started_at,
                "finished_at": finished_at,
                "current_stage": current_stage,
                "progress": _json_dict(progress),
                "error_message": error_message,
                "summary": _json_dict(summary),
            }
        elif normalized.startswith("delete from flow_stage_executions"):
            execution_id = params[0]
            self.connection.stages = [
                row for row in self.connection.stages
                if row["execution_id"] != execution_id
            ]
        elif normalized.startswith("delete from flow_messages"):
            execution_id = params[0]
            self.connection.messages = [
                row for row in self.connection.messages
                if row["execution_id"] != execution_id
            ]
        elif normalized.startswith("insert into flow_stage_executions"):
            (
                execution_id,
                stage,
                status,
                progress_current,
                progress_total,
                elapsed_seconds,
                estimated_remaining_seconds,
                current_item,
                processed,
                skipped,
                metrics,
                progress,
                error_message,
                started_at,
                finished_at,
            ) = params
            self.connection.stages.append({
                "execution_id": execution_id,
                "stage": stage,
                "status": status,
                "progress_current": progress_current,
                "progress_total": progress_total,
                "elapsed_seconds": elapsed_seconds,
                "estimated_remaining_seconds": estimated_remaining_seconds,
                "current_item": current_item,
                "processed": processed,
                "skipped": skipped,
                "metrics": _json_dict(metrics),
                "progress": _json_dict(progress),
                "error_message": error_message,
                "started_at": started_at,
                "finished_at": finished_at,
            })
        elif normalized.startswith("insert into flow_messages"):
            execution_id, stage, severity, code, message, details, level = params
            self.connection.messages.append({
                "execution_id": execution_id,
                "stage": stage,
                "severity": severity,
                "level": level,
                "code": code,
                "message": message,
                "details": _json_dict(details),
            })
        elif normalized.startswith("select * from flow_executions"):
            execution = self.connection.executions.get(params[0])
            self.result = [execution] if execution else []
        elif normalized.startswith("with active as"):
            if self.connection.stale_execution:
                execution_id, stage = self.connection.stale_execution
                self.result = [{"execution_id": execution_id, "stage": stage}]
            else:
                self.result = []
        elif normalized.startswith("select * from flow_stage_executions"):
            execution_id = params[0]
            self.result = [
                row for row in self.connection.stages
                if row["execution_id"] == execution_id
            ]
        elif normalized.startswith("select * from flow_messages"):
            execution_id = params[0]
            if "and stage is null" in normalized:
                self.result = [
                    row for row in self.connection.messages
                    if row["execution_id"] == execution_id and row["stage"] is None
                ]
            else:
                stage = params[1]
                self.result = [
                    row for row in self.connection.messages
                    if row["execution_id"] == execution_id and row["stage"] == stage
                ]
        elif normalized.startswith("insert into flow_logs"):
            (
                execution_id,
                stage,
                operation,
                status,
                duration,
                processed,
                error_code,
                message,
                details,
                level,
                event,
            ) = params
            self.connection.logs.append({
                "execution_id": execution_id,
                "stage": stage,
                "operation": operation,
                "status": status,
                "duration": duration,
                "processed": processed,
                "error_code": error_code,
                "message": message,
                "details": _json_dict(details),
                "level": level,
                "event": event,
            })
        elif (
            normalized.startswith("update flow_stage_executions")
            and "set status = 'failed'" in normalized
        ):
            reason, execution_id, stage = params
            for row in self.connection.stages:
                if row["execution_id"] == execution_id and row["stage"] == stage:
                    row["status"] = "failed"
                    row["finished_at"] = "now"
                    row["error_message"] = reason
        elif normalized.startswith("update flow_executions"):
            reason, execution_id = params
            row = self.connection.executions[execution_id]
            row["status"] = "failed"
            row["finished_at"] = "now"
            row["current_stage"] = None
            row["error_message"] = reason
            row["summary"] = {"status": "failed"}
        elif normalized.startswith("insert into flow_summaries"):
            (
                execution_id,
                metrics,
                warnings_count,
                errors_count,
                status,
                warnings,
                errors,
            ) = params
            self.connection.summaries[execution_id] = {
                "execution_id": execution_id,
                "metrics": _json_dict(metrics),
                "warnings_count": warnings_count,
                "errors_count": errors_count,
                "status": status,
                "warnings": _json_list(warnings),
                "errors": _json_list(errors),
            }
        elif normalized.startswith("delete from flow_library_inventory"):
            execution_id = params[0]
            self.connection.inventory = [
                row for row in self.connection.inventory
                if row["execution_id"] != execution_id
            ]
        elif normalized.startswith("insert into flow_library_inventory"):
            (
                execution_id,
                work_name,
                source_path,
                destination_path,
                group_name,
                current_group,
                main_chapters,
                side_chapters,
                total_chapters,
                is_valid,
                warnings,
                metrics,
            ) = params
            self.connection.inventory.append({
                "id": len(self.connection.inventory) + 1,
                "execution_id": execution_id,
                "work_name": work_name,
                "source_path": source_path,
                "destination_path": destination_path,
                "group_name": group_name,
                "current_group": current_group,
                "main_chapters": main_chapters,
                "side_chapters": side_chapters,
                "total_chapters": total_chapters,
                "is_valid": is_valid,
                "warnings": _json_list(warnings),
                "metrics": _json_dict(metrics),
            })
        elif normalized.startswith("select * from flow_library_inventory"):
            execution_id = params[0]
            self.result = [
                row for row in self.connection.inventory
                if row["execution_id"] == execution_id
            ]
        elif normalized.startswith("select i.execution_id"):
            self.result = (
                [{"execution_id": self.connection.inventory[-1]["execution_id"]}]
                if self.connection.inventory else []
            )
        elif normalized.startswith("insert into flow_file_normalization_plans"):
            (
                execution_id,
                status,
                total_items,
                total_conflicts,
                total_errors,
                error_message,
            ) = params
            plan = {
                "id": len(self.connection.normalization_plans) + 1,
                "execution_id": execution_id,
                "status": status,
                "total_items": total_items,
                "total_conflicts": total_conflicts,
                "total_errors": total_errors,
                "error_message": error_message,
            }
            self.connection.normalization_plans.append(plan)
            self.result = [{"id": plan["id"]}]
        elif normalized.startswith("insert into flow_file_normalization_items"):
            (
                plan_id,
                execution_id,
                inventory_issue_id,
                work_title,
                original_path,
                proposed_path,
                operation,
                status,
                severity,
                message,
                details,
            ) = params
            item = {
                "id": len(self.connection.normalization_items) + 1,
                "plan_id": plan_id,
                "execution_id": execution_id,
                "inventory_issue_id": inventory_issue_id,
                "work_title": work_title,
                "original_path": original_path,
                "proposed_path": proposed_path,
                "operation": operation,
                "status": status,
                "severity": severity,
                "message": message,
                "details": _json_dict(details),
            }
            self.connection.normalization_items.append(item)
            self.result = [{"id": item["id"]}]
        elif normalized.startswith("select * from flow_file_normalization_plans where id"):
            plan_id = params[0]
            self.result = [
                row for row in self.connection.normalization_plans
                if row["id"] == plan_id
            ]
        elif normalized.startswith("select * from flow_file_normalization_plans"):
            self.result = (
                [self.connection.normalization_plans[-1]]
                if self.connection.normalization_plans else []
            )
        elif normalized.startswith("select * from flow_file_normalization_items"):
            plan_id = params[0]
            self.result = [
                row for row in self.connection.normalization_items
                if row["plan_id"] == plan_id
            ]
        elif normalized.startswith("update flow_file_normalization_plans"):
            (
                status,
                total_items,
                total_conflicts,
                total_errors,
                error_message,
                _sets_applied_at,
                plan_id,
            ) = params
            for row in self.connection.normalization_plans:
                if row["id"] == plan_id:
                    row.update({
                        "status": status,
                        "total_items": total_items,
                        "total_conflicts": total_conflicts,
                        "total_errors": total_errors,
                        "error_message": error_message,
                    })
        elif normalized.startswith("update flow_file_normalization_items"):
            (
                status,
                severity,
                message,
                details,
                _sets_applied_at,
                item_id,
            ) = params
            for row in self.connection.normalization_items:
                if row["id"] == item_id:
                    row.update({
                        "status": status,
                        "severity": severity,
                        "message": message,
                        "details": _json_dict(details),
                    })
        else:
            self.result = []

    def fetchall(self):
        return self.result

    def fetchone(self):
        return self.result[0] if self.result else None


def _json_dict(value):
    import json
    if isinstance(value, str):
        return json.loads(value)
    return value or {}


def _json_list(value):
    import json
    if value is None:
        return []
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, list):
        return value
    return list(value)


if __name__ == "__main__":
    unittest.main()

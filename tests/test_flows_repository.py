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


class FakeConnection:
    def __init__(self):
        self.executions = {}
        self.stages = []
        self.messages = []
        self.logs = []
        self.summaries = {}
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
            execution_id, status, started_at, finished_at = params
            self.connection.executions[execution_id] = {
                "execution_id": execution_id,
                "status": status,
                "started_at": started_at,
                "finished_at": finished_at,
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
            })
        elif normalized.startswith("insert into flow_messages"):
            execution_id, stage, severity, code, message, details = params
            self.connection.messages.append({
                "execution_id": execution_id,
                "stage": stage,
                "severity": severity,
                "code": code,
                "message": message,
                "details": _json_dict(details),
            })
        elif normalized.startswith("select * from flow_executions"):
            execution = self.connection.executions.get(params[0])
            self.result = [execution] if execution else []
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
            })
        elif normalized.startswith("insert into flow_summaries"):
            execution_id, metrics, warnings_count, errors_count = params
            self.connection.summaries[execution_id] = {
                "execution_id": execution_id,
                "metrics": _json_dict(metrics),
                "warnings_count": warnings_count,
                "errors_count": errors_count,
            }
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


if __name__ == "__main__":
    unittest.main()

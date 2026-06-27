import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from manhwateca.database.connection import connect
from manhwateca.flows.domain import (
    FlowError,
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
from manhwateca.flows.integrations import LibraryInventoryItem


@dataclass(frozen=True)
class FlowLogRecord:
    execution_id: str
    operation: str
    status: str
    stage: StageId | None = None
    duration: float | None = None
    processed: int | None = None
    error_code: str | None = None
    message: str | None = None
    details: dict[str, Any] | None = None


class FlowRepository:
    def __init__(self, connection=None, *, connection_factory=None):
        self.connection = connection
        self.connection_factory = connection_factory or connect

    def save_execution(self, execution: WorkflowExecution) -> None:
        if not execution.execution_id:
            raise ValueError("execution_id é obrigatório para persistir Fluxos.")
        with self._cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO flow_executions (
                    execution_id, status, started_at, finished_at,
                    current_stage, progress, error_message, summary, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, now())
                ON CONFLICT (execution_id) DO UPDATE
                SET status = EXCLUDED.status,
                    started_at = EXCLUDED.started_at,
                    finished_at = EXCLUDED.finished_at,
                    current_stage = EXCLUDED.current_stage,
                    progress = EXCLUDED.progress,
                    error_message = EXCLUDED.error_message,
                    summary = EXCLUDED.summary,
                    updated_at = now()
                """,
                (
                    execution.execution_id,
                    execution.status.value,
                    execution.started_at,
                    execution.finished_at,
                    _current_stage_value(execution),
                    _json(execution.progress.to_dict()),
                    _execution_error_message(execution),
                    _json(_execution_summary(execution)),
                ),
            )
            cursor.execute(
                """
                DELETE FROM flow_stage_executions
                WHERE execution_id = %s
                """,
                (execution.execution_id,),
            )
            cursor.execute(
                """
                DELETE FROM flow_messages
                WHERE execution_id = %s
                """,
                (execution.execution_id,),
            )
            for stage in execution.stages:
                self._insert_stage(cursor, execution.execution_id, stage)
            for warning in execution.warnings:
                self._insert_message(
                    cursor, execution.execution_id, None, "warning", warning
                )
            for error in execution.errors:
                self._insert_message(
                    cursor, execution.execution_id, None, "error", error
                )
        self._connection().commit()

    def load_execution(self, execution_id: str) -> WorkflowExecution | None:
        row = self._fetch_one(
            """
            SELECT *
            FROM flow_executions
            WHERE execution_id = %s
            """,
            (execution_id,),
        )
        if row is None:
            return None
        stages = self._load_stages(execution_id)
        messages = self._fetch_all(
            """
            SELECT *
            FROM flow_messages
            WHERE execution_id = %s
              AND stage IS NULL
            ORDER BY id
            """,
            (execution_id,),
        )
        return WorkflowExecution(
            execution_id=row["execution_id"],
            status=WorkflowStatus(row["status"]),
            started_at=_string_or_none(row.get("started_at")),
            finished_at=_string_or_none(row.get("finished_at")),
            stages=tuple(stages),
            warnings=tuple(
                _message_from_row(item, FlowWarning)
                for item in messages if item["severity"] == "warning"
            ),
            errors=tuple(
                _message_from_row(item, FlowError)
                for item in messages if item["severity"] == "error"
            ),
        )

    def latest_execution(self) -> WorkflowExecution | None:
        row = self._fetch_one(
            """
            SELECT execution_id
            FROM flow_executions
            ORDER BY created_at DESC, execution_id DESC
            LIMIT 1
            """
        )
        if row is None:
            return None
        return self.load_execution(row["execution_id"])

    def list_history(self, limit: int = 20) -> list[WorkflowExecution]:
        rows = self._fetch_all(
            """
            SELECT execution_id
            FROM flow_executions
            ORDER BY created_at DESC, execution_id DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [
            execution for row in rows
            if (execution := self.load_execution(row["execution_id"])) is not None
        ]

    def append_log(self, record: FlowLogRecord) -> None:
        self._execute(
            """
            INSERT INTO flow_logs (
                execution_id, stage, operation, status, duration, processed,
                error_code, message, details, level, event
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            """,
            (
                record.execution_id,
                record.stage.value if record.stage else None,
                record.operation,
                record.status,
                record.duration,
                record.processed,
                record.error_code,
                record.message,
                _json(record.details or {}),
                record.status,
                record.operation,
            ),
        )
        self._connection().commit()

    def list_logs(self, execution_id: str) -> list[dict]:
        return [
            dict(row) for row in self._fetch_all(
                """
                SELECT *
                FROM flow_logs
                WHERE execution_id = %s
                ORDER BY created_at, id
                """,
                (execution_id,),
            )
        ]

    def save_summary(
        self,
        execution_id: str,
        metrics: dict[str, Any],
        *,
        warnings_count: int = 0,
        errors_count: int = 0,
        warnings: list[dict[str, Any]] | None = None,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self._execute(
            """
            INSERT INTO flow_summaries (
                execution_id, metrics, warnings_count, errors_count,
                status, warnings, errors, updated_at
            )
            VALUES (%s, %s::jsonb, %s, %s, %s, %s::jsonb, %s::jsonb, now())
            ON CONFLICT (execution_id) DO UPDATE
            SET metrics = EXCLUDED.metrics,
                warnings_count = EXCLUDED.warnings_count,
                errors_count = EXCLUDED.errors_count,
                status = EXCLUDED.status,
                warnings = EXCLUDED.warnings,
                errors = EXCLUDED.errors,
                updated_at = now()
            """,
            (
                execution_id,
                _json(metrics),
                warnings_count,
                errors_count,
                metrics.get("status"),
                _json(warnings or []),
                _json(errors or []),
            ),
        )
        self._connection().commit()

    def load_summary(self, execution_id: str) -> dict | None:
        row = self._fetch_one(
            """
            SELECT *
            FROM flow_summaries
            WHERE execution_id = %s
            """,
            (execution_id,),
        )
        return dict(row) if row else None

    def save_inventory(
        self,
        execution_id: str,
        inventory: tuple[LibraryInventoryItem, ...],
    ) -> None:
        self._execute(
            """
            DELETE FROM flow_library_inventory
            WHERE execution_id = %s
            """,
            (execution_id,),
        )
        with self._cursor() as cursor:
            for item in inventory:
                cursor.execute(
                    """
                    INSERT INTO flow_library_inventory (
                        execution_id, work_name, source_path, destination_path,
                        group_name, current_group, main_chapters, side_chapters,
                        total_chapters, is_valid, warnings, metrics, updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s::jsonb, %s::jsonb, now()
                    )
                    ON CONFLICT (execution_id, source_path) DO UPDATE
                    SET work_name = EXCLUDED.work_name,
                        destination_path = EXCLUDED.destination_path,
                        group_name = EXCLUDED.group_name,
                        current_group = EXCLUDED.current_group,
                        main_chapters = EXCLUDED.main_chapters,
                        side_chapters = EXCLUDED.side_chapters,
                        total_chapters = EXCLUDED.total_chapters,
                        is_valid = EXCLUDED.is_valid,
                        warnings = EXCLUDED.warnings,
                        metrics = EXCLUDED.metrics,
                        updated_at = now()
                    """,
                    (
                        execution_id,
                        item.name,
                        item.source_path,
                        item.destination_path,
                        item.group,
                        item.current_group,
                        item.main_chapters,
                        item.side_chapters,
                        item.total_chapters,
                        item.is_valid,
                        _json(_messages_to_list(item.warnings)),
                        _json(item.metrics),
                    ),
                )
        self._connection().commit()

    def load_inventory(self, execution_id: str) -> tuple[LibraryInventoryItem, ...]:
        rows = self._fetch_all(
            """
            SELECT *
            FROM flow_library_inventory
            WHERE execution_id = %s
            ORDER BY work_name, id
            """,
            (execution_id,),
        )
        return tuple(_inventory_from_row(row) for row in rows)

    def latest_inventory_execution_id(self) -> str | None:
        row = self._fetch_one(
            """
            SELECT i.execution_id
            FROM flow_library_inventory i
            JOIN flow_executions e ON e.execution_id = i.execution_id
            ORDER BY e.created_at DESC, i.id DESC
            LIMIT 1
            """
        )
        return row["execution_id"] if row else None

    def _insert_stage(self, cursor, execution_id: str, stage: StageExecution):
        result = stage.result or StageResult()
        cursor.execute(
            """
            INSERT INTO flow_stage_executions (
                execution_id, stage, status, progress_current,
                progress_total, elapsed_seconds,
                estimated_remaining_seconds, current_item, processed,
                skipped, metrics, progress, error_message, started_at, finished_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                %s::jsonb, %s, %s, %s
            )
            """,
            (
                execution_id,
                stage.stage_id.value,
                stage.status.value,
                stage.progress.current,
                stage.progress.total,
                stage.progress.elapsed_seconds,
                stage.progress.estimated_remaining_seconds,
                stage.current_item,
                result.processed,
                result.skipped,
                _json(result.metrics),
                _json(stage.progress.to_dict()),
                result.errors[0].message if result.errors else None,
                stage.started_at,
                stage.finished_at,
            ),
        )
        for message in stage.messages:
            self._insert_message(
                cursor, execution_id, stage.stage_id.value, "info", message
            )
        for warning in result.warnings:
            self._insert_message(
                cursor, execution_id, stage.stage_id.value, "warning", warning
            )
        for error in result.errors:
            self._insert_message(
                cursor, execution_id, stage.stage_id.value, "error", error
            )

    def _insert_message(
        self,
        cursor,
        execution_id: str,
        stage,
        severity: str,
        message: FlowMessage,
    ):
        cursor.execute(
            """
            INSERT INTO flow_messages (
                execution_id, stage, severity, code, message, details, level
            )
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
            """,
            (
                execution_id,
                stage,
                severity,
                message.code,
                message.message,
                _json(message.details),
                severity,
            ),
        )

    def _load_stages(self, execution_id: str) -> list[StageExecution]:
        rows = self._fetch_all(
            """
            SELECT *
            FROM flow_stage_executions
            WHERE execution_id = %s
            ORDER BY id
            """,
            (execution_id,),
        )
        return [self._stage_from_row(row) for row in rows]

    def _stage_from_row(self, row) -> StageExecution:
        messages = self._fetch_all(
            """
            SELECT *
            FROM flow_messages
            WHERE execution_id = %s
              AND stage = %s
            ORDER BY id
            """,
            (row["execution_id"], row["stage"]),
        )
        warnings = tuple(
            _message_from_row(item, FlowWarning)
            for item in messages if item["severity"] == "warning"
        )
        errors = tuple(
            _message_from_row(item, FlowError)
            for item in messages if item["severity"] == "error"
        )
        info = tuple(
            _message_from_row(item, FlowMessage)
            for item in messages if item["severity"] == "info"
        )
        return StageExecution(
            stage_id=StageId(row["stage"]),
            status=StageStatus(row["status"]),
            progress=Progress(
                current=row.get("progress_current") or 0,
                total=row.get("progress_total") or 0,
                elapsed_seconds=row.get("elapsed_seconds"),
                estimated_remaining_seconds=row.get(
                    "estimated_remaining_seconds"
                ),
            ),
            current_item=row.get("current_item"),
            started_at=_string_or_none(row.get("started_at")),
            finished_at=_string_or_none(row.get("finished_at")),
            result=StageResult(
                processed=row.get("processed") or 0,
                skipped=row.get("skipped") or 0,
                warnings=warnings,
                errors=errors,
                metrics=_dict(row.get("metrics")),
            ),
            messages=info,
        )

    def _fetch_all(self, query, params=None):
        with self._cursor() as cursor:
            cursor.execute(query, params or ())
            return list(cursor.fetchall())

    def _fetch_one(self, query, params=None):
        with self._cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def _execute(self, query, params=None):
        with self._cursor() as cursor:
            cursor.execute(query, params or ())

    def _cursor(self):
        return self._connection().cursor()

    def _connection(self):
        if self.connection is None:
            self.connection = self.connection_factory()
        return self.connection


def _message_from_row(row, message_type):
    return message_type(
        message=row.get("message") or "",
        code=row.get("code"),
        details=_dict(row.get("details")),
    )


def _dict(value) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


def _json(value) -> str:
    if value is None:
        value = {}
    return json.dumps(value, ensure_ascii=False)


def _string_or_none(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone().isoformat(timespec="seconds")
    return str(value)


def _current_stage_value(execution: WorkflowExecution) -> str | None:
    return execution.current_stage.stage_id.value if execution.current_stage else None


def _execution_error_message(execution: WorkflowExecution) -> str | None:
    if execution.errors:
        return execution.errors[0].message
    for stage in execution.stages:
        if stage.result and stage.result.errors:
            return stage.result.errors[0].message
    return None


def _execution_summary(execution: WorkflowExecution) -> dict[str, Any]:
    return {
        "status": execution.status.value,
        "currentStage": _current_stage_value(execution),
        "progress": execution.progress.to_dict(),
        "warnings": sum(
            len(stage.result.warnings)
            for stage in execution.stages
            if stage.result
        ) + len(execution.warnings),
        "errors": sum(
            len(stage.result.errors)
            for stage in execution.stages
            if stage.result
        ) + len(execution.errors),
    }


def _messages_to_list(messages: tuple[FlowMessage, ...]) -> list[dict[str, Any]]:
    return [
        {
            "message": message.message,
            "code": message.code,
            "details": message.details,
        }
        for message in messages
    ]


def _inventory_from_row(row) -> LibraryInventoryItem:
    return LibraryInventoryItem(
        name=row["work_name"],
        source_path=row["source_path"],
        destination_path=row.get("destination_path"),
        group=row.get("group_name"),
        current_group=row.get("current_group"),
        main_chapters=row.get("main_chapters") or 0,
        side_chapters=row.get("side_chapters") or 0,
        total_chapters=row.get("total_chapters") or 0,
        is_valid=bool(row.get("is_valid")),
        warnings=tuple(
            FlowWarning(
                item.get("message", ""),
                code=item.get("code"),
                details=item.get("details") or {},
            )
            for item in _list(row.get("warnings"))
        ),
        metrics=_dict(row.get("metrics")),
    )


def _list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return list(value)

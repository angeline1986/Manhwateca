import unittest
from unittest.mock import patch

from manhwateca.audit.models import AuditEvent
from manhwateca.audit.repository import AuditRepository
from manhwateca.audit.sanitizer import MASK


class AuditRepositoryTests(unittest.TestCase):
    def test_record_inserts_event_and_returns_id(self):
        connection = FakeConnection()
        repository = repository_with(connection)

        event_id = repository.record(AuditEvent(
            module="flows",
            action="workflow.start",
            entity_type="workflow_execution",
            entity_id="wf_1",
            message="Workflow iniciado.",
        ))

        self.assertEqual(1, event_id)
        self.assertEqual(1, len(connection.rows))
        self.assertEqual("flows", connection.rows[0]["module"])
        self.assertEqual("workflow.start", connection.rows[0]["action"])

    def test_list_recent_returns_desc_order(self):
        connection = FakeConnection()
        connection.rows = [
            row(1, "flows", "workflow.start"),
            row(2, "flows", "workflow.finish"),
        ]

        result = repository_with(connection).list_recent()

        self.assertEqual([2, 1], [item["id"] for item in result])

    def test_list_by_module_filters(self):
        connection = FakeConnection()
        connection.rows = [
            row(1, "flows", "workflow.start"),
            row(2, "notion", "notion.sync"),
        ]

        result = repository_with(connection).list_by_module("flows")

        self.assertEqual([1], [item["id"] for item in result])

    def test_list_by_entity_filters(self):
        connection = FakeConnection()
        connection.rows = [
            row(1, "flows", "workflow.start", "workflow_execution", "wf_1"),
            row(2, "flows", "workflow.start", "workflow_execution", "wf_2"),
        ]

        result = repository_with(connection).list_by_entity(
            "workflow_execution",
            "wf_2",
        )

        self.assertEqual([2], [item["id"] for item in result])

    def test_details_are_sanitized_before_persisting(self):
        connection = FakeConnection()
        repository = repository_with(connection)

        repository.record(AuditEvent(
            module="flows",
            action="workflow.start",
            details={"config": {"notion": {"token": "abc"}}},
        ))

        self.assertEqual(
            {"config": {"notion": {"token": MASK}}},
            connection.rows[0]["details"],
        )

    def test_error_status_is_accepted(self):
        connection = FakeConnection()

        repository_with(connection).record(AuditEvent(
            module="flows",
            action="workflow.fail",
            status="error",
            severity="error",
        ))

        self.assertEqual("error", connection.rows[0]["status"])
        self.assertEqual("error", connection.rows[0]["severity"])

    def test_empty_details_work(self):
        connection = FakeConnection()

        repository_with(connection).record(AuditEvent(
            module="flows",
            action="workflow.start",
        ))

        self.assertEqual({}, connection.rows[0]["details"])


def repository_with(connection):
    repository = AuditRepository()
    repository.database_url = None
    return PatchedRepository(repository, connection)


class PatchedRepository:
    def __init__(self, repository, connection):
        self.repository = repository
        self.connection = connection

    def __getattr__(self, name):
        attribute = getattr(self.repository, name)
        if not callable(attribute):
            return attribute

        def wrapped(*args, **kwargs):
            with patch(
                "manhwateca.audit.repository.transaction",
                return_value=FakeTransaction(self.connection),
            ):
                return attribute(*args, **kwargs)

        return wrapped


class FakeTransaction:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, *_args):
        return False


class FakeConnection:
    def __init__(self):
        self.rows = []

    def cursor(self):
        return FakeCursor(self)


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.result = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=()):
        import json

        normalized = " ".join(query.split()).lower()
        if normalized.startswith("insert into manhwateca.system_audit_logs"):
            (
                occurred_at,
                actor,
                session_id,
                request_id,
                module,
                action,
                entity_type,
                entity_id,
                status,
                severity,
                duration_ms,
                message,
                details,
            ) = params
            event_id = len(self.connection.rows) + 1
            self.connection.rows.append({
                "id": event_id,
                "occurred_at": occurred_at,
                "actor": actor,
                "session_id": session_id,
                "request_id": request_id,
                "module": module,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "status": status,
                "severity": severity,
                "duration_ms": duration_ms,
                "message": message,
                "details": json.loads(details),
            })
            self.result = [{"id": event_id}]
            return
        if "where module = %s" in normalized:
            module, limit = params
            self.result = [
                item for item in self._ordered(limit)
                if item["module"] == module
            ]
            return
        if "where entity_type = %s" in normalized:
            entity_type, entity_id, limit = params
            self.result = [
                item for item in self._ordered(limit)
                if item["entity_type"] == entity_type
                and item["entity_id"] == entity_id
            ]
            return
        if normalized.startswith("select * from manhwateca.system_audit_logs"):
            limit = params[0]
            self.result = self._ordered(limit)

    def _ordered(self, limit):
        return sorted(
            self.connection.rows,
            key=lambda item: item["id"],
            reverse=True,
        )[:limit]

    def fetchone(self):
        return self.result[0] if self.result else None

    def fetchall(self):
        return self.result


def row(
    event_id,
    module,
    action,
    entity_type=None,
    entity_id=None,
):
    return {
        "id": event_id,
        "module": module,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": {},
    }


if __name__ == "__main__":
    unittest.main()

import json

from manhwateca.audit.models import AuditEvent
from manhwateca.audit.sanitizer import sanitize_audit_details
from manhwateca.database.connection import transaction


class AuditRepository:
    def __init__(self, database_url: str | None = None):
        self.database_url = database_url

    def record(self, event: AuditEvent) -> int:
        details = sanitize_audit_details(event.details)

        with transaction(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO manhwateca.system_audit_logs (
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
                        details
                    )
                    VALUES (
                        COALESCE(%s, now()),
                        %s, %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s,
                        %s,
                        %s,
                        %s::jsonb
                    )
                    RETURNING id
                    """,
                    (
                        event.occurred_at,
                        event.actor,
                        event.session_id,
                        event.request_id,
                        event.module,
                        event.action,
                        event.entity_type,
                        event.entity_id,
                        event.status,
                        event.severity,
                        event.duration_ms,
                        event.message,
                        json.dumps(details, ensure_ascii=False),
                    ),
                )
                row = cursor.fetchone()
                return int(row["id"])

    def list_recent(self, limit: int = 100) -> list[dict]:
        with transaction(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM manhwateca.system_audit_logs
                    ORDER BY occurred_at DESC, id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                return list(cursor.fetchall())

    def list_by_module(self, module: str, limit: int = 100) -> list[dict]:
        with transaction(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM manhwateca.system_audit_logs
                    WHERE module = %s
                    ORDER BY occurred_at DESC, id DESC
                    LIMIT %s
                    """,
                    (module, limit),
                )
                return list(cursor.fetchall())

    def list_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
    ) -> list[dict]:
        with transaction(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM manhwateca.system_audit_logs
                    WHERE entity_type = %s
                      AND entity_id = %s
                    ORDER BY occurred_at DESC, id DESC
                    LIMIT %s
                    """,
                    (entity_type, entity_id, limit),
                )
                return list(cursor.fetchall())

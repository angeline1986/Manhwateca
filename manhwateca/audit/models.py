from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AuditStatus(str, Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class AuditSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AuditModule(str, Enum):
    FLOWS = "flows"
    DASHBOARD = "dashboard"
    LIBRARY = "library"
    SETTINGS = "settings"
    MANGAUPDATES = "mangaupdates"
    NOTION = "notion"
    SYSTEM = "system"


@dataclass(frozen=True)
class AuditEvent:
    module: str
    action: str

    status: str = AuditStatus.SUCCESS.value
    severity: str = AuditSeverity.INFO.value
    actor: str = "system"

    session_id: str | None = None
    request_id: str | None = None

    entity_type: str | None = None
    entity_id: str | None = None

    duration_ms: int | None = None
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    occurred_at: datetime | None = None

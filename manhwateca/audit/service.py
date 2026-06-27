import logging

from manhwateca.audit.models import AuditEvent
from manhwateca.audit.repository import AuditRepository


logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, repository: AuditRepository | None = None):
        self.repository = repository or AuditRepository()

    def record(self, event: AuditEvent) -> int | None:
        try:
            return self.repository.record(event)
        except Exception:
            logger.exception(
                "Falha ao gravar auditoria. A operação principal será preservada."
            )
            return None

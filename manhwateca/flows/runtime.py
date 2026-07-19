import logging
import os
import threading

from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    connect,
)
from manhwateca.flows.domain import FlowError, StageId
from manhwateca.flows.integrations import (
    FlowIntegrations,
    IntegrationCheck,
    IntegrationStatus,
    IntegrationValidation,
    MetadataUpdateResult,
    NotionSyncResult,
    SeriesSearchResult,
)
from manhwateca.flows.library import LocalLibraryIntegration
from manhwateca.flows.mangaupdates import MangaUpdatesFlowIntegration
from manhwateca.flows.normalization import (
    FileNormalizationService,
    LocalFileNormalizationIntegration,
)
from manhwateca.flows.orchestrator import WorkflowOrchestrator
from manhwateca.flows.repository import FlowRepository
from manhwateca.database import MangaRepository
from manhwateca.notion_sync.flow_integration import OfficialNotionFlowIntegration


logger = logging.getLogger(__name__)


class OfficialFlowBackend:
    def __init__(
        self,
        *,
        repository_factory=None,
        integrations: FlowIntegrations | None = None,
        audit_service=None,
        start_timeout: float = 2.0,
    ):
        self.repository_factory = repository_factory or FlowRepository
        self.integrations = integrations or default_flow_integrations()
        self.audit_service = audit_service
        self.start_timeout = start_timeout

    def get_status(self):
        repository = self.repository_factory()
        if hasattr(repository, "recover_stale_execution"):
            repository.recover_stale_execution(
                timeout_minutes=_stale_timeout_minutes(),
            )
        return repository.latest_execution()

    def list_history(self):
        return self.repository_factory().list_history()

    def start(self):
        started = threading.Event()
        thread = threading.Thread(
            target=self._run_start,
            args=(started,),
            daemon=True,
        )
        thread.start()
        started.wait(self.start_timeout)
        execution = self.get_status()
        if execution is None:
            raise RuntimeError("Workflow não pôde ser iniciado.")
        return execution

    def run_stage(self, stage: StageId, payload=None):
        started = threading.Event()
        thread = threading.Thread(
            target=self._run_stage,
            args=(stage, started, payload),
            daemon=True,
        )
        thread.start()
        started.wait(self.start_timeout)
        execution = self.get_status()
        if execution is None:
            raise RuntimeError("Nenhum Workflow iniciado.")
        return execution

    def cancel(self):
        return self._orchestrator().cancel()

    def generate_normalization_preview(self):
        return self._normalization_service().generate_preview()

    def apply_normalization(self):
        return self._normalization_service().apply_latest()

    def latest_normalization(self):
        return self._normalization_service().latest()

    def _run_start(self, started: threading.Event) -> None:
        try:
            self._orchestrator(
                on_started=started.set,
                on_stage_started=started.set,
            ).start()
        except Exception:
            logger.exception("Falha ao executar Workflow em background.")
            started.set()

    def _run_stage(self, stage: StageId, started: threading.Event, payload=None) -> None:
        try:
            self._orchestrator(on_stage_started=started.set).run_stage(
                stage,
                finish_after_stage=True,
                payload=payload,
            )
        except Exception:
            logger.exception("Falha ao executar etapa de Workflow em background.")
            started.set()

    def _orchestrator(self, **callbacks):
        return WorkflowOrchestrator(
            self.repository_factory(),
            self.integrations,
            audit_service=self.audit_service,
            **callbacks,
        )

    def _normalization_service(self):
        integration = (
            self.integrations.normalization
            if self.integrations.normalization is not None
            else LocalFileNormalizationIntegration()
        )
        return FileNormalizationService(self.repository_factory(), integration)


class DatabaseHealthIntegration:
    def check_status(self) -> IntegrationCheck:
        validation = self.validate()
        if validation.valid:
            return IntegrationCheck(
                "PostgreSQL",
                IntegrationStatus.OPERATIONAL,
                message="Banco de dados disponível.",
            )
        return IntegrationCheck(
            "PostgreSQL",
            IntegrationStatus.UNAVAILABLE,
            message="Banco de dados indisponível.",
            errors=validation.errors,
        )

    def validate(self, stage: StageId | None = None) -> IntegrationValidation:
        try:
            connection = connect()
            connection.close()
        except (DatabaseConfigurationError, DatabaseConnectionError) as error:
            return IntegrationValidation(
                stage=stage,
                valid=False,
                errors=(FlowError(str(error), code="DATABASE_UNAVAILABLE"),),
            )
        return IntegrationValidation(stage=stage, valid=True)


class DeferredMangaUpdatesIntegration:
    def check_status(self) -> IntegrationCheck:
        return IntegrationCheck(
            "MangaUpdates",
            IntegrationStatus.WARNING,
            message="Integração aguardando implementação oficial das etapas.",
        )

    def validate(self, stage: StageId | None = None) -> IntegrationValidation:
        return IntegrationValidation(stage=stage, valid=True)

    def search_series(self) -> SeriesSearchResult:
        return SeriesSearchResult()

    def get_metadata(self, selected_ids=None) -> MetadataUpdateResult:
        return MetadataUpdateResult()


class DeferredNotionIntegration:
    def check_status(self) -> IntegrationCheck:
        return IntegrationCheck(
            "Notion",
            IntegrationStatus.WARNING,
            message="Integração aguardando implementação oficial da etapa.",
        )

    def validate(self, stage: StageId | None = None) -> IntegrationValidation:
        return IntegrationValidation(stage=stage, valid=True)

    def sync_page(self, work_ids=None) -> NotionSyncResult:
        return NotionSyncResult()


class UnavailableNotionIntegration:
    def __init__(self, message: str = "Integração com o Notion indisponível."):
        self.message = message

    def check_status(self) -> IntegrationCheck:
        return IntegrationCheck(
            "Notion",
            IntegrationStatus.UNAVAILABLE,
            message=self.message,
            errors=(
                FlowError(
                    self.message,
                    code="NOTION_UNAVAILABLE",
                ),
            ),
        )

    def validate(self, stage: StageId | None = None) -> IntegrationValidation:
        return IntegrationValidation(
            stage=stage,
            valid=False,
            errors=(
                FlowError(
                    self.message,
                    code="NOTION_UNAVAILABLE",
                ),
            ),
        )

    def sync_page(self, work_ids=None) -> NotionSyncResult:
        return NotionSyncResult(
            failed=1,
            metrics={
                "status": "error",
                "message": self.message,
                "applied_count": 0,
                "failed_count": 1,
            },
        )


def default_flow_integrations() -> FlowIntegrations:
    return FlowIntegrations(
        database=DatabaseHealthIntegration(),
        library=LocalLibraryIntegration(),
        mangaupdates=MangaUpdatesFlowIntegration(),
        notion=_default_notion_integration(),
        normalization=LocalFileNormalizationIntegration(),
    )


def _default_notion_integration():
    token = os.environ.get("NOTION_TOKEN", "").strip()
    database_id = os.environ.get("NOTION_DATABASE_ID", "").strip()
    if not token or not database_id:
        return UnavailableNotionIntegration(
            "Integração com o Notion indisponível. Verifique a configuração do Notion.",
        )
    try:
        from notion_client import Client

        return OfficialNotionFlowIntegration(
            Client(auth=token),
            database_id,
            repository=MangaRepository(),
        )
    except Exception:
        logger.warning("Falha ao configurar integração oficial com Notion.")
        return UnavailableNotionIntegration()


def _stale_timeout_minutes() -> int:
    raw = os.environ.get("FLOW_STALE_TIMEOUT_MINUTES", "15")
    try:
        value = int(raw)
    except ValueError:
        return 15
    return max(1, value)

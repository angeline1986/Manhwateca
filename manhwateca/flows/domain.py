from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowStatus(str, Enum):
    IDLE = "idle"
    VALIDATING = "validating"
    RUNNING = "running"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class StageStatus(str, Enum):
    WAITING = "waiting"
    VALIDATING = "validating"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageId(str, Enum):
    ORGANIZE_LIBRARY = "organize_library"
    CATALOG_WORKS = "catalog_works"
    RESOLVE_IDS = "resolve_ids"
    UPDATE_METADATA = "update_metadata"
    SYNC_NOTION = "sync_notion"


@dataclass(frozen=True)
class FlowMessage:
    message: str
    code: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FlowWarning(FlowMessage):
    pass


@dataclass(frozen=True)
class FlowError(FlowMessage):
    pass


@dataclass(frozen=True)
class Progress:
    current: int = 0
    total: int = 0
    elapsed_seconds: int | None = None
    estimated_remaining_seconds: int | None = None

    @property
    def percent(self) -> int:
        if self.total <= 0:
            return 0
        value = round((self.current / self.total) * 100)
        return max(0, min(100, value))

    def to_dict(self) -> dict[str, Any]:
        return {
            "current": self.current,
            "total": self.total,
            "percent": self.percent,
            "elapsedSeconds": self.elapsed_seconds,
            "estimatedRemainingSeconds": self.estimated_remaining_seconds,
        }


@dataclass(frozen=True)
class StageDefinition:
    id: StageId
    order: int
    name: str
    purpose: str
    actions: tuple[str, ...]
    start_criteria: tuple[str, ...]
    completion_criteria: tuple[str, ...]
    depends_on: StageId | None = None
    next_stage: StageId | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id.value,
            "order": self.order,
            "name": self.name,
            "purpose": self.purpose,
            "actions": list(self.actions),
            "startCriteria": list(self.start_criteria),
            "completionCriteria": list(self.completion_criteria),
            "dependsOn": self.depends_on.value if self.depends_on else None,
            "nextStage": self.next_stage.value if self.next_stage else None,
        }


@dataclass(frozen=True)
class StageResult:
    processed: int = 0
    skipped: int = 0
    warnings: tuple[FlowWarning, ...] = ()
    errors: tuple[FlowError, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


@dataclass(frozen=True)
class StageExecution:
    stage_id: StageId
    status: StageStatus = StageStatus.WAITING
    progress: Progress = field(default_factory=Progress)
    result: StageResult | None = None
    current_item: str | None = None
    messages: tuple[FlowMessage, ...] = ()
    started_at: str | None = None
    finished_at: str | None = None

    @property
    def is_finished(self) -> bool:
        return self.status in {
            StageStatus.COMPLETED,
            StageStatus.COMPLETED_WITH_WARNINGS,
            StageStatus.SKIPPED,
            StageStatus.FAILED,
            StageStatus.CANCELLED,
        }

    def with_status(self, status: StageStatus) -> "StageExecution":
        return StageExecution(
            stage_id=self.stage_id,
            status=status,
            progress=self.progress,
            result=self.result,
            current_item=self.current_item,
            messages=self.messages,
            started_at=self.started_at,
            finished_at=self.finished_at,
        )


@dataclass(frozen=True)
class WorkflowExecution:
    status: WorkflowStatus = WorkflowStatus.IDLE
    stages: tuple[StageExecution, ...] = ()
    warnings: tuple[FlowWarning, ...] = ()
    errors: tuple[FlowError, ...] = ()
    execution_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None

    @property
    def current_stage(self) -> StageExecution | None:
        for stage in self.stages:
            if stage.status in {StageStatus.VALIDATING, StageStatus.RUNNING}:
                return stage
        return None

    @property
    def progress(self) -> Progress:
        if not self.stages:
            return Progress()
        finished = sum(1 for stage in self.stages if stage.is_finished)
        return Progress(current=finished, total=len(self.stages))

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings) or any(
            stage.result and stage.result.has_warnings
            for stage in self.stages
        )

    @property
    def has_errors(self) -> bool:
        return bool(self.errors) or any(
            stage.result and stage.result.has_errors
            for stage in self.stages
        )


OFFICIAL_STAGE_DEFINITIONS = (
    StageDefinition(
        id=StageId.ORGANIZE_LIBRARY,
        order=1,
        name="Organizar Biblioteca",
        purpose="Preparar a biblioteca para processamento.",
        actions=(
            "localizar diretórios",
            "validar estrutura",
            "identificar novas obras",
            "atualizar índice interno",
            "registrar inconsistências",
        ),
        start_criteria=(
            "biblioteca configurada",
            "diretório acessível",
        ),
        completion_criteria=(
            "varredura finalizada",
            "índice atualizado",
            "inconsistências registradas",
        ),
        next_stage=StageId.CATALOG_WORKS,
    ),
    StageDefinition(
        id=StageId.CATALOG_WORKS,
        order=2,
        name="Catalogar Obras",
        purpose="Transformar diretórios válidos em registros persistidos no banco de dados.",
        actions=(
            "criar novos registros",
            "atualizar registros existentes",
            "validar dados mínimos",
            "identificar duplicidades",
        ),
        start_criteria=("organização concluída",),
        completion_criteria=(
            "todas as obras catalogadas",
            "registros atualizados",
            "pendências identificadas",
        ),
        depends_on=StageId.ORGANIZE_LIBRARY,
        next_stage=StageId.RESOLVE_IDS,
    ),
    StageDefinition(
        id=StageId.RESOLVE_IDS,
        order=3,
        name="Resolver IDs",
        purpose="Associar cada obra ao seu identificador oficial no MangaUpdates.",
        actions=(
            "pesquisar candidatos",
            "validar correspondências",
            "confirmar associações",
            "registrar obras não localizadas",
        ),
        start_criteria=("obra catalogada",),
        completion_criteria=(
            "todos os IDs possíveis resolvidos",
            "pendências registradas",
        ),
        depends_on=StageId.CATALOG_WORKS,
        next_stage=StageId.UPDATE_METADATA,
    ),
    StageDefinition(
        id=StageId.UPDATE_METADATA,
        order=4,
        name="Atualizar Metadados",
        purpose="Atualizar automaticamente as informações oficiais das obras.",
        actions=(
            "consultar MangaUpdates",
            "atualizar títulos",
            "atualizar autores",
            "atualizar gêneros",
            "atualizar status",
            "atualizar capítulos",
            "registrar data da sincronização",
        ),
        start_criteria=("obra com mangaupdates_id",),
        completion_criteria=(
            "metadados atualizados",
            "histórico registrado",
        ),
        depends_on=StageId.RESOLVE_IDS,
        next_stage=StageId.SYNC_NOTION,
    ),
    StageDefinition(
        id=StageId.SYNC_NOTION,
        order=5,
        name="Sincronizar Notion",
        purpose="Refletir no Notion todas as alterações realizadas durante o Workflow.",
        actions=(
            "criar páginas",
            "atualizar páginas existentes",
            "sincronizar propriedades",
            "registrar falhas",
            "consolidar resultados",
        ),
        start_criteria=("metadados atualizados",),
        completion_criteria=(
            "sincronização encerrada",
            "resumo disponível",
        ),
        depends_on=StageId.UPDATE_METADATA,
    ),
)


def official_stage_ids() -> tuple[StageId, ...]:
    return tuple(stage.id for stage in OFFICIAL_STAGE_DEFINITIONS)

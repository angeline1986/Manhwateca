from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from manhwateca.flows.domain import FlowError, FlowWarning, StageId


class IntegrationStatus(str, Enum):
    OPERATIONAL = "operational"
    CHECKING = "checking"
    WARNING = "warning"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class IntegrationCheck:
    name: str
    status: IntegrationStatus
    message: str | None = None
    warnings: tuple[FlowWarning, ...] = ()
    errors: tuple[FlowError, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return self.status in {
            IntegrationStatus.OPERATIONAL,
            IntegrationStatus.WARNING,
        }


@dataclass(frozen=True)
class IntegrationValidation:
    stage: StageId | None
    valid: bool
    warnings: tuple[FlowWarning, ...] = ()
    errors: tuple[FlowError, ...] = ()


@dataclass(frozen=True)
class LibraryInventoryIssue:
    work_title: str
    relative_path: str
    file_name: str
    issue_type: str
    severity: str
    message: str
    suggestion: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LibraryInventoryItem:
    name: str
    source_path: str
    destination_path: str | None = None
    group: str | None = None
    current_group: str | None = None
    main_chapters: int = 0
    side_chapters: int = 0
    total_chapters: int = 0
    is_valid: bool = True
    warnings: tuple[FlowWarning, ...] = ()
    issues: tuple[LibraryInventoryIssue, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LibraryScanResult:
    works_found: int = 0
    chapters_found: int = 0
    correct_locations: int = 0
    pending_moves: int = 0
    conflicts: int = 0
    duplicates: int = 0
    empty_folders: int = 0
    inconsistencies: tuple[FlowWarning, ...] = ()
    inventory: tuple[LibraryInventoryItem, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CatalogResult:
    created: int = 0
    updated: int = 0
    duplicates: int = 0
    pending: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SeriesSearchResult:
    searched: int = 0
    matched: int = 0
    pending: int = 0
    not_found: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MetadataUpdateResult:
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NotionSyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FileNormalizationItem:
    work_title: str
    original_path: str
    proposed_path: str
    operation: str
    status: str = "ready"
    severity: str = "info"
    message: str | None = None
    inventory_issue_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)
    item_id: int | None = None


@dataclass(frozen=True)
class FileNormalizationPlan:
    execution_id: str
    status: str
    items: tuple[FileNormalizationItem, ...] = ()
    plan_id: int | None = None
    total_conflicts: int = 0
    total_errors: int = 0
    error_message: str | None = None

    @property
    def total_items(self) -> int:
        return len(self.items)


class DatabaseHealthIntegration(Protocol):
    def check_status(self) -> IntegrationCheck:
        ...

    def validate(self, stage: StageId | None = None) -> IntegrationValidation:
        ...


class LibraryIntegration(Protocol):
    def check_status(self) -> IntegrationCheck:
        ...

    def validate(self, stage: StageId | None = None) -> IntegrationValidation:
        ...

    def scan_library(self) -> LibraryScanResult:
        ...

    def catalog_works(self) -> CatalogResult:
        ...


class MangaUpdatesIntegration(Protocol):
    def check_status(self) -> IntegrationCheck:
        ...

    def validate(self, stage: StageId | None = None) -> IntegrationValidation:
        ...

    def search_series(self) -> SeriesSearchResult:
        ...

    def get_metadata(self, selected_ids=None) -> MetadataUpdateResult:
        ...


class NotionIntegration(Protocol):
    def check_status(self) -> IntegrationCheck:
        ...

    def validate(self, stage: StageId | None = None) -> IntegrationValidation:
        ...

    def sync_page(self, work_ids=None) -> NotionSyncResult:
        ...


class FileNormalizationIntegration(Protocol):
    def generate_preview(self, execution_id: str) -> FileNormalizationPlan:
        ...

    def validate_plan(self, plan: FileNormalizationPlan) -> FileNormalizationPlan:
        ...

    def apply_plan(self, plan: FileNormalizationPlan) -> FileNormalizationPlan:
        ...


@dataclass(frozen=True)
class FlowIntegrations:
    database: DatabaseHealthIntegration
    library: LibraryIntegration
    mangaupdates: MangaUpdatesIntegration
    notion: NotionIntegration
    normalization: FileNormalizationIntegration | None = None

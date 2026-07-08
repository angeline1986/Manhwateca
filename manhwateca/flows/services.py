from dataclasses import dataclass
from typing import Protocol

from manhwateca.flows.domain import FlowWarning, StageResult, StageId
from manhwateca.flows.integrations import FlowIntegrations


class StageService(Protocol):
    def validate(self) -> tuple[FlowWarning, ...]:
        ...

    def execute(self, **kwargs) -> StageResult:
        ...

    def finalize(self, result: StageResult) -> StageResult:
        ...


@dataclass
class BaseStageService:
    integrations: FlowIntegrations
    stage_id: StageId

    def validate(self) -> tuple[FlowWarning, ...]:
        validation = self._integration().validate(self.stage_id)
        if not validation.valid and validation.errors:
            raise RuntimeError("; ".join(error.message for error in validation.errors))
        return validation.warnings

    def execute(self, **kwargs) -> StageResult:
        return StageResult()

    def finalize(self, result: StageResult) -> StageResult:
        return result

    def _integration(self):
        raise NotImplementedError


class OrganizeLibraryService(BaseStageService):
    def __init__(self, integrations: FlowIntegrations):
        super().__init__(integrations, StageId.ORGANIZE_LIBRARY)

    def execute(self, **kwargs) -> StageResult:
        result = self.integrations.library.scan_library()
        warnings = result.inconsistencies
        if result.works_found == 0 and not warnings:
            warnings = (
                FlowWarning(
                    "Nenhuma obra foi detectada na biblioteca.",
                    code="LIBRARY_EMPTY",
                ),
            )
        return StageResult(
            processed=result.works_found,
            warnings=warnings,
            inventory=result.inventory,
            metrics={
                "worksFound": result.works_found,
                "chaptersFound": result.chapters_found,
                "correctLocations": result.correct_locations,
                "pendingMoves": result.pending_moves,
                "conflicts": result.conflicts,
                "duplicates": result.duplicates,
                "emptyFolders": result.empty_folders,
                **result.metrics,
            },
        )

    def _integration(self):
        return self.integrations.library


class CatalogWorksService(BaseStageService):
    def __init__(self, integrations: FlowIntegrations):
        super().__init__(integrations, StageId.CATALOG_WORKS)

    def execute(self, **kwargs) -> StageResult:
        result = self.integrations.library.catalog_works()
        warnings = ()
        if result.created + result.updated == 0 and result.pending == 0:
            warnings = (
                FlowWarning(
                    "Nenhuma obra válida foi catalogada.",
                    code="CATALOG_EMPTY",
                ),
            )
        elif result.pending or result.duplicates:
            warnings = (
                FlowWarning(
                    "Catalogação concluída com pendências.",
                    details={
                        "pending": result.pending,
                        "duplicates": result.duplicates,
                    },
                ),
            )
        return StageResult(
            processed=result.created + result.updated,
            warnings=warnings,
            metrics={
                "created": result.created,
                "updated": result.updated,
                "duplicates": result.duplicates,
                "pending": result.pending,
                **result.metrics,
            },
        )

    def _integration(self):
        return self.integrations.library


class ResolveIdsService(BaseStageService):
    def __init__(self, integrations: FlowIntegrations):
        super().__init__(integrations, StageId.RESOLVE_IDS)

    def execute(self, **kwargs) -> StageResult:
        result = self.integrations.mangaupdates.search_series()
        warnings = ()
        if result.searched == 0:
            warnings = (
                FlowWarning(
                    "Nenhuma obra elegível para resolução de ID.",
                    code="RESOLVE_IDS_EMPTY",
                    details={
                        "catalogWorks": result.metrics.get("catalogWorks", 0),
                        "alreadyResolved": result.metrics.get("alreadyResolved", 0),
                    },
                ),
            )
        elif result.pending or result.not_found:
            warnings = (
                FlowWarning(
                    "Resolução de IDs concluída com pendências.",
                    details={
                        "pending": result.pending,
                        "notFound": result.not_found,
                    },
                ),
            )
        return StageResult(
            processed=result.matched,
            skipped=result.not_found,
            warnings=warnings,
            metrics={
                "searched": result.searched,
                "matched": result.matched,
                "pending": result.pending,
                "notFound": result.not_found,
                **result.metrics,
            },
        )

    def _integration(self):
        return self.integrations.mangaupdates


class UpdateMetadataService(BaseStageService):
    def __init__(self, integrations: FlowIntegrations):
        super().__init__(integrations, StageId.UPDATE_METADATA)

    def execute(self, **kwargs) -> StageResult:
        selected_ids = kwargs.get("selected_ids")
        result = self.integrations.mangaupdates.get_metadata(selected_ids=selected_ids)
        warnings = ()
        if result.skipped or result.failed:
            warnings = (
                FlowWarning(
                    "Atualização de metadados concluída com alertas.",
                    details={
                        "skipped": result.skipped,
                        "failed": result.failed,
                    },
                ),
            )
        return StageResult(
            processed=result.updated,
            skipped=result.skipped,
            warnings=warnings,
            metrics={
                "updated": result.updated,
                "skipped": result.skipped,
                "failed": result.failed,
                **result.metrics,
            },
        )

    def _integration(self):
        return self.integrations.mangaupdates


class SyncNotionService(BaseStageService):
    def __init__(self, integrations: FlowIntegrations):
        super().__init__(integrations, StageId.SYNC_NOTION)

    def execute(self, **kwargs) -> StageResult:
        result = self.integrations.notion.sync_page()
        warnings = ()
        if result.skipped or result.failed:
            warnings = (
                FlowWarning(
                    "Sincronização com Notion concluída com alertas.",
                    details={
                        "skipped": result.skipped,
                        "failed": result.failed,
                    },
                ),
            )
        return StageResult(
            processed=result.created + result.updated,
            skipped=result.skipped,
            warnings=warnings,
            metrics={
                "created": result.created,
                "updated": result.updated,
                "skipped": result.skipped,
                "failed": result.failed,
                **result.metrics,
            },
        )

    def _integration(self):
        return self.integrations.notion


def default_stage_services(integrations: FlowIntegrations) -> dict[StageId, StageService]:
    return {
        StageId.ORGANIZE_LIBRARY: OrganizeLibraryService(integrations),
        StageId.CATALOG_WORKS: CatalogWorksService(integrations),
        StageId.RESOLVE_IDS: ResolveIdsService(integrations),
        StageId.UPDATE_METADATA: UpdateMetadataService(integrations),
        StageId.SYNC_NOTION: SyncNotionService(integrations),
    }

from pathlib import Path

from manhwateca.flows.domain import FlowError, FlowWarning, StageId
from manhwateca.flows.integrations import (
    CatalogResult,
    IntegrationCheck,
    IntegrationStatus,
    IntegrationValidation,
    LibraryInventoryItem,
    LibraryScanResult,
)
from manhwateca.flows.repository import FlowRepository
from manhwateca.database.manga_repository import MangaRepository
from manhwateca.library_organizer.discovery import (
    find_empty_legacy_folders,
    find_manga_folders,
    is_manga_folder,
)
from manhwateca.library_organizer.grouping import (
    get_current_group,
    get_group,
    is_group_folder,
    is_legacy_container,
)
from manhwateca.library_organizer.planning import build_plan, detect_conflicts
from manhwateca.shared.duplicates import detect_duplicates_organize
from manhwateca.shared.paths import get_required_path_env
from manhwateca.shared.sizing import classify_manga_size


class LocalLibraryIntegration:
    def __init__(
        self,
        library_root: Path | str | None = None,
        *,
        flow_repository_factory=FlowRepository,
        manga_repository_factory=MangaRepository,
    ):
        self.library_root = Path(library_root).expanduser() if library_root else None
        self.flow_repository_factory = flow_repository_factory
        self.manga_repository_factory = manga_repository_factory

    def check_status(self) -> IntegrationCheck:
        validation = self.validate()
        if validation.valid and not validation.warnings:
            return IntegrationCheck(
                "Biblioteca local",
                IntegrationStatus.OPERATIONAL,
                message="Biblioteca configurada e acessível.",
            )
        if validation.valid:
            return IntegrationCheck(
                "Biblioteca local",
                IntegrationStatus.WARNING,
                message="Biblioteca acessível com alertas.",
                warnings=validation.warnings,
            )
        return IntegrationCheck(
            "Biblioteca local",
            IntegrationStatus.UNAVAILABLE,
            message="Biblioteca indisponível.",
            errors=validation.errors,
        )

    def validate(self, stage: StageId | None = None) -> IntegrationValidation:
        try:
            root = self._root()
        except ValueError as error:
            return IntegrationValidation(
                stage=stage,
                valid=False,
                errors=(FlowError(str(error), code="LIBRARY_NOT_CONFIGURED"),),
            )
        if not root.exists():
            return IntegrationValidation(
                stage=stage,
                valid=False,
                errors=(FlowError(
                    f"Biblioteca não encontrada: {root}",
                    code="LIBRARY_NOT_FOUND",
                ),),
            )
        if not root.is_dir():
            return IntegrationValidation(
                stage=stage,
                valid=False,
                errors=(FlowError(
                    f"Biblioteca não é um diretório: {root}",
                    code="LIBRARY_NOT_DIRECTORY",
                ),),
            )
        try:
            next(root.iterdir(), None)
        except OSError as error:
            return IntegrationValidation(
                stage=stage,
                valid=False,
                errors=(FlowError(
                    f"Biblioteca inacessível: {error}",
                    code="LIBRARY_NOT_ACCESSIBLE",
                ),),
            )
        return IntegrationValidation(stage=stage, valid=True)

    def scan_library(self) -> LibraryScanResult:
        validation = self.validate(StageId.ORGANIZE_LIBRARY)
        if not validation.valid:
            raise RuntimeError("; ".join(error.message for error in validation.errors))

        root = self._root()
        manga_folders = find_manga_folders(
            root,
            is_group_folder,
            lambda path: is_manga_folder(path, is_group_folder, is_legacy_container),
        )
        empty_folders = find_empty_legacy_folders(root, is_legacy_container)
        if not manga_folders:
            media_files = sum(
                1
                for path in root.rglob("*")
                if path.is_file() and path.suffix.lower() in {".pdf", ".cbz"}
            )
            return LibraryScanResult(
                inconsistencies=(FlowWarning(
                    "Nenhuma obra foi detectada na biblioteca.",
                    code="LIBRARY_EMPTY",
                    details={"mediaFiles": media_files},
                ),),
                metrics={
                    "libraryRoot": str(root),
                    "mediaFiles": media_files,
                },
            )

        plan = build_plan(
            manga_folders,
            root,
            get_group,
            lambda path: get_current_group(path, root),
        )
        conflicts = detect_conflicts(plan)
        duplicates = detect_duplicates_organize(plan)
        chapters_found = sum(item["total_caps"] for item in plan)
        correct = sum(1 for item in plan if item["is_correct"])
        pending_moves = len(plan) - correct
        warnings = _warnings(conflicts, duplicates, empty_folders)

        return LibraryScanResult(
            works_found=len(plan),
            chapters_found=chapters_found,
            correct_locations=correct,
            pending_moves=pending_moves,
            conflicts=len(conflicts),
            duplicates=len(duplicates),
            empty_folders=len(empty_folders),
            inconsistencies=warnings,
            inventory=_inventory_items(plan, conflicts, duplicates),
            metrics={
                "libraryRoot": str(root),
                "groups": sorted({item["group"] for item in plan}),
            },
        )

    def catalog_works(self):
        flow_repository = self.flow_repository_factory()
        execution = flow_repository.latest_execution()
        if execution is None or execution.execution_id is None:
            return CatalogResult(
                metrics={"inventoryExecutionId": None, "reason": "empty_inventory"},
            )
        execution_id = execution.execution_id

        inventory = flow_repository.load_inventory(execution_id)
        manga_repository = self.manga_repository_factory()
        created = 0
        updated = 0
        pending = 0

        for item in inventory:
            if not item.is_valid:
                pending += 1
                continue
            payload = _catalog_payload(item)
            existing = manga_repository.find_by_normalized_title(item.name)
            manga_repository.save_catalog_manga(payload)
            if existing:
                updated += 1
            else:
                created += 1

        return CatalogResult(
            created=created,
            updated=updated,
            pending=pending,
            metrics={
                "inventoryExecutionId": execution_id,
                "inventoryItems": len(inventory),
                "validItems": len([item for item in inventory if item.is_valid]),
            },
        )

    def _root(self) -> Path:
        return self.library_root or get_required_path_env("MANGA_ROOT")


def _warnings(conflicts, duplicates, empty_folders) -> tuple[FlowWarning, ...]:
    warnings = []
    if conflicts:
        warnings.append(FlowWarning(
            "Conflitos de organização encontrados.",
            code="LIBRARY_CONFLICTS",
            details={"count": len(conflicts)},
        ))
    if duplicates:
        warnings.append(FlowWarning(
            "Possíveis duplicidades encontradas.",
            code="LIBRARY_DUPLICATES",
            details={"count": len(duplicates)},
        ))
    if empty_folders:
        warnings.append(FlowWarning(
            "Pastas vazias encontradas para revisão.",
            code="LIBRARY_EMPTY_FOLDERS",
            details={"count": len(empty_folders)},
        ))
    return tuple(warnings)


def _inventory_items(plan, conflicts, duplicates) -> tuple[LibraryInventoryItem, ...]:
    return tuple(
        LibraryInventoryItem(
            name=item["name"],
            source_path=str(item["source"]),
            destination_path=str(item["destination"]),
            group=item["group"],
            current_group=item["current_group"],
            main_chapters=item["main_caps"],
            side_chapters=item["side_caps"],
            total_chapters=item["total_caps"],
            is_valid=not (
                _has_conflict(item, conflicts)
                or _has_duplicate(item, duplicates)
            ),
            warnings=_item_warnings(item, conflicts, duplicates),
            metrics={
                "isCorrect": item["is_correct"],
                "existsAtDestination": item["exists"],
            },
        )
        for item in plan
    )


def _has_conflict(item, conflicts) -> bool:
    return any(item in conflict["items"] for conflict in conflicts)


def _has_duplicate(item, duplicates) -> bool:
    return any(
        item["name"] in [entry["original"] for entry in duplicate["entries"]]
        for duplicate in duplicates
    )


def _item_warnings(item, conflicts, duplicates) -> tuple[FlowWarning, ...]:
    warnings = []
    if _has_conflict(item, conflicts):
        warnings.append(FlowWarning(
            "Obra com conflito de organização.",
            code="LIBRARY_ITEM_CONFLICT",
        ))
    if _has_duplicate(item, duplicates):
        warnings.append(FlowWarning(
            "Obra com possível duplicidade.",
            code="LIBRARY_ITEM_DUPLICATE",
        ))
    return tuple(warnings)


def _catalog_payload(item: LibraryInventoryItem) -> dict:
    return {
        "nome": item.name,
        "alias": [],
        "ultimo_lido": None,
        "main_caps": item.main_chapters,
        "side_caps": item.side_chapters,
        "total_caps": item.total_chapters,
        "tamanho": classify_manga_size(item.main_chapters),
        "count_status": "OK",
        "path": item.destination_path or item.source_path,
    }

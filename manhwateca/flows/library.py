from pathlib import Path

from manhwateca.flows.domain import FlowError, FlowWarning, StageId
from manhwateca.flows.integrations import (
    IntegrationCheck,
    IntegrationStatus,
    IntegrationValidation,
    LibraryScanResult,
)
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


class LocalLibraryIntegration:
    def __init__(self, library_root: Path | str | None = None):
        self.library_root = Path(library_root).expanduser() if library_root else None

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
            metrics={
                "libraryRoot": str(root),
                "groups": sorted({item["group"] for item in plan}),
            },
        )

    def catalog_works(self):
        raise NotImplementedError(
            "Catalogação pertence à etapa Catalogar Obras."
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

from pathlib import Path
import re

from manhwateca.flows.domain import FlowError, FlowWarning, StageId
from manhwateca.flows.integrations import (
    CatalogResult,
    IntegrationCheck,
    IntegrationStatus,
    IntegrationValidation,
    LibraryInventoryItem,
    LibraryInventoryIssue,
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


MEDIA_EXTENSIONS = {".pdf", ".cbz"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


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
        inventory = _inventory_items(root, plan, conflicts, duplicates)
        issue_count = sum(len(item.issues) for item in inventory)
        if issue_count:
            warnings = (
                *warnings,
                FlowWarning(
                    "Arquivos de capítulos fora do padrão encontrados.",
                    code="LIBRARY_CHAPTER_ISSUES",
                    details={"count": issue_count},
                ),
            )

        return LibraryScanResult(
            works_found=len(plan),
            chapters_found=chapters_found,
            correct_locations=correct,
            pending_moves=pending_moves,
            conflicts=len(conflicts),
            duplicates=len(duplicates),
            empty_folders=len(empty_folders),
            inconsistencies=warnings,
            inventory=inventory,
            metrics={
                "libraryRoot": str(root),
                "groups": sorted({item["group"] for item in plan}),
                "chapterIssues": issue_count,
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
        structural_issues = 0

        for item in inventory:
            if not item.is_valid:
                pending += 1
                continue
            item_issues = item.metrics.get("chapterIssues", 0)
            if item_issues:
                structural_issues += item_issues
                pending += 1
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
                "structuralIssues": structural_issues,
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


def _inventory_items(
    root: Path,
    plan,
    conflicts,
    duplicates,
) -> tuple[LibraryInventoryItem, ...]:
    return tuple(
        _inventory_item(root, item, conflicts, duplicates)
        for item in plan
    )


def _inventory_item(root, item, conflicts, duplicates) -> LibraryInventoryItem:
    issues = _chapter_issues(root, item)
    return LibraryInventoryItem(
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
        warnings=(*_item_warnings(item, conflicts, duplicates), *_issue_warnings(issues)),
        issues=issues,
        metrics={
            "isCorrect": item["is_correct"],
            "existsAtDestination": item["exists"],
            "chapterIssues": len(issues),
        },
    )


def _chapter_issues(root: Path, item) -> tuple[LibraryInventoryIssue, ...]:
    issues = []
    source = Path(item["source"])
    for file in sorted(source.iterdir()):
        if not file.is_file():
            continue
        suffix = file.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            normalized = file.stem.casefold()
            if _is_cover_file(normalized):
                issues.append(_issue(root, item, file, "cover_file", "warning",
                    "Arquivo de capa encontrado junto aos capítulos.",
                    "Manter capas separadas da sequência de capítulos.",
                ))
            else:
                issues.append(_issue(root, item, file, "image_file", "warning",
                    "Arquivo de imagem encontrado junto aos capítulos.",
                    "Mover imagens soltas para uma pasta de apoio ou definir como capa quando aplicável.",
                ))
            continue
        if suffix not in MEDIA_EXTENSIONS:
            continue
        normalized = file.stem.casefold()
        if _is_cover_file(normalized):
            issues.append(_issue(root, item, file, "cover_file", "warning",
                "Arquivo de capa encontrado junto aos capítulos.",
                "Manter capas padronizadas como arquivo de capa, separadas da sequência de capítulos.",
            ))
        if _has_range_marker(normalized):
            issues.append(_issue(root, item, file, "chapter_range", "warning",
                "Arquivo parece conter intervalo de capítulos.",
                "Dividir o arquivo ou padronizar explicitamente o intervalo antes de continuar.",
            ))
        if re.search(r"\b\d+\.\d+\b", normalized):
            issues.append(_issue(root, item, file, "chapter_decimal", "warning",
                "Arquivo possui capítulo decimal.",
                "Revisar se o capítulo decimal deve ser side story ou capítulo principal.",
            ))
        if "side" in normalized:
            issues.append(_issue(root, item, file, "side_story", "info",
                "Arquivo identificado como side story.",
                "Confirmar se side stories estão nomeadas no padrão esperado.",
            ))
        if any(marker in normalized for marker in ("hiatus", "fim", "final")):
            issues.append(_issue(root, item, file, "hiatus_or_final_marker", "warning",
                "Arquivo possui marcador editorial no nome.",
                "Remover marcadores como Fim/Hiatus do nome do capítulo e registrar isso nos metadados.",
            ))
        if _looks_like_unknown_chapter(file.name):
            issues.append(_issue(root, item, file, "unknown_chapter_pattern", "warning",
                "Nome de capítulo fora do padrão esperado.",
                "Padronizar o nome para Capítulo N antes das próximas etapas.",
            ))
    return tuple(issues)


def _issue(root, item, file, issue_type, severity, message, suggestion):
    try:
        relative_path = str(file.relative_to(root))
    except ValueError:
        relative_path = file.name
    return LibraryInventoryIssue(
        work_title=item["name"],
        relative_path=relative_path,
        file_name=file.name,
        issue_type=issue_type,
        severity=severity,
        message=message,
        suggestion=suggestion,
    )


def _is_cover_file(value: str) -> bool:
    return value in {"cover", "capa"} or value.startswith(("cover ", "capa "))


def _has_range_marker(value: str) -> bool:
    return bool(re.search(r"\d+\s*(?:ao|a|=|_)\s*\d+", value))


def _looks_like_unknown_chapter(filename: str) -> bool:
    value = filename.casefold()
    if not re.search(r"\b(cap|capitulo|capítulo)\b", value):
        return False
    return bool(re.search(r"\d+\s*(?:ao|a|=|_)\s*\d+", value))


def _issue_warnings(issues) -> tuple[FlowWarning, ...]:
    if not issues:
        return ()
    return (
        FlowWarning(
            "Obra possui arquivos de capítulos para revisão.",
            code="LIBRARY_ITEM_CHAPTER_ISSUES",
            details={"count": len(issues)},
        ),
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
        "count_status": "Revisar" if item.metrics.get("chapterIssues") else "OK",
        "path": item.destination_path or item.source_path,
    }

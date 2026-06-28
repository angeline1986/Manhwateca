import shutil
import unicodedata
import uuid
from dataclasses import replace
from pathlib import Path

from manhwateca.file_normalizer import conflicts as file_conflicts
from manhwateca.file_normalizer import planner as file_planner
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
from manhwateca.library_organizer.planning import (
    build_plan as build_folder_plan,
    detect_conflicts as detect_folder_conflicts,
)
from manhwateca.shared.paths import get_required_path_env
from manhwateca.shared.titles import get_canonical_manga_name

from manhwateca.flows.integrations import (
    FileNormalizationItem,
    FileNormalizationPlan,
)


class LocalFileNormalizationIntegration:
    def __init__(self, library_root: Path | str | None = None):
        self.library_root = Path(library_root).expanduser() if library_root else None

    def generate_preview(self, execution_id: str) -> FileNormalizationPlan:
        root = self._root().resolve()
        items = [
            *self._file_items(root),
            *self._folder_items(root),
        ]
        conflicts = sum(1 for item in items if item.status == "conflict")
        status = "blocked" if conflicts else "ready"
        return FileNormalizationPlan(
            execution_id=execution_id,
            status=status,
            items=tuple(items),
            total_conflicts=conflicts,
        )

    def validate_plan(self, plan: FileNormalizationPlan) -> FileNormalizationPlan:
        root = self._root().resolve()
        items = tuple(self._validate_item(item, root) for item in plan.items)
        conflicts = sum(1 for item in items if item.status == "conflict")
        errors = sum(1 for item in items if item.status == "failed")
        status = "blocked" if conflicts or errors else "ready"
        return replace(
            plan,
            status=status,
            items=items,
            total_conflicts=conflicts,
            total_errors=errors,
        )

    def apply_plan(self, plan: FileNormalizationPlan) -> FileNormalizationPlan:
        validated = self.validate_plan(plan)
        if validated.status != "ready":
            return validated

        root = self._root().resolve()
        applied = []
        for item in validated.items:
            if item.status != "ready":
                applied.append(item)
                continue
            applied.append(self._apply_item(item, root))

        errors = sum(1 for item in applied if item.status == "failed")
        applied_count = sum(1 for item in applied if item.status == "applied")
        if errors and applied_count:
            status = "partially_applied"
        elif errors:
            status = "failed"
        else:
            status = "applied"
        return replace(
            validated,
            status=status,
            items=tuple(applied),
            total_errors=errors,
            error_message="Falhas ao aplicar padronização." if errors else None,
        )

    def _file_items(self, root: Path) -> list[FileNormalizationItem]:
        plan = file_planner.build_plan(root, get_canonical_manga_name)
        conflicts = file_conflicts.detect_conflicts(plan)
        conflicted_paths = {
            item["old_path"]
            for conflict in conflicts
            for item in conflict["files"]
        }
        items = []
        for _group, mangas in plan.items():
            for manga_name, files in mangas.items():
                for file_item in files:
                    status = (
                        "conflict"
                        if file_item["old_path"] in conflicted_paths
                        else "ready"
                    )
                    items.append(FileNormalizationItem(
                        work_title=manga_name,
                        original_path=file_item["old_path"],
                        proposed_path=file_item["new_path"],
                        operation="rename_file",
                        status=status,
                        severity="warning" if status == "conflict" else "info",
                        message=(
                            "Conflito de destino detectado."
                            if status == "conflict"
                            else "Arquivo será renomeado."
                        ),
                        details={
                            "kind": file_item.get("kind"),
                            "oldName": file_item.get("old_name"),
                            "newName": file_item.get("new_name"),
                        },
                    ))
        return items

    def _folder_items(self, root: Path) -> list[FileNormalizationItem]:
        manga_folders = find_manga_folders(
            root,
            is_group_folder,
            lambda path: is_manga_folder(path, is_group_folder, is_legacy_container),
        )
        find_empty_legacy_folders(root, is_legacy_container)
        plan = build_folder_plan(
            manga_folders,
            root,
            get_group,
            lambda path: get_current_group(path, root),
        )
        conflicts = detect_folder_conflicts(plan)
        conflicted_sources = {
            str(item["source"])
            for conflict in conflicts
            for item in conflict["items"]
        }
        items = []
        for item in plan:
            if item["is_correct"]:
                continue
            source = str(item["source"])
            status = "conflict" if source in conflicted_sources else "ready"
            items.append(FileNormalizationItem(
                work_title=item["name"],
                original_path=source,
                proposed_path=str(item["destination"]),
                operation="move_folder",
                status=status,
                severity="warning" if status == "conflict" else "info",
                message=(
                    "Conflito de destino detectado."
                    if status == "conflict"
                    else "Pasta será movida para o grupo correto."
                ),
                details={
                    "group": item.get("group"),
                    "currentGroup": item.get("current_group"),
                },
            ))
        return items

    def _validate_item(
        self,
        item: FileNormalizationItem,
        root: Path,
    ) -> FileNormalizationItem:
        if item.status == "conflict":
            return item
        source = Path(item.original_path).resolve()
        destination = Path(item.proposed_path).resolve()
        if not _inside(source, root) or not _inside(destination, root):
            return replace(
                item,
                status="failed",
                severity="error",
                message="Caminho fora da biblioteca.",
            )
        if not source.exists():
            return replace(
                item,
                status="failed",
                severity="error",
                message="Origem não existe mais. Gere um novo preview.",
            )
        if destination.exists() and not _same_path(source, destination):
            return replace(
                item,
                status="conflict",
                severity="warning",
                message="Destino já existe. Aplicação bloqueada.",
            )
        return item

    def _apply_item(
        self,
        item: FileNormalizationItem,
        root: Path,
    ) -> FileNormalizationItem:
        source = Path(item.original_path).resolve()
        destination = Path(item.proposed_path).resolve()
        try:
            if item.operation == "move_folder":
                destination.parent.mkdir(parents=True, exist_ok=True)
                _move(source, destination)
            else:
                _rename(source, destination)
        except OSError as error:
            return replace(
                item,
                status="failed",
                severity="error",
                message=f"Falha ao aplicar: {error}",
            )
        return replace(
            item,
            status="applied",
            severity="info",
            message="Padronização aplicada.",
        )

    def _root(self) -> Path:
        return self.library_root or get_required_path_env("MANGA_ROOT")


class FileNormalizationService:
    def __init__(self, repository, integration):
        self.repository = repository
        self.integration = integration

    def generate_preview(self) -> FileNormalizationPlan:
        execution = self.repository.latest_execution()
        if execution is None or execution.execution_id is None:
            raise RuntimeError("Nenhuma execução de Fluxos encontrada.")
        plan = self.integration.generate_preview(execution.execution_id)
        return self.repository.save_normalization_plan(plan)

    def latest(self) -> FileNormalizationPlan | None:
        return self.repository.latest_normalization_plan()

    def apply_latest(self) -> FileNormalizationPlan:
        plan = self.repository.latest_normalization_plan()
        if plan is None:
            raise RuntimeError("Nenhum preview de padronização encontrado.")
        if plan.status != "ready":
            raise RuntimeError("Preview de padronização não está pronto para aplicar.")
        applied = self.integration.apply_plan(plan)
        return self.repository.update_normalization_plan(applied)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _same_path(source: Path, destination: Path) -> bool:
    try:
        return source.samefile(destination)
    except FileNotFoundError:
        return False


def _equivalent_name(source: Path, destination: Path) -> bool:
    return (
        source.parent == destination.parent
        and unicodedata.normalize("NFC", source.name).casefold()
        == unicodedata.normalize("NFC", destination.name).casefold()
    )


def _rename(source: Path, destination: Path) -> None:
    if _equivalent_name(source, destination):
        temporary = source.with_name(
            f"manhwateca-temp-{uuid.uuid4().hex}{source.suffix}"
        )
        source.rename(temporary)
        temporary.rename(destination)
    else:
        source.rename(destination)


def _move(source: Path, destination: Path) -> None:
    if _equivalent_name(source, destination):
        temporary = source.with_name(f"manhwateca-temp-{uuid.uuid4().hex}")
        source.rename(temporary)
        temporary.rename(destination)
    else:
        shutil.move(str(source), str(destination))

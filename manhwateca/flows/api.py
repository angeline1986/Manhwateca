from datetime import datetime
from typing import Any

from manhwateca.flows.domain import (
    OFFICIAL_STAGE_DEFINITIONS,
    FlowError,
    FlowWarning,
    StageExecution,
    StageId,
    WorkflowExecution,
)
from manhwateca.flows.integrations import FlowIntegrations, IntegrationCheck
from manhwateca.flows.legacy_adapter import LegacyWorkflowAdapter


class FlowController:
    def __init__(self, backend, integrations: FlowIntegrations | None = None):
        self.backend = backend
        self.integrations = integrations

    @classmethod
    def from_project(
        cls,
        project_root,
        *,
        backend=None,
        integrations=None,
        legacy_manager=None,
    ):
        return cls(
            backend or LegacyWorkflowAdapter(project_root, manager=legacy_manager),
            integrations=integrations,
        )

    def handle_get(self, path: str):
        if path == "/api/flows/status":
            return self._ok({"execution": self._current_execution()})
        if path == "/api/flows/history":
            return self._ok({"history": self._history()})
        if path == "/api/flows/integrations":
            return self._ok({"integrations": self._integrations_status()})
        return None

    def handle_post(self, path: str, payload: dict[str, Any]):
        if path == "/api/flows/start":
            return self._run(lambda: self.backend.start(), status=202)
        if path == "/api/flows/cancel":
            return self._run(self._cancel, status=202)
        prefix = "/api/flows/stages/"
        suffix = "/run"
        if path.startswith(prefix) and path.endswith(suffix):
            stage_slug = path.removeprefix(prefix).removesuffix(suffix)
            return self._run(lambda: self._run_stage(stage_slug), status=202)
        return None

    def _current_execution(self):
        if hasattr(self.backend, "get_status"):
            return _execution_to_dict(self.backend.get_status())
        return _execution_to_dict(self.backend.status())

    def _history(self):
        if hasattr(self.backend, "list_history"):
            return [
                _execution_to_dict(execution)
                for execution in self.backend.list_history()
            ]
        current = self._current_execution()
        return [current] if current else []

    def _integrations_status(self):
        if self.integrations is None:
            return [
                {
                    "id": item,
                    "name": item,
                    "status": "unknown",
                    "available": False,
                    "message": "Integração ainda não conectada à API oficial.",
                    "warnings": [],
                    "errors": [],
                    "details": {},
                }
                for item in ("database", "library", "mangaupdates", "notion")
            ]
        checks = (
            ("database", self.integrations.database.check_status()),
            ("library", self.integrations.library.check_status()),
            ("mangaupdates", self.integrations.mangaupdates.check_status()),
            ("notion", self.integrations.notion.check_status()),
        )
        return [_integration_to_dict(identifier, check) for identifier, check in checks]

    def _run_stage(self, stage_slug: str):
        try:
            stage = StageId(stage_slug)
        except ValueError as error:
            raise ValueError("Etapa de Fluxos inválida.") from error
        if hasattr(self.backend, "run_stage"):
            return self.backend.run_stage(stage)
        return self.backend.start(stage=stage)

    def _cancel(self):
        if not hasattr(self.backend, "cancel"):
            raise NotImplementedError("Cancelamento ainda não disponível neste backend.")
        return self.backend.cancel()

    def _run(self, callback, *, status: int):
        try:
            execution = callback()
        except ValueError as error:
            return self._error(str(error), status=400)
        except NotImplementedError as error:
            return self._error(str(error), status=501)
        except RuntimeError as error:
            return self._error(str(error), status=409)
        return self._ok({"execution": _execution_to_dict(execution)}, status=status)

    def _ok(self, data, *, status=200):
        return {
            "success": True,
            "timestamp": _now(),
            "data": data,
            "errors": [],
            "warnings": [],
        }, status

    def _error(self, message: str, *, status: int):
        return {
            "success": False,
            "timestamp": _now(),
            "data": None,
            "errors": [{"message": message}],
            "warnings": [],
        }, status


def _execution_to_dict(execution: WorkflowExecution | None):
    if execution is None:
        return None
    return {
        "id": execution.execution_id,
        "status": execution.status.value,
        "startedAt": execution.started_at,
        "finishedAt": execution.finished_at,
        "progress": execution.progress.to_dict(),
        "currentStage": (
            execution.current_stage.stage_id.value
            if execution.current_stage else None
        ),
        "stages": [_stage_to_dict(stage) for stage in execution.stages],
        "warnings": [_message_to_dict(warning) for warning in execution.warnings],
        "errors": [_message_to_dict(error) for error in execution.errors],
        "definitions": [
            definition.to_dict()
            for definition in OFFICIAL_STAGE_DEFINITIONS
        ],
    }


def _stage_to_dict(stage: StageExecution):
    result = stage.result
    return {
        "id": stage.stage_id.value,
        "status": stage.status.value,
        "progress": stage.progress.to_dict(),
        "currentItem": stage.current_item,
        "startedAt": stage.started_at,
        "finishedAt": stage.finished_at,
        "messages": [_message_to_dict(message) for message in stage.messages],
        "result": {
            "processed": result.processed if result else 0,
            "skipped": result.skipped if result else 0,
            "metrics": result.metrics if result else {},
            "warnings": (
                [_message_to_dict(warning) for warning in result.warnings]
                if result else []
            ),
            "errors": (
                [_message_to_dict(error) for error in result.errors]
                if result else []
            ),
        },
    }


def _integration_to_dict(identifier: str, check: IntegrationCheck):
    return {
        "id": identifier,
        "name": check.name,
        "status": check.status.value,
        "available": check.available,
        "message": check.message,
        "warnings": [_message_to_dict(warning) for warning in check.warnings],
        "errors": [_message_to_dict(error) for error in check.errors],
        "details": check.details,
    }


def _message_to_dict(message: FlowError | FlowWarning):
    return {
        "code": message.code,
        "message": message.message,
        "details": message.details,
    }


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")

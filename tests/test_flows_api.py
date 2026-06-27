import unittest

from manhwateca.flows.api import FlowController
from manhwateca.flows.domain import (
    FlowError,
    FlowWarning,
    StageExecution,
    StageId,
    StageStatus,
    WorkflowExecution,
    WorkflowStatus,
)
from manhwateca.flows.integrations import (
    FlowIntegrations,
    IntegrationCheck,
    IntegrationStatus,
)


class FlowControllerTests(unittest.TestCase):
    def test_status_uses_official_response_shape(self):
        controller = FlowController(FakeBackend())

        payload, status = controller.handle_get("/api/flows/status")

        self.assertEqual(200, status)
        self.assertTrue(payload["success"])
        self.assertIn("timestamp", payload)
        self.assertEqual([], payload["errors"])
        self.assertEqual([], payload["warnings"])
        execution = payload["data"]["execution"]
        self.assertEqual("wf_1", execution["id"])
        self.assertEqual("running", execution["status"])
        self.assertEqual("organize_library", execution["currentStage"])
        self.assertEqual("organize_library", execution["stages"][0]["id"])
        self.assertEqual("running", execution["stages"][0]["status"])
        self.assertTrue(execution["definitions"])

    def test_start_delegates_to_backend(self):
        backend = FakeBackend()
        controller = FlowController(backend)

        payload, status = controller.handle_post("/api/flows/start", {})

        self.assertEqual(202, status)
        self.assertEqual(["start"], backend.calls)
        self.assertEqual("running", payload["data"]["execution"]["status"])

    def test_run_stage_delegates_to_backend_with_stage_id(self):
        backend = FakeBackend()
        controller = FlowController(backend)

        payload, status = controller.handle_post(
            "/api/flows/stages/resolve_ids/run",
            {},
        )

        self.assertEqual(202, status)
        self.assertEqual(("run_stage", StageId.RESOLVE_IDS), backend.calls[-1])
        self.assertEqual("running", payload["data"]["execution"]["status"])

    def test_invalid_stage_returns_bad_request(self):
        controller = FlowController(FakeBackend())

        payload, status = controller.handle_post(
            "/api/flows/stages/invented/run",
            {},
        )

        self.assertEqual(400, status)
        self.assertFalse(payload["success"])
        self.assertEqual("Etapa de Fluxos inválida.", payload["errors"][0]["message"])

    def test_cancel_delegates_to_backend(self):
        backend = FakeBackend()
        controller = FlowController(backend)

        payload, status = controller.handle_post("/api/flows/cancel", {})

        self.assertEqual(202, status)
        self.assertEqual("cancelled", payload["data"]["execution"]["status"])
        self.assertEqual(["cancel"], backend.calls)

    def test_history_returns_serialized_executions(self):
        controller = FlowController(FakeBackend())

        payload, status = controller.handle_get("/api/flows/history")

        self.assertEqual(200, status)
        self.assertEqual("wf_1", payload["data"]["history"][0]["id"])

    def test_integrations_returns_checks(self):
        controller = FlowController(
            FakeBackend(),
            integrations=FlowIntegrations(
                database=FakeIntegration("PostgreSQL"),
                library=FakeIntegration("Biblioteca"),
                mangaupdates=FakeIntegration("MangaUpdates"),
                notion=FakeIntegration("Notion"),
            ),
        )

        payload, status = controller.handle_get("/api/flows/integrations")

        self.assertEqual(200, status)
        self.assertEqual(
            ["database", "library", "mangaupdates", "notion"],
            [item["id"] for item in payload["data"]["integrations"]],
        )
        self.assertTrue(all(
            item["status"] == "operational"
            for item in payload["data"]["integrations"]
        ))

    def test_from_project_uses_official_backend_by_default(self):
        controller = FlowController.from_project("/tmp")

        self.assertTrue(hasattr(controller.backend, "get_status"))
        self.assertTrue(hasattr(controller.backend, "list_history"))
        self.assertTrue(hasattr(controller.backend, "run_stage"))


class FakeBackend:
    def __init__(self):
        self.calls = []

    def get_status(self):
        return _execution(WorkflowStatus.RUNNING)

    def start(self):
        self.calls.append("start")
        return _execution(WorkflowStatus.RUNNING)

    def run_stage(self, stage):
        self.calls.append(("run_stage", stage))
        return _execution(WorkflowStatus.RUNNING)

    def cancel(self):
        self.calls.append("cancel")
        return _execution(WorkflowStatus.CANCELLED)

    def list_history(self):
        return [_execution(WorkflowStatus.COMPLETED)]


class FakeIntegration:
    def __init__(self, name):
        self.name = name

    def check_status(self):
        return IntegrationCheck(
            self.name,
            IntegrationStatus.OPERATIONAL,
        )


def _execution(status):
    return WorkflowExecution(
        execution_id="wf_1",
        status=status,
        started_at="2026-06-27T10:00:00-03:00",
        finished_at=(
            "2026-06-27T10:05:00-03:00"
            if status != WorkflowStatus.RUNNING
            else None
        ),
        warnings=(FlowWarning("Alerta global."),),
        errors=(
            (FlowError("Falha global."),)
            if status == WorkflowStatus.FAILED
            else ()
        ),
        stages=(
            StageExecution(
                StageId.ORGANIZE_LIBRARY,
                status=(
                    StageStatus.RUNNING
                    if status == WorkflowStatus.RUNNING
                    else StageStatus.COMPLETED
                ),
                started_at="2026-06-27T10:01:00-03:00",
            ),
        ),
    )


if __name__ == "__main__":
    unittest.main()

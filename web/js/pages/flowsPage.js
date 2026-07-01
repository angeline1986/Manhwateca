import {
  cancelWorkflowRun,
  getFlowStatus,
  getFlowsState,
  runFlowStage,
  startWorkflow as startFlowWorkflow,
} from "../api/flowsApi.js";
import { getMangaUpdatesWorks, getReviewItems } from "../api/mangaupdatesApi.js";
import {
  applySelectedDecisions,
  selectCandidate,
  selectManualId,
} from "../flows/flowDecisionHandlers.js";
import { ACTIVE_FLOW_STEPS, FLOW_STAGE_GROUPS } from "../flows/flowConstants.js";
import {
  currentFlowStage,
  normalizeFlowsPayload,
  withOptimisticStage,
} from "../flows/flowModel.js";
import { renderFlowsOverview } from "../flows/flowRenderer.js";

export { normalizeFlowsPayload } from "../flows/flowModel.js";
export { FLOW_STAGE_GROUPS } from "../flows/flowConstants.js";

export function initFlowsPage(elements, options = {}) {
  let workflowState;
  let workflowTimer;
  let pendingRequest = false;
  let activeSubtab = "buscar";
  let worksPage = 1;
  let reviewState = { summary: {}, items: [] };
  let selectedDecisions = {};
  let worksState = { kpis: {}, items: [], pagination: {} };
  const showPage = options.showPage || (() => {});

  async function loadWorkflow() {
    const [data] = await Promise.all([
      loadFlowsApiState({ includeDetails: true }),
      loadReviewState(),
      loadWorksState(),
    ]);
    renderWorkflow(data);
    scheduleWorkflowPolling(data);
  }

  async function pollWorkflowStatus() {
    const data = await loadFlowsApiState({ includeDetails: false });
    if (flowChanged(data)) renderWorkflow(data);
    else workflowState = data;
    scheduleWorkflowPolling(data);
  }

  function stopWorkflowPolling() {
    clearTimeout(workflowTimer);
  }

  function scheduleWorkflowPolling(data) {
    clearTimeout(workflowTimer);
    if (data.run.status !== "running" && !pendingRequest) return;
    workflowTimer = setTimeout(pollWorkflowStatus, 1000);
  }

  async function loadFlowsApiState({ includeDetails }) {
    if (!includeDetails) {
      const status = await getFlowStatus();
      return withDetails(normalizeFlowsPayload(status.payload));
    }
    const flowState = await getFlowsState();
    return withDetails(normalizeFlowsPayload(flowState.status), flowState);
  }

  function withDetails(data, flowState = {}) {
    data.integrations = flowState.integrations?.data?.integrations
      || workflowState?.integrations
      || [];
    data.history = flowState.history?.data?.history || workflowState?.history || [];
    return data;
  }

  async function loadReviewState() {
    try {
      const { payload } = await getReviewItems();
      reviewState = { summary: payload.summary || {}, items: payload.items || [] };
    } catch {
      reviewState = { summary: {}, items: [] };
    }
  }

  async function loadWorksState() {
    try {
      const { payload } = await getMangaUpdatesWorks({
        status: "WITHOUT_ID",
        page: String(worksPage),
        pageSize: "5",
      });
      worksState = payload.data || { kpis: {}, items: [], pagination: {} };
    } catch {
      worksState = { kpis: {}, items: [], pagination: {} };
    }
  }

  function renderWorkflow(data) {
    workflowState = data;
    renderFlowsOverview(elements, data, {
      activeSubtab,
      review: reviewState,
      selectedDecisions,
      works: worksState,
    });
    renderLegacyWorkflow(data);
  }

  function flowChanged(data) {
    return JSON.stringify(data.run || {}) !== JSON.stringify(workflowState?.run || {});
  }

  function renderLegacyWorkflow(data) {
    if (elements.workflowSteps) {
      elements.workflowSteps.innerHTML = data.steps.map(step =>
        `<label><input type="checkbox" value="${step.id}" checked> ${step.label}</label>`
      ).join("");
    }
    if (elements.workflowNotice) elements.workflowNotice.textContent = data.run.notification || "Fluxo carregado.";
    if (elements.startWorkflow) elements.startWorkflow.disabled = data.run.status === "running";
  }

  async function runWorkflow(resume = false) {
    const selected = workflowState?.steps?.length
      ? workflowState.steps.map(step => step.id).filter(step => ACTIVE_FLOW_STEPS.includes(step))
      : ACTIVE_FLOW_STEPS;
    const { response, payload } = await startFlowWorkflow({ selected, resume });
    setFeedback(response.ok ? "Fluxo iniciado." : errorMessage(payload), response.ok ? "success" : "error");
    if (response.ok) renderWorkflow(normalizeFlowsPayload(payload));
    await loadWorkflow();
  }

  async function runCurrentFlowStage() {
    const run = workflowState?.run || { status: "idle", results: {} };
    const stage = selectedFlowStage(run);
    if (!stage || pendingRequest) return;
    if (stage.id === "resolve_ids" && activeSubtab !== "buscar") {
      showPage("mangaupdates");
      return;
    }
    pendingRequest = true;
    setFeedback(`Solicitando execução de ${stage.title}. Aguarde...`, "info");
    renderWorkflow(withOptimisticStage(workflowState, stage.id));
    try {
      const { response, payload } = await runFlowStage(stage.id);
      setFeedback(response.ok ? `${stage.title} finalizada.` : errorMessage(payload), response.ok ? "success" : "error");
      await loadWorkflow();
    } catch (error) {
      setFeedback(`Falha ao solicitar ${stage.title}: ${error.message || "erro desconhecido"}.`, "error");
      await loadWorkflow();
    } finally {
      pendingRequest = false;
    }
  }

  async function cancelWorkflow() {
    const { response, payload } = await cancelWorkflowRun();
    setFeedback(response.ok ? "Cancelamento solicitado." : errorMessage(payload), response.ok ? "success" : "error");
    await loadWorkflow();
  }

  function setFeedback(message, tone = "success") {
    const className = `flow-feedback flow-feedback--${tone}`;
    for (const target of [elements.workflowFeedback, elements.flowsFeedback]) {
      if (!target) continue;
      target.textContent = message;
      target.className = className;
    }
  }

  function errorMessage(payload) {
    return payload?.errors?.[0]?.message || payload?.error || "Não foi possível executar.";
  }

  function selectedFlowStage(run) {
    return FLOW_STAGE_GROUPS.find(group => group.id === activeSubtab) || currentFlowStage(run);
  }

  elements.startWorkflow?.addEventListener("click", () => runWorkflow(false));
  elements.resumeWorkflow?.addEventListener("click", () => runWorkflow(true));
  elements.flowsStartWorkflow?.addEventListener("click", () => runCurrentFlowStage());
  elements.flowsResumeWorkflow?.addEventListener("click", () => runWorkflow(true));

  for (const area of [elements.flowsCurrentActions, elements.flowsCurrentCards]) {
    area?.addEventListener("click", event => {
      const subtab = event.target.closest("[data-flow-subtab]");
      if (subtab) {
        activeSubtab = subtab.dataset.flowSubtab;
        renderWorkflow(workflowState);
        return;
      }
      const worksPageAction = event.target.closest("[data-flow-works-page]");
      if (worksPageAction) {
        worksPage = Number(worksPageAction.dataset.flowWorksPage || 1);
        loadWorkflow();
        return;
      }
      const selectedCandidate = event.target.closest("[data-flow-select-id]");
      if (selectedCandidate) {
        selectedDecisions = selectCandidate(selectedDecisions, selectedCandidate);
        setFeedback("Decisão marcada para aplicação.", "info");
        renderWorkflow(workflowState);
        return;
      }
      const manualDecision = event.target.closest("[data-flow-manual-work]");
      if (manualDecision) {
        const result = selectManualId(selectedDecisions, manualDecision, area);
        if (result.error) setFeedback(result.error, "error");
        else {
          selectedDecisions = result.selectedDecisions;
          setFeedback("ID manual marcado para aplicação.", "info");
          renderWorkflow(workflowState);
        }
        return;
      }
      if (event.target.closest("[data-flow-apply-decisions]")) {
        applySelectedDecisions(selectedDecisions, { errorMessage, reload: loadWorkflow, setFeedback })
          .then(updated => { selectedDecisions = updated; });
        return;
      }
      if (event.target.closest("[data-page]")) {
        showPage(event.target.closest("[data-page]").dataset.page);
        return;
      }
      if (event.target.closest("[data-flow-cancel]")) {
        cancelWorkflow();
        return;
      }
      if (event.target.closest("[data-flow-refresh]")) {
        loadWorkflow();
        return;
      }
      if (event.target.closest("[data-flow-run-stage], [data-flow-start]")) {
        runCurrentFlowStage();
      }
    });
  }

  return { loadWorkflow, stopWorkflowPolling };
}

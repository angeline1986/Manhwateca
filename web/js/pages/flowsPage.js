import {
  cancelWorkflowRun,
  getFlowStatus,
  getFlowsState,
  runFlowStage,
  startWorkflow as startFlowWorkflow,
} from "../api/flowsApi.js";
import { ACTIVE_FLOW_STEPS, FLOW_STAGE_GROUPS } from "../flows/flowConstants.js";
import {
  loadMetadataState as fetchMetadataState,
  loadReviewState as fetchReviewState,
  loadWorksState as fetchWorksState,
} from "../flows/flowPageData.js";
import { handleFlowsChange, handleFlowsClick } from "../flows/flowsClickHandler.js";
import {
  currentFlowStage,
  normalizeFlowsPayload,
  withOptimisticStage,
} from "../flows/flowModel.js";
import { renderFlowsOverview } from "../flows/flowRenderer.js";

export function initFlowsPage(elements, options = {}) {
  let workflowState;
  let workflowTimer;
  let pendingRequest = false;
  let activeSubtab = "buscar";
  let worksPage = 1;
  let activeReviewKey = "";
  let showResolvedReview = false;
  let reviewState = { summary: {}, items: [] };
  let selectedDecisions = {};
  let savedReviewKeys = new Set();
  let worksState = { kpis: {}, items: [], pagination: {} };
  let metadataState = { kpis: {}, items: [], pagination: {} };
  const showPage = options.showPage || (() => {});

  async function loadWorkflow() {
    const [data] = await Promise.all([
      loadFlowsApiState({ includeDetails: true }),
      refreshReviewState(),
      refreshWorksState(),
      refreshMetadataState(),
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

  function stopWorkflowPolling() { clearTimeout(workflowTimer); }

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
    data.integrations = flowState.integrations?.data?.integrations || workflowState?.integrations || [];
    data.history = flowState.history?.data?.history || workflowState?.history || [];
    return data;
  }

  async function refreshReviewState() { reviewState = await fetchReviewState(); }
  async function refreshWorksState() { worksState = await fetchWorksState(worksPage); }
  async function refreshMetadataState() { metadataState = await fetchMetadataState(); }

  function renderWorkflow(data) {
    workflowState = data;
    renderFlowsOverview(elements, data, {
      activeSubtab,
      activeReviewKey,
      showResolvedReview,
      review: reviewState,
      selectedDecisions: activeSubtab === "decisoes" ? readyDecisions() : selectedDecisions,
      savedReviewKeys: [...savedReviewKeys],
      metadata: metadataState,
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

  async function refreshAfterStage(stageId) {
    const maxAttempts = stageId === "update_metadata" ? 60 : 2;
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      if (attempt > 0) await new Promise(resolve => setTimeout(resolve, 800));
      const data = await loadFlowsApiState({ includeDetails: false });
      renderWorkflow(data);
      const run = data?.run || { status: "idle", results: {} };
      const stageResult = run.results?.[stageId];
      const completed = stageResult
        ? stageResult.status === "completed" || stageResult.status === "completed_with_warnings"
        : run.status !== "running";
      if (completed) break;
    }
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
    const payload = stage.id === "update_metadata"
      ? { selected_ids: selectedMetadataWorkIds() }
      : {};
    const metadataSelectionCount = payload.selected_ids?.length || 0;
    pendingRequest = true;
    setFeedback(stage.id === "update_metadata"
      ? metadataRunningMessage(metadataSelectionCount)
      : `Solicitando execução de ${stage.title}. Aguarde...`, "info");
    renderWorkflow(withOptimisticStage(workflowState, stage.id));
    try {
      const { response, payload: responsePayload } = await runFlowStage(stage.id, payload);
      if (response.ok) {
        setFeedback(stage.id === "update_metadata"
          ? metadataRunningMessage(metadataSelectionCount)
          : `${stage.title} em execução. Aguarde...`, "info");
        await refreshAfterStage(stage.id);
        setFeedback(stage.id === "update_metadata"
          ? metadataSuccessMessage(metadataSelectionCount)
          : `${stage.title} finalizada.`, "success");
      } else {
        setFeedback(errorMessage(responsePayload), "error");
        await loadWorkflow();
      }
    } catch (error) {
      setFeedback(`Falha ao solicitar ${stage.title}: ${error.message || "erro desconhecido"}.`, "error");
      await loadWorkflow();
    } finally {
      pendingRequest = false;
    }
  }

  function metadataRunningMessage(count) {
    return count > 0
      ? `🔄 Sincronizando ${selectedLabel(count, "obra", "obras")}...`
      : "🔄 Sincronizando metadados...";
  }

  function metadataSuccessMessage(count) {
    return count > 0
      ? `✅ ${selectedLabel(count, "obra sincronizada", "obras sincronizadas")} com sucesso.`
      : "✅ Metadados atualizados com sucesso.";
  }

  function selectedLabel(count, singular, plural) {
    return `${count} ${count === 1 ? singular : plural}`;
  }

  function selectedMetadataWorkIds() {
    const area = elements.flowsCurrentCards;
    if (!area) return [];
    return [...area.querySelectorAll("[data-metadata-choice]:checked")]
      .map(input => Number(input.dataset.metadataWorkId))
      .filter(value => Number.isFinite(value) && value > 0);
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
    return (
      payload?.errors?.[0]?.message
      || payload?.error
      || payload?.rejected?.[0]
      || payload?.validation?.blocks?.[0]?.reason
      || "Não foi possível executar."
    );
  }

  function selectedFlowStage(run) { return FLOW_STAGE_GROUPS.find(group => group.id === activeSubtab) || currentFlowStage(run); }

  function setActiveSubtab(subtab) {
    activeSubtab = subtab || "buscar";
    if (activeSubtab === "pendencias") showResolvedReview = false; if (activeSubtab === "decisoes") setFeedback("");
    renderWorkflow(workflowState);
  }

  function itemKey(item) {
    return item.queueId || item.nome_decisao || item.localTitle || item.nome || "obra";
  }

  function readyDecisions() {
    return Object.fromEntries(Object.entries(selectedDecisions).filter(([key]) => savedReviewKeys.has(key)));
  }

  function nextPendingKey(currentKey) {
    const pending = (reviewState.items || [])
      .map(itemKey)
      .filter(key => key !== currentKey && !savedReviewKeys.has(key));
    return pending[0] || "";
  }

  function saveCurrentReviewDecision() {
    const key = activeReviewKey || itemKey(reviewState.items?.[0] || {});
    if (!selectedDecisions[key]) {
      setFeedback("Escolha um candidato ou informe um ID antes de salvar.", "error");
      return;
    }
    savedReviewKeys.add(key);
    activeReviewKey = nextPendingKey(key);
    showResolvedReview = false;
    setFeedback(activeReviewKey ? "Decisão salva. Próxima pendência selecionada." : "Revisão concluída.", "success");
    renderWorkflow(workflowState);
  }

  function reviewAgain() {
    showResolvedReview = true; activeReviewKey = itemKey(reviewState.items?.[0] || {});
    renderWorkflow(workflowState);
  }

  function afterApply(updatedDecisions) {
    selectedDecisions = updatedDecisions;
    if (!Object.keys(updatedDecisions).length) savedReviewKeys = new Set(); renderWorkflow(workflowState);
  }

  elements.startWorkflow?.addEventListener("click", () => runWorkflow(false));
  elements.resumeWorkflow?.addEventListener("click", () => runWorkflow(true));
  elements.flowsStartWorkflow?.addEventListener("click", () => runCurrentFlowStage());
  elements.flowsResumeWorkflow?.addEventListener("click", () => runWorkflow(true));

  window.addEventListener("manhwateca:flow-subtab", event => setActiveSubtab(event.detail?.subtab));

  const area = elements.flowsCurrentCards;
  area?.addEventListener("click", event => handleFlowsClick(event, {
    area,
    afterApply,
    cancelWorkflow,
    errorMessage,
    getSelectedDecisions: () => selectedDecisions,
    loadWorkflow,
    readyDecisions,
    renderWorkflow: () => renderWorkflow(workflowState),
    reviewAgain,
    runCurrentFlowStage,
    saveCurrentReviewDecision,
    setActiveReviewKey: value => { activeReviewKey = value; },
    setActiveSubtab,
    setFeedback,
    setSelectedDecisions: value => { selectedDecisions = value; },
    setWorksPage: value => { worksPage = value; },
    showPage,
  }));
  area?.addEventListener("change", event => handleFlowsChange(event, area));

  return { loadWorkflow, stopWorkflowPolling };
}

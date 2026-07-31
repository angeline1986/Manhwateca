import {
  cancelWorkflowRun,
  getFlowStatus,
  getFlowsState,
  runFlowStage,
  startWorkflow as startFlowWorkflow,
} from "../api/flowsApi.js";
import {
  applyConfirmedMangaUpdatesIdCorrection,
  getConfirmedMangaUpdatesIdCandidates,
  previewConfirmedMangaUpdatesIdCorrection,
} from "../api/mangaupdatesApi.js";
import { ACTIVE_FLOW_STEPS, FLOW_STAGE_GROUPS } from "../flows/flowConstants.js";
import {
  loadMetadataState as fetchMetadataState,
  loadNotionMetadataState as fetchNotionMetadataState,
  loadReviewState as fetchReviewState,
  loadWorksState as fetchWorksState,
} from "../flows/flowPageData.js";
import {
  handleFlowsChange,
  handleFlowsClick,
  handleFlowsInput,
} from "../flows/flowsClickHandler.js";
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
  let reviewSearchQuery = "";
  let showResolvedReview = false;
  let confirmedIdCorrection = {
    search: "",
    candidates: [],
    selectedWork: null,
    newWorkCode: "",
    preview: null,
    error: "",
    page: 1,
  };
  let confirmedIdSearchSequence = 0;
  let reviewState = { summary: {}, items: [] };
  let selectedDecisions = {};
  let savedReviewKeys = new Set();
  let worksState = { kpis: {}, items: [], pagination: {} };
  let metadataState = { kpis: {}, items: [], pagination: {} };
  let notionMetadataState = {};
  let recentlySyncedNotionWorkIds = [];
  const showPage = options.showPage || (() => {});

  async function loadWorkflow() {
    const [data] = await Promise.all([
      loadFlowsApiState({ includeDetails: true }),
      refreshReviewState(),
      refreshWorksState(),
      refreshMetadataState(),
      refreshNotionMetadataState(),
      refreshConfirmedIdCandidatesState(),
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
  async function refreshNotionMetadataState() { notionMetadataState = await fetchNotionMetadataState(); }
  async function refreshConfirmedIdCandidatesState(search = confirmedIdCorrection.search || "") {
    const { response, payload } = await getConfirmedMangaUpdatesIdCandidates({
      search,
      limit: 25,
    });
    confirmedIdCorrection = {
      ...confirmedIdCorrection,
      search,
      candidates: response.ok ? (payload.items || []) : [],
      candidatesError: response.ok ? "" : errorMessage(payload),
      candidatesLoading: false,
      page: 1,
    };
  }

  function renderWorkflow(data) {
    workflowState = data;
    renderFlowsOverview(elements, data, {
      activeSubtab,
      activeReviewKey,
      showResolvedReview,
      review: reviewState,
      reviewSearchQuery,
      confirmedIdCorrection,
      selectedDecisions: activeSubtab === "decisoes" ? readyDecisions() : selectedDecisions,
      savedReviewKeys: [...savedReviewKeys],
      metadata: metadataState,
      notionMetadata: notionMetadataState,
      recentlySyncedNotionWorkIds,
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
    const maxAttemptsByStage = {
      update_metadata: 60,
      sync_notion: 120,
    };
    const terminalStatuses = new Set([
      "completed",
      "completed_with_warnings",
      "failed",
      "cancelled",
    ]);
    const maxAttempts = maxAttemptsByStage[stageId] || 2;
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      if (attempt > 0) await new Promise(resolve => setTimeout(resolve, 800));
      const data = await loadFlowsApiState({ includeDetails: false });
      renderWorkflow(data);
      const run = data?.run || { status: "idle", results: {} };
      const stageResult = run.results?.[stageId];
      const completed = stageResult
        ? terminalStatuses.has(stageResult.status)
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
    const payload = stagePayload(stage.id);
    const metadataSelectionCount = payload.selected_ids?.length || 0;
    const notionScopeIds = stage.id === "sync_notion" ? notionExecutionScopeIds(payload) : [];
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
        if (stage.id === "sync_notion" && notionStageSynced()) {
          recentlySyncedNotionWorkIds = notionScopeIds;
          renderWorkflow(workflowState);
        }
        const finalFeedback = stageFinalFeedback(stage.id, metadataSelectionCount);
        setFeedback(finalFeedback.message, finalFeedback.tone);
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

  async function createMissingNotionPage(workId) {
    if (!Number.isFinite(workId) || workId <= 0 || pendingRequest) return;
    pendingRequest = true;
    setFeedback("Criando página no Notion...", "info");
    try {
      const response = await fetch("/api/notion/pages/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ work_id: workId }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setFeedback(errorMessage(payload), "error");
        await loadWorkflow();
        return;
      }
      recentlySyncedNotionWorkIds = [workId];
      setFeedback("Página criada no Notion.", "success");
      await loadWorkflow();
    } catch (error) {
      setFeedback(`Falha ao criar página no Notion: ${error.message || "erro desconhecido"}.`, "error");
      await loadWorkflow();
    } finally {
      pendingRequest = false;
    }
  }

  async function previewConfirmedIdCorrection() {
    if (pendingRequest) return;
    const values = confirmedIdCorrectionValues();
    if (!values.workId) {
      confirmedIdCorrection = {
        ...confirmedIdCorrection,
        ...values,
        error: "Selecione uma obra antes de validar o novo ID.",
      };
      renderWorkflow(workflowState);
      return;
    }
    confirmedIdCorrection = {
      ...confirmedIdCorrection,
      ...values,
      preview: null,
      error: "",
      loading: true,
    };
    renderWorkflow(workflowState);
    focusConfirmedIdSearch();
    try {
      const { response, payload } = await previewConfirmedMangaUpdatesIdCorrection({
        work_id: values.workId,
        new_work_code: values.newWorkCode,
      });
      confirmedIdCorrection = {
        ...confirmedIdCorrection,
        ...values,
        preview: response.ok ? payload : null,
        error: response.ok ? "" : errorMessage(payload),
        loading: false,
      };
      setFeedback(
        response.ok ? "ID validado. Revise o preview antes de aplicar." : errorMessage(payload),
        response.ok ? "info" : "error",
      );
    } catch (error) {
      confirmedIdCorrection = {
        ...confirmedIdCorrection,
        ...values,
        preview: null,
        error: `Falha ao validar ID: ${error.message || "erro desconhecido"}.`,
        loading: false,
      };
      setFeedback(confirmedIdCorrection.error, "error");
    }
    renderWorkflow(workflowState);
    focusConfirmedIdSearch();
  }

  function focusConfirmedIdSearch() {
    const input = area?.querySelector("[data-confirmed-id-search]");
    if (!input) return;
    input.focus();
    const cursor = input.value.length;
    input.setSelectionRange(cursor, cursor);
  }

  async function applyConfirmedIdCorrection() {
    if (pendingRequest || !confirmedIdCorrection.preview?.can_apply) return;
    pendingRequest = true;
    const values = confirmedIdCorrectionValues();
    setFeedback("Aplicando correção do ID confirmado...", "info");
    try {
      const { response, payload } = await applyConfirmedMangaUpdatesIdCorrection({
        work_id: values.workId,
        expected_current_work_code: confirmedIdCorrection.preview?.work?.current_work_code,
        new_work_code: values.newWorkCode,
        confirmed: true,
      });
      if (!response.ok) {
        confirmedIdCorrection = {
          ...confirmedIdCorrection,
          ...values,
          preview: null,
          error: errorMessage(payload),
        };
        setFeedback(errorMessage(payload), "error");
        renderWorkflow(workflowState);
        return;
      }
      confirmedIdCorrection = {
        ...confirmedIdCorrection,
        selectedWork: null,
        newWorkCode: "",
        preview: null,
        error: "",
      };
      setFeedback(
        "ID MangaUpdates corrigido com sucesso. Os metadados derivados foram invalidados. Siga para Atualizar metadados antes de sincronizar com o Notion.",
        "success",
      );
      await refreshMetadataState();
      await refreshNotionMetadataState();
      await refreshConfirmedIdCandidatesState();
      renderWorkflow(workflowState);
    } catch (error) {
      setFeedback(`Falha ao aplicar correção: ${error.message || "erro desconhecido"}.`, "error");
      renderWorkflow(workflowState);
    } finally {
      pendingRequest = false;
    }
  }

  function confirmedIdCorrectionValues() {
    const area = elements.flowsCurrentCards;
    return {
      workId: confirmedIdCorrection.selectedWork?.id || "",
      newWorkCode: area?.querySelector("[data-confirmed-id-new]")?.value?.trim() || confirmedIdCorrection.newWorkCode || "",
    };
  }

  function selectConfirmedIdCorrectionWork(workId) {
    const selectedWork = (confirmedIdCorrection.candidates || [])
      .find(item => Number(item.id) === Number(workId));
    confirmedIdCorrection = {
      ...confirmedIdCorrection,
      selectedWork: selectedWork || null,
      newWorkCode: "",
      preview: null,
      error: selectedWork ? "" : "Obra não encontrada na lista atual.",
    };
    setFeedback("");
    renderWorkflow(workflowState);
  }

  async function searchConfirmedIdCorrectionWorks(search) {
    const sequence = confirmedIdSearchSequence + 1;
    confirmedIdSearchSequence = sequence;
    confirmedIdCorrection = {
      ...confirmedIdCorrection,
      search,
      candidatesLoading: true,
      selectedWork: null,
      newWorkCode: "",
      preview: null,
      error: "",
      page: 1,
    };
    renderWorkflow(workflowState);
    try {
      const { response, payload } = await getConfirmedMangaUpdatesIdCandidates({
        search,
        limit: 25,
      });
      if (sequence !== confirmedIdSearchSequence) return;
      confirmedIdCorrection = {
        ...confirmedIdCorrection,
        candidates: response.ok ? (payload.items || []) : [],
        candidatesError: response.ok ? "" : errorMessage(payload),
        candidatesLoading: false,
        page: 1,
      };
    } catch (error) {
      if (sequence !== confirmedIdSearchSequence) return;
      confirmedIdCorrection = {
        ...confirmedIdCorrection,
        candidates: [],
        candidatesError: `Falha ao buscar obras: ${error.message || "erro desconhecido"}.`,
        candidatesLoading: false,
        page: 1,
      };
    }
    renderWorkflow(workflowState);
  }

  function setConfirmedIdCorrectionNewWorkCode(newWorkCode) {
    confirmedIdCorrection = {
      ...confirmedIdCorrection,
      newWorkCode,
      preview: null,
      error: "",
    };
    setFeedback("");
    renderWorkflow(workflowState);
    const input = area?.querySelector("[data-confirmed-id-new]");
    if (input) {
      input.focus();
      const cursor = input.value.length;
      input.setSelectionRange(cursor, cursor);
    }
  }

  function setConfirmedIdCorrectionPage(page) {
    const total = confirmedIdCorrection.candidates?.length || 0;
    const pages = Math.max(1, Math.ceil(total / 5));
    const nextPage = Math.min(Math.max(Number(page) || 1, 1), pages);
    confirmedIdCorrection = {
      ...confirmedIdCorrection,
      page: nextPage,
    };
    renderWorkflow(workflowState);
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

  function stageFinalFeedback(stageId, metadataSelectionCount) {
    if (stageId === "update_metadata") {
      return {
        message: metadataSuccessMessage(metadataSelectionCount),
        tone: "success",
      };
    }
    const result = workflowState?.run?.results?.[stageId] || {};
    if (result.status === "failed") {
      return {
        message: errorMessage(result),
        tone: "error",
      };
    }
    if (result.status === "completed_with_warnings") {
      return {
        message: stageWarningMessage(result),
        tone: "warning",
      };
    }
    return {
      message: `${selectedFlowStage(workflowState?.run)?.title || "Etapa"} finalizada.`,
      tone: "success",
    };
  }

  function stageWarningMessage(result) {
    return (
      result.warnings?.[0]?.message
      || result.messages?.[0]
      || "Etapa concluída com alertas."
    );
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

  function selectedNotionWorkIds() {
    const area = elements.flowsCurrentCards;
    if (!area) return [];
    return [...area.querySelectorAll("[data-notion-sync-choice]:checked")]
      .map(input => Number(input.dataset.notionSyncWorkId))
      .filter(value => Number.isFinite(value) && value > 0);
  }

  function stagePayload(stageId) {
    if (stageId === "update_metadata") {
      return { selected_ids: selectedMetadataWorkIds() };
    }
    if (stageId === "sync_notion") {
      const workIds = selectedNotionWorkIds();
      return { work_ids: workIds.length ? workIds : remainingJourneyNotionWorkIds() };
    }
    return {};
  }

  function notionExecutionScopeIds(payload) {
    return payload.work_ids || [];
  }

  function remainingJourneyNotionWorkIds() {
    const hidden = new Set(recentlySyncedNotionWorkIds.map(Number));
    return (workflowState?.run?.results?.update_metadata?.metrics?.processed_work_ids || [])
      .filter(workId => !hidden.has(Number(workId)));
  }

  function notionStageSynced() {
    return workflowState?.run?.results?.sync_notion?.metrics?.status === "synced";
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
      || payload?.blockers?.[0]?.message
      || payload?.rejected?.[0]
      || payload?.validation?.blocks?.[0]?.reason
      || "Não foi possível executar."
    );
  }

  function selectedFlowStage(run) { return FLOW_STAGE_GROUPS.find(group => group.id === activeSubtab) || currentFlowStage(run); }

  function setActiveSubtab(subtab) {
    activeSubtab = subtab || "buscar";
    setFeedback("");
    if (activeSubtab === "pendencias") showResolvedReview = false;
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

  function setReviewSearchQuery(value) {
    reviewSearchQuery = value || "";
    activeReviewKey = firstVisibleReviewKey(reviewSearchQuery);
    renderWorkflow(workflowState);
    const input = area?.querySelector("[data-flow-review-search]");
    if (input) {
      input.focus();
      const cursor = input.value.length;
      input.setSelectionRange(cursor, cursor);
    }
  }

  function firstVisibleReviewKey(query) {
    const normalized = normalizeReviewSearch(query);
    const items = [...(reviewState.items || [])].sort((left, right) =>
      reviewTitle(left).localeCompare(reviewTitle(right), "pt-BR", { sensitivity: "base" })
    );
    const visible = items.find(item =>
      !normalized || normalizeReviewSearch(reviewTitle(item)).includes(normalized)
    );
    return visible ? itemKey(visible) : "";
  }

  function reviewTitle(item) {
    return item.localTitle || item.nome || item.searchedTitle || item.normalizedTitle || "";
  }

  function normalizeReviewSearch(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("pt-BR")
      .trim();
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
    createMissingNotionPage,
    confirmedIdCorrection,
    previewConfirmedIdCorrection,
    applyConfirmedIdCorrection,
    selectConfirmedIdCorrectionWork,
    setConfirmedIdCorrectionPage,
    saveCurrentReviewDecision,
    setActiveReviewKey: value => { activeReviewKey = value; },
    setReviewSearchQuery,
    setActiveSubtab,
    setFeedback,
    setSelectedDecisions: value => { selectedDecisions = value; },
    setWorksPage: value => { worksPage = value; },
    showPage,
  }));
  area?.addEventListener("change", event => handleFlowsChange(event, area));
  area?.addEventListener("input", event => handleFlowsInput(event, area, {
    setReviewSearchQuery,
    searchConfirmedIdCorrectionWorks,
    setConfirmedIdCorrectionNewWorkCode,
  }));

  return { loadWorkflow, stopWorkflowPolling };
}

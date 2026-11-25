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
import { getReleasesSummary } from "../api/releasesApi.js";
import { ACTIVE_FLOW_STEPS, FLOW_STAGE_GROUPS } from "../flows/flowConstants.js";
import { createDecisionWorkspaceController } from "../flows/decisionWorkspaceController.js";
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
  handleFlowsKeydown,
} from "../flows/flowsClickHandler.js";
import {
  currentFlowStage,
  normalizeFlowsPayload,
  withOptimisticStage,
} from "../flows/flowModel.js";
import { renderFlowsOverview } from "../flows/flowRenderer.js";
import { escapeHtml } from "../utils/html.js";

export function initFlowsPage(elements, options = {}) {
  let workflowState;
  let workflowTimer;
  let pendingRequest = false;
  let awaitingResolveIdsCompletion = false;
  let activeSubtab = "buscar";
  let worksPage = 1;
  let worksPageSize = 10;
  let worksFilter = "WITHOUT_ID";
  let selectedWorkIds = new Set();
  let worksLoadSequence = 0;
  let activeReviewKey = "";
  let reviewSearchQuery = "";
  let reviewQueueFilter = "all";
  let reviewQueuePageSize = 5;
  let selectedReviewQueueKeys = new Set();
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
  let ignoredReviewKeys = new Set();
  let worksState = { kpis: {}, items: [], pagination: {} };
  let releaseMonitorState = {};
  let metadataState = { kpis: {}, items: [], pagination: {} };
  let notionMetadataState = {};
  let notionSyncCandidateStatus = "default";
  let recentlySyncedNotionWorkIds = [];
  let flowSectionOpenState = {};
  const showPage = options.showPage || (() => {});
  const decisionWorkspace = createDecisionWorkspaceController({
    getDecisions: () => selectedDecisions,
    setDecisions: value => { selectedDecisions = value; },
    getSavedKeys: () => savedReviewKeys,
    getConfirmedCorrection: () => confirmedIdCorrection,
    render: () => renderWorkflow(workflowState),
    reload: loadWorkflow,
    afterApply,
    errorMessage,
    setFeedback,
  });

  async function loadWorkflow() {
    const [data] = await Promise.all([
      loadFlowsApiState({ includeDetails: true }),
      refreshReviewState(),
      refreshWorksState(),
      refreshMetadataState(),
      refreshNotionMetadataState(),
      refreshConfirmedIdCandidatesState(),
      refreshReleaseMonitorState(),
    ]);
    renderWorkflow(data);
    scheduleWorkflowPolling(data);
    return data;
  }

  async function pollWorkflowStatus() {
    const data = await loadFlowsApiState({ includeDetails: false });
    if (flowChanged(data)) renderWorkflow(data);
    else workflowState = data;
    const resolveIdsStatus = data.run.results?.resolve_ids?.status;
    if (awaitingResolveIdsCompletion && ["completed", "completed_with_warnings", "failed", "cancelled"].includes(resolveIdsStatus)) {
      awaitingResolveIdsCompletion = false;
      await refreshWorksState();
      renderWorkflow(data);
      const finalFeedback = stageFinalFeedback("resolve_ids", 0);
      setFeedback(finalFeedback.message, finalFeedback.tone);
    }
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
  async function refreshWorksState() {
    const sequence = ++worksLoadSequence;
    const nextState = await fetchWorksState({
      page: worksPage,
      pageSize: worksPageSize,
      status: worksFilter,
    });
    if (sequence === worksLoadSequence) worksState = nextState;
  }

  async function refreshReleaseMonitorState() {
    try {
      const { response, payload } = await getReleasesSummary();
      releaseMonitorState = response.ok ? payload : {};
    } catch {
      releaseMonitorState = {};
    }
  }

  async function reloadWorksList() {
    const sequence = ++worksLoadSequence;
    const nextState = await fetchWorksState({
      page: worksPage,
      pageSize: worksPageSize,
      status: worksFilter,
    });
    if (sequence !== worksLoadSequence) return;
    worksState = nextState;
    if (workflowState) renderWorkflow(workflowState);
  }

  function setWorksFilter(value) {
    worksFilter = value || "WITHOUT_ID";
    worksPage = 1;
    reloadWorksList();
  }

  function setWorksPage(value) {
    worksPage = Math.max(1, Number(value) || 1);
    reloadWorksList();
  }

  function setWorksPageSize(value) {
    worksPageSize = Math.max(1, Number(value) || 10);
    worksPage = 1;
    reloadWorksList();
  }

  function setWorksSelection(workId, checked) {
    const id = Number(workId);
    if (!Number.isInteger(id) || id <= 0) return;
    if (checked) selectedWorkIds.add(id);
    else selectedWorkIds.delete(id);
  }

  function selectVisibleWorks(checked) {
    for (const item of worksState.items || []) {
      setWorksSelection(item.mangaId, checked);
    }
  }

  function showWorkDetails(workId) {
    const item = (worksState.items || []).find(row => Number(row.mangaId) === Number(workId));
    if (!item) return;
    const reviewItem = (reviewState.items || []).find(row => Number(row.mangaId) === Number(workId));
    showWorksDetailsDialog(item, reviewItem);
  }
  async function refreshMetadataState() { metadataState = await fetchMetadataState(); }
  async function refreshNotionMetadataState() { notionMetadataState = await fetchNotionMetadataState(notionSyncCandidateStatus); }
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
    captureFlowSectionOpenState();
    workflowState = data;
    renderFlowsOverview(elements, data, {
      activeSubtab,
      activeReviewKey,
      showResolvedReview,
      ignoredReviewKeys: [...ignoredReviewKeys],
      review: reviewState,
      reviewSearchQuery,
      reviewQueueFilter,
      reviewQueuePageSize,
      selectedReviewQueueKeys: [...selectedReviewQueueKeys],
      ...decisionWorkspace.snapshot(),
      confirmedIdCorrection,
      selectedDecisions,
      savedReviewKeys: [...savedReviewKeys],
      metadata: metadataState,
      notionMetadata: notionMetadataState,
      notionSyncCandidateStatus,
      recentlySyncedNotionWorkIds,
      flowSectionOpenState,
      works: worksState,
      releaseMonitor: releaseMonitorState,
      worksFilter,
      selectedWorkIds: [...selectedWorkIds],
    });
    syncReviewQueueSelectionState();
    syncWorksSelectionState();
    renderLegacyWorkflow(data);
    const batchDialog = elements.flowsCurrentCards?.querySelector("[data-flow-batch-dialog]");
    if (batchDialog && decisionWorkspace.state.batchOpen) {
      batchDialog.addEventListener("close", () => { decisionWorkspace.state.batchOpen = false; }, { once: true });
      batchDialog.showModal();
    }
    const correctionDialog = elements.flowsCurrentCards?.querySelector("[data-flow-correction-dialog]");
    if (correctionDialog && decisionWorkspace.state.correctionOpen) {
      correctionDialog.addEventListener("close", () => { decisionWorkspace.state.correctionOpen = false; }, { once: true });
      correctionDialog.showModal();
    }
  }

  function syncReviewQueueSelectionState() {
    const selectAll = elements.flowsCurrentCards?.querySelector(
      "[data-flow-review-select-all]",
    );
    if (!selectAll) return;
    const items = [...elements.flowsCurrentCards.querySelectorAll(
      "[data-flow-review-item-select]",
    )];
    const selected = items.filter(item => item.checked).length;
    selectAll.checked = Boolean(items.length && selected === items.length);
    selectAll.indeterminate = selected > 0 && selected < items.length;
  }

  function syncWorksSelectionState() {
    const area = elements.flowsCurrentCards;
    const selectAll = area?.querySelector("[data-flow-works-select-all]");
    if (selectAll) {
      const choices = [...area.querySelectorAll("[data-flow-works-select]")];
      const selected = choices.filter(input => selectedWorkIds.has(Number(input.dataset.flowWorksSelect))).length;
      selectAll.checked = Boolean(choices.length && selected === choices.length);
      selectAll.indeterminate = selected > 0 && selected < choices.length;
    }
    const searchButton = area?.querySelector("[data-flow-run-stage]");
    if (searchButton) searchButton.disabled = selectedWorkIds.size === 0 || pendingRequest;
  }

  function captureFlowSectionOpenState() {
    const sections = elements.flowsCurrentCards?.querySelectorAll("[data-flow-section]");
    if (!sections?.length) return;
    flowSectionOpenState = {
      ...flowSectionOpenState,
      ...Object.fromEntries([...sections].map(section => [
        section.dataset.flowSection,
        section.open,
      ])),
    };
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
      resolve_ids: 220,
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
    let stageCompleted = false;
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      if (attempt > 0) await new Promise(resolve => setTimeout(resolve, 800));
      const data = await loadFlowsApiState({ includeDetails: false });
      renderWorkflow(data);
      const run = data?.run || { status: "idle", results: {} };
      const stageResult = run.results?.[stageId];
      const completed = stageResult
        ? terminalStatuses.has(stageResult.status)
        : run.status !== "running";
      if (completed) {
        stageCompleted = true;
        break;
      }
    }
    const finalData = await loadWorkflow();
    if (!stageCompleted) {
      const finalStageStatus = finalData.run.results?.[stageId]?.status;
      stageCompleted = terminalStatuses.has(finalStageStatus) || finalData.run.status !== "running";
    }
    return stageCompleted;
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
        const stageCompleted = await refreshAfterStage(stage.id);
        if (stageCompleted && stage.id === "resolve_ids") {
          const status = workflowState?.run?.results?.resolve_ids?.status;
          if (status === "completed" || status === "completed_with_warnings") {
            selectedWorkIds.clear();
            renderWorkflow(workflowState);
          }
        }
        if (stageCompleted && stage.id === "sync_notion") {
          rememberProcessedNotionWorkIds(completedNotionWorkIds(notionScopeIds));
          renderWorkflow(workflowState);
        }
        if (!stageCompleted) {
          if (stage.id === "resolve_ids") awaitingResolveIdsCompletion = true;
          setFeedback(`${stage.title} continua em execução.`, "info");
          return;
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
      syncWorksSelectionState();
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
    focusCorrectionIdInput();
    try {
      const { response, payload } = await previewConfirmedMangaUpdatesIdCorrection({
        work_id: values.workId,
        new_work_code: values.newWorkCode,
      });
      confirmedIdCorrection = {
        ...confirmedIdCorrection,
        ...values,
        preview: response.ok || payload?.blockers ? payload : null,
        error: response.ok || payload?.blockers ? "" : errorMessage(payload),
        loading: false,
      };
      setFeedback("");
    } catch (error) {
      confirmedIdCorrection = {
        ...confirmedIdCorrection,
        ...values,
        preview: null,
        error: `Falha ao validar ID: ${error.message || "erro desconhecido"}.`,
        loading: false,
      };
      setFeedback("");
    }
    renderWorkflow(workflowState);
    focusCorrectionIdInput();
  }

  function focusCorrectionIdInput() {
    const input = area?.querySelector("[data-confirmed-id-new]");
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
        decisionWorkspace.state.correctionOpen = false;
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
      decisionWorkspace.state.correctionOpen = false;
      setFeedback(
        "ID MangaUpdates corrigido com sucesso. Os metadados derivados foram invalidados. Siga para Atualizar metadados antes de sincronizar com o Notion.",
        "success",
      );
      await refreshMetadataState();
      await refreshNotionMetadataState();
      await refreshConfirmedIdCandidatesState();
      renderWorkflow(workflowState);
    } catch (error) {
      decisionWorkspace.state.correctionOpen = false;
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
    focusConfirmedIdSearch();
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
    focusConfirmedIdSearch();
  }

  function focusConfirmedIdSearch() {
    const input = elements.flowsCurrentCards?.querySelector("[data-confirmed-id-search]");
    if (!input) return;
    input.focus();
    const cursor = input.value.length;
    input.setSelectionRange(cursor, cursor);
  }

  function setConfirmedIdCorrectionNewWorkCode(newWorkCode) {
    decisionWorkspace.state.correctionOpen = false;
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
    if (stageId === "sync_notion") {
      return notionFinalFeedback();
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

  function notionFinalFeedback() {
    const result = workflowState?.run?.results?.sync_notion || {};
    const metrics = result.metrics || {};
    if (result.status === "failed" || metrics.status === "error") {
      return {
        message: errorMessage(result),
        tone: "error",
      };
    }
    if (result.status === "completed_with_warnings" || metrics.status === "blocked") {
      return {
        message: stageWarningMessage(result),
        tone: "warning",
      };
    }
    const applied = Number(metrics.applied_count || metrics.updated_count || 0);
    const remoteMatches = Number(metrics.remote_matches_local_count || metrics.unchanged_count || 0);
    const failed = Number(metrics.failed_count || 0);
    const checked = Number(metrics.checked_count || applied + remoteMatches + failed);
    if (checked > 0) {
      return {
        message: `Verificação concluída: ${checked} obra(s), ${applied} alteração(ões), ${remoteMatches} equivalente(s) ao Notion, ${failed} falha(s).`,
        tone: failed ? "warning" : "success",
      };
    }
    return {
      message: "Sincronização Notion concluída.",
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
    if (stageId === "resolve_ids") {
      return { selected_ids: [...selectedWorkIds] };
    }
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

  function rememberProcessedNotionWorkIds(workIds) {
    const current = new Set(recentlySyncedNotionWorkIds.map(Number));
    workIds
      .map(Number)
      .filter(workId => Number.isFinite(workId) && workId > 0)
      .forEach(workId => current.add(workId));
    recentlySyncedNotionWorkIds = [...current];
  }

  function completedNotionWorkIds(fallbackWorkIds = []) {
    const metrics = workflowState?.run?.results?.sync_notion?.metrics || {};
    const successfulStatuses = new Set(["synced", "remote_matches_local"]);
    const results = Array.isArray(metrics.results) ? metrics.results : [];
    const explicit = results
      .filter(item => successfulStatuses.has(String(item.status || "")))
      .map(item => item.work_id || item.workId)
      .filter(workId => Number.isFinite(Number(workId)) && Number(workId) > 0);
    if (explicit.length) return explicit;
    return metrics.status === "synced" ? fallbackWorkIds : [];
  }

  function remainingJourneyNotionWorkIds() {
    const hidden = new Set(recentlySyncedNotionWorkIds.map(Number));
    return (workflowState?.run?.results?.update_metadata?.metrics?.processed_work_ids || [])
      .filter(workId => !hidden.has(Number(workId)));
  }

  async function cancelWorkflow() {
    const { response, payload } = await cancelWorkflowRun();
    setFeedback(response.ok ? "Cancelamento solicitado." : errorMessage(payload), response.ok ? "success" : "error");
    await loadWorkflow();
  }

  function setFeedback(message, tone = "success") {
    const className = `flow-feedback flow-feedback--${tone}`;
    if (elements.workflowFeedback) {
      elements.workflowFeedback.textContent = message || "";
      elements.workflowFeedback.className = className;
    }
    if (elements.flowsFeedback) {
      const messageElement = elements.flowsFeedback.querySelector("[data-flow-feedback-message]");
      if (messageElement) messageElement.textContent = message || "";
      elements.flowsFeedback.className = `flow-feedback-toast ${className}`;
      elements.flowsFeedback.hidden = !message;
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
    activeSubtab = subtab === "decisoes" ? "pendencias" : subtab || "buscar";
    setFeedback("");
    if (activeSubtab === "pendencias") showResolvedReview = false;
    if (subtab === "decisoes") decisionWorkspace.openBatch();
    else {
      decisionWorkspace.state.batchOpen = false;
      decisionWorkspace.state.correctionOpen = false;
    }
    renderWorkflow(workflowState);
  }

  function itemKey(item) {
    return item.queueId || item.nome_decisao || item.localTitle || item.nome || "obra";
  }

  function readyDecisions() {
    return Object.fromEntries(Object.entries(selectedDecisions).filter(([key]) => savedReviewKeys.has(key)));
  }

  function clearManualReviewDecision(key) {
    const remaining = { ...selectedDecisions };
    delete remaining[key];
    selectedDecisions = remaining;
    savedReviewKeys.delete(key);
    decisionWorkspace.resetBatchValidation();
  }

  function nextPendingKey(currentKey) {
    const pending = (reviewState.items || [])
      .map(itemKey)
      .filter(key => key !== currentKey && !savedReviewKeys.has(key) && !ignoredReviewKeys.has(key));
    return pending[0] || "";
  }

  function saveCurrentReviewDecision(key) {
    if (!selectedDecisions[key]) {
      setFeedback("Escolha um candidato ou informe um ID antes de preparar o lote.", "error");
      return;
    }
    savedReviewKeys.add(key);
    decisionWorkspace.resetBatchValidation();
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

  function setReviewQueueFilter(value) {
    reviewQueueFilter = value || "all";
    activeReviewKey = "";
    renderWorkflow(workflowState);
  }

  function setReviewQueuePageSize(value) {
    reviewQueuePageSize = Math.max(1, Number(value) || 5);
    renderWorkflow(workflowState);
  }

  function setReviewQueueSelection(keys, checked) {
    for (const key of keys) {
      if (checked) selectedReviewQueueKeys.add(key);
      else selectedReviewQueueKeys.delete(key);
    }
    renderWorkflow(workflowState);
  }

  async function setNotionSyncCandidateStatus(value) {
    notionSyncCandidateStatus = value || "default";
    await refreshNotionMetadataState();
    renderWorkflow(workflowState);
  }

  function ignoreCurrentReview(key) {
    const reviewKey = key || activeReviewKey || itemKey(reviewState.items?.[0] || {});
    if (!reviewKey) return;
    ignoredReviewKeys.add(reviewKey);
    delete selectedDecisions[reviewKey];
    savedReviewKeys.delete(reviewKey);
    decisionWorkspace.resetBatchValidation();
    activeReviewKey = nextPendingKey(reviewKey);
    setFeedback("Pendência ignorada nesta sessão.", "info");
    renderWorkflow(workflowState);
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
    savedReviewKeys = new Set([...savedReviewKeys].filter(key => key in updatedDecisions));
    decisionWorkspace.pruneApplied(updatedDecisions);
    renderWorkflow(workflowState);
  }

  elements.startWorkflow?.addEventListener("click", () => runWorkflow(false));
  elements.resumeWorkflow?.addEventListener("click", () => runWorkflow(true));
  elements.flowsStartWorkflow?.addEventListener("click", () => runCurrentFlowStage());
  elements.flowsResumeWorkflow?.addEventListener("click", () => runWorkflow(true));

  window.addEventListener("manhwateca:flow-subtab", event => {
    if (event.detail?.reviewKey) activeReviewKey = event.detail.reviewKey;
    setActiveSubtab(event.detail?.subtab);
  });

  const area = elements.flowsCurrentCards;
  elements.flowsFeedback?.addEventListener("click", event => {
    if (event.target.closest("[data-flow-feedback-close]")) setFeedback("");
  });
  area?.addEventListener("click", event => handleFlowsClick(event, {
    area,
    afterApply,
    openBatch: decisionWorkspace.openBatch,
    closeBatch: decisionWorkspace.closeBatch,
    checkBatch: decisionWorkspace.checkBatch,
    applyBatch: decisionWorkspace.applyBatch,
    openCorrection: decisionWorkspace.openCorrection,
    closeCorrection: decisionWorkspace.closeCorrection,
    setWorkspaceMode: decisionWorkspace.setMode,
    setReviewDetailTab: decisionWorkspace.setTab,
    setReviewManualDraft: decisionWorkspace.setManualDraft,
    validateAndSetReviewDecision: decisionWorkspace.selectDecision,
    nextReview: () => { activeReviewKey = nextPendingKey(activeReviewKey); decisionWorkspace.state.reviewDetailTab = "manual"; renderWorkflow(workflowState); },
    editReview: key => { savedReviewKeys.delete(key); activeReviewKey = key; decisionWorkspace.state.reviewDetailTab = "manual"; decisionWorkspace.resetBatchValidation(); renderWorkflow(workflowState); },
    removeReview: key => { savedReviewKeys.delete(key); delete selectedDecisions[key]; activeReviewKey = key; decisionWorkspace.resetBatchValidation(); renderWorkflow(workflowState); },
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
    ignoreCurrentReview,
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
    setWorksFilter,
    setWorksPage: setWorksPage,
    setWorksPageSize,
    setWorksSelection,
    selectVisibleWorks,
    hasSelectedWorks: () => selectedWorkIds.size > 0,
    isSearchPending: () => pendingRequest,
    showWorkDetails,
    showPage,
  }));
  area?.addEventListener("change", event => handleFlowsChange(event, area, {
    setNotionSyncCandidateStatus,
    setBatchChoice: decisionWorkspace.setBatchChoice,
    setReviewQueueFilter,
    setReviewQueuePageSize,
    setReviewQueueSelection,
    setWorksSelection,
    selectVisibleWorks,
    hasSelectedWorks: () => selectedWorkIds.size > 0,
    isSearchPending: () => pendingRequest,
    setWorksPageSize,
  }));
  area?.addEventListener("input", event => handleFlowsInput(event, area, {
    getSelectedDecisions: () => selectedDecisions,
    clearManualReviewDecision,
    setReviewManualDraft: decisionWorkspace.setManualDraft,
    renderWorkflow: () => renderWorkflow(workflowState),
    setReviewSearchQuery,
    searchConfirmedIdCorrectionWorks,
    setConfirmedIdCorrectionNewWorkCode,
  }));
  area?.addEventListener("keydown", event => handleFlowsKeydown(event));

  return { loadWorkflow, stopWorkflowPolling };
}

function showWorksDetailsDialog(item, reviewItem) {
  document.querySelector("[data-flow-works-details-dialog]")?.remove();
  const candidates = reviewItem?.candidates || [];
  const status = {
    READY_TO_SEARCH: "Não pesquisada",
    CANDIDATES_FOUND: "Revisão",
    PENDING_REVIEW: "Revisão",
    MANUAL_ID_REQUIRED: "Sem correspondência",
    ERROR: "Falha",
  }[item.decisionStatus] || "Sem ID confirmado";
  const result = item.decisionStatus === "READY_TO_SEARCH"
    ? "Ainda não consultada"
    : item.decisionStatus === "ERROR"
      ? "Falha na consulta"
      : `${Number(item.candidatesCount || 0)} candidato(s)`;
  const lastSearch = item.lastSearchAt
    ? new Date(item.lastSearchAt).toLocaleString("pt-BR")
    : "Ainda não pesquisada";
  const candidateMarkup = candidates.length
    ? candidates.map(candidate => {
      const confidence = Number(candidate.confidence ?? candidate.pontuacao);
      const confidenceLabel = Number.isFinite(confidence)
        ? `${Math.round(confidence <= 1 ? confidence * 100 : confidence)}% de confiança`
        : "Confiança não informada";
      return `<li><strong>${escapeHtml(candidate.title || candidate.titulo || "Candidato sem título")}</strong><span>ID ${escapeHtml(String(candidate.id || "—"))} · ${escapeHtml(confidenceLabel)}</span></li>`;
    }).join("")
    : "<li class=\"flow-search-detail-empty\">Nenhum candidato disponível para revisão.</li>";
  const dialog = document.createElement("dialog");
  dialog.className = "flow-search-details-dialog";
  dialog.dataset.flowWorksDetailsDialog = "";
  dialog.innerHTML = `
    <div class="flow-search-details-content">
      <header class="flow-search-details-header">
        <div><span class="eyebrow">Detalhes da obra</span><h3>${escapeHtml(item.localTitle || "Obra sem título")}</h3></div>
        <button type="button" class="flow-search-details-close" data-flow-works-details-close aria-label="Fechar detalhes">×</button>
      </header>
      <dl class="flow-search-details-meta">
        <div><dt>Situação</dt><dd>${escapeHtml(status)}</dd></div>
        <div><dt>Resultado</dt><dd>${escapeHtml(result)}</dd></div>
        <div><dt>Última busca</dt><dd>${escapeHtml(lastSearch)}</dd></div>
      </dl>
      <section class="flow-search-details-candidates"><h4>Candidatos</h4><ul>${candidateMarkup}</ul></section>
      ${reviewItem ? '<button type="button" class="primary-action" data-flow-works-details-review>Revisar candidatos</button>' : ""}
    </div>`;
  dialog.addEventListener("click", event => {
    if (event.target === dialog || event.target.closest("[data-flow-works-details-close]")) dialog.close();
    if (event.target.closest("[data-flow-works-details-review]")) {
      dialog.close();
      window.dispatchEvent(new CustomEvent("manhwateca:flow-subtab", {
        detail: { subtab: "pendencias", reviewKey: reviewItem.queueId },
      }));
    }
  });
  dialog.addEventListener("close", () => dialog.remove(), { once: true });
  document.body.append(dialog);
  dialog.showModal();
}

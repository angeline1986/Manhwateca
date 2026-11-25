import {
  FLOW_STAGE_GROUPS,
  FLOW_STATUS_LABELS,
  RESOLVE_ID_STEPS,
} from "./flowConstants.js";
import { currentFlowStage, flowStageStatus, visibleFlowStatuses } from "./flowModel.js";
import { defaultCards, renderMeta, renderTopAction } from "./flowRendererDetails.js";
import { renderResolveIdsPanel } from "./resolveIdsPanel.js";
import { renderSyncNotionPanel } from "./syncNotionPanel.js";
import { renderUpdateMetadataPanel } from "./updateMetadataPanel.js";
import { escapeHtml } from "../utils/html.js";
export { primaryLabel } from "./flowRendererDetails.js";

export function renderFlowsOverview(elements, data, options = {}) {
  const run = data.run || { status: "idle", results: {} };
  const visibleStatuses = visibleFlowStatuses(run);
  const stageStatuses = FLOW_STAGE_GROUPS.map(group => visibleStatuses[group.id]);
  const completed = stageStatuses.filter(status =>
    ["completed", "completed_with_warnings"].includes(status)
  ).length;
  const percent = Math.round((completed / FLOW_STAGE_GROUPS.length) * 100);
  const activeStage = currentFlowStage(run, visibleStatuses);
  const activeStatus = visibleStatuses[activeStage.id] || "waiting";
  const visibleRunning = stageStatuses.some(status =>
    ["running", "validating"].includes(status)
  );

  renderSummary(elements, completed, percent, activeStage, activeStatus, run);
  renderStageList(elements, run, visibleStatuses);
  renderCurrentPanel(elements, {
    activeStage,
    activeStatus,
    completed,
    data,
    run,
    visibleRunning,
    activeSubtab: options.activeSubtab || "buscar",
    activeReviewKey: options.activeReviewKey || "",
    showResolvedReview: Boolean(options.showResolvedReview),
    selectedDecisions: options.selectedDecisions || {},
    savedReviewKeys: options.savedReviewKeys || [],
    visibleStatuses,
    review: options.review,
    reviewSearchQuery: options.reviewSearchQuery || "",
    reviewQueueFilter: options.reviewQueueFilter || "all",
    reviewQueuePageSize: options.reviewQueuePageSize || 5,
    selectedReviewQueueKeys: options.selectedReviewQueueKeys || [],
    ignoredReviewKeys: options.ignoredReviewKeys || [],
    confirmedIdCorrection: options.confirmedIdCorrection || {},
    workspaceMode: options.workspaceMode || "review",
    reviewDetailTab: options.reviewDetailTab || "manual",
    manualDrafts: options.manualDrafts || {},
    reviewChoiceFeedback: options.reviewChoiceFeedback || {},
    reviewValidationPending: Boolean(options.reviewValidationPending),
    batchSelectedKeys: options.batchSelectedKeys || [],
    batchValidation: options.batchValidation || null,
    batchChecking: Boolean(options.batchChecking),
    metadata: options.metadata,
    notionMetadata: options.notionMetadata,
    notionSyncCandidateStatus: options.notionSyncCandidateStatus || "default",
    recentlySyncedNotionWorkIds: options.recentlySyncedNotionWorkIds || [],
    flowSectionOpenState: options.flowSectionOpenState || {},
    works: options.works,
    worksFilter: options.worksFilter || "WITHOUT_ID",
    selectedWorkIds: options.selectedWorkIds || [],
  });
  return { activeStage, activeStatus, visibleRunning };
}

function renderSummary(elements, completed, percent, activeStage, activeStatus, run) {
  if (elements.flowsSummary) {
    elements.flowsSummary.innerHTML = [
      `<span class="flow-chip ${completed === FLOW_STAGE_GROUPS.length ? "ok" : ""}">${completed} de ${FLOW_STAGE_GROUPS.length} etapas deste fluxo concluídas</span>`,
      `<span class="flow-chip">${escapeHtml(FLOW_STATUS_LABELS[activeStatus] || activeStatus)}: ${escapeHtml(activeStage.title)}</span>`,
      run.status === "failed" ? '<span class="flow-chip warn">Requer atenção</span>' : "",
    ].join("");
  }
  if (elements.flowsProgress) {
    elements.flowsProgress.innerHTML = `
      <span><b>${percent}%</b> concluído · etapa ${activeStage.order} de ${FLOW_STAGE_GROUPS.length}</span>
      <div><span style="width:${percent}%"></span></div>
    `;
  }
}

function renderStageList(elements, run, visibleStatuses) {
  if (!elements.flowsStageList) return;
  elements.flowsStageList.innerHTML = FLOW_STAGE_GROUPS.map(group => {
    const status = visibleStatuses[group.id];
    const marker = status === "completed" ? "✓" : group.order;
    const currentClass = ["running", "validating", "completed_with_warnings"].includes(status)
      ? " current"
      : "";
    return `
      <article class="flow-stage ${status}${currentClass}">
        <span class="flow-stage-marker">${escapeHtml(marker)}</span>
        <div>
          <h3>${group.order}. ${escapeHtml(group.title)}</h3>
          <p>${escapeHtml(group.description)}</p>
        </div>
        <span class="flow-stage-status">${escapeHtml(FLOW_STATUS_LABELS[status] || status)}</span>
      </article>
    `;
  }).join("");
}

function renderCurrentPanel(elements, context) {
  const { activeStage, data, run, visibleRunning } = context;
  const selectedStage = FLOW_STAGE_GROUPS.find(group =>
    group.id === context.activeSubtab
  ) || activeStage;
  const selectedStatus = flowStageStatus(selectedStage, run);
  const content = elements.flowsCurrentTitle?.closest(".flows-journey-content");
  const topbar = document.getElementById("topbar");
  if (context.activeSubtab === "pendencias" && !topbar?.querySelector(".flow-decision-breadcrumb")) {
    topbar?.querySelector(".topbar-flow-meta")?.insertAdjacentHTML("beforebegin", '<nav class="flow-decision-breadcrumb" aria-label="Localização"><span>Manhwateca</span><span>Fluxo operacional</span><span>Central de decisões</span><strong aria-current="page">Resolver IDs</strong></nav>');
  }
  document.getElementById("topbar")?.classList.toggle(
    "flows-search-page-active",
    selectedStage.id === "resolve_ids" && context.activeSubtab === "buscar",
  );
  document.getElementById("topbar")?.classList.toggle("flows-decision-page-active", context.activeSubtab === "pendencias");
  content?.classList.toggle("flows-resolve-mode", selectedStage.id === "resolve_ids");
  content?.classList.toggle("flows-apply-mode", false);
  content?.classList.toggle("flows-metadata-mode", selectedStage.id === "update_metadata");
  content?.classList.toggle("flows-review-mode", context.activeSubtab === "pendencias");
  content?.classList.toggle("flows-sync-notion-mode", selectedStage.id === "sync_notion");
  content?.closest(".flows-journey-panel")?.classList.toggle("flows-journey-panel--resolve", context.activeSubtab === "buscar");
  content?.closest(".flows-journey-panel")?.classList.toggle("flows-journey-panel--metadata", selectedStage.id === "update_metadata");
  content?.closest(".flows-journey-panel")?.classList.toggle("flows-journey-panel--review", context.activeSubtab === "pendencias");
  content?.closest(".flows-journey-panel")?.classList.toggle("flows-journey-panel--sync-notion", selectedStage.id === "sync_notion");
  if (elements.flowsCurrentTitle) {
    elements.flowsCurrentTitle.innerHTML = titleWithTooltip(
      journeyTitle(context.activeSubtab, selectedStage),
      selectedStage.description,
    );
  }
  if (elements.flowsCurrentDescription) {
    elements.flowsCurrentDescription.textContent = "Jornada operacional";
  }
  renderMeta(elements, run, selectedStatus);
  renderTopAction(elements, selectedStage, selectedStatus, visibleRunning);
  if (!elements.flowsCurrentCards) return;
  elements.flowsCurrentCards.classList.toggle("flow-detail-card--resolve", context.activeSubtab === "buscar");
  elements.flowsCurrentCards.classList.toggle("flow-detail-card--metadata", selectedStage.id === "update_metadata");
  elements.flowsCurrentCards.classList.toggle("flow-detail-card--review", context.activeSubtab === "pendencias");
  elements.flowsCurrentCards.classList.toggle("flow-detail-card--sync-notion", selectedStage.id === "sync_notion");
  if (selectedStage.id === "resolve_ids") {
    elements.flowsCurrentCards.innerHTML = renderResolveIdsPanel(context);
    return;
  }
  if (selectedStage.id === "update_metadata") {
    elements.flowsCurrentCards.innerHTML = renderUpdateMetadataPanel(context.metadata);
    return;
  }
  if (selectedStage.id === "sync_notion") {
    const hiddenWorkIds = context.recentlySyncedNotionWorkIds || [];
    const journeyWorkIds = (run.results?.update_metadata?.metrics?.processed_work_ids || [])
      .filter(workId => !hiddenWorkIds.map(Number).includes(Number(workId)));
    elements.flowsCurrentCards.innerHTML = renderSyncNotionPanel({
      stageResult: run.results?.sync_notion,
      stageStatus: selectedStatus,
      legacyMetadata: context.notionMetadata,
      journeyWorkIds,
      hiddenWorkIds,
      candidateStatus: context.notionSyncCandidateStatus,
    });
    return;
  }
  elements.flowsCurrentCards.innerHTML = defaultCards(selectedStage, data);
}

function titleWithTooltip(title, description) {
  if (!description) return escapeHtml(title);
  return `<span class="flow-heading-tooltip" tabindex="0" aria-label="${escapeHtml(description)}">${escapeHtml(title)}</span>`;
}

function journeyTitle(activeSubtab, selectedStage) {
  return RESOLVE_ID_STEPS.find(step => step.id === activeSubtab)?.title
    || selectedStage.title;
}

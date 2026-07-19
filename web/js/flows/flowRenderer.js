import {
  FLOW_STAGE_GROUPS,
  FLOW_STATUS_LABELS,
  RESOLVE_ID_STEPS,
} from "./flowConstants.js";
import { currentFlowStage, visibleFlowStatuses } from "./flowModel.js";
import { renderResolveIdsPanel } from "./resolveIdsPanel.js";
import { renderSyncNotionPanel } from "./syncNotionPanel.js";
import { renderUpdateMetadataPanel } from "./updateMetadataPanel.js";
import { escapeHtml } from "../utils/html.js";

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
    metadata: options.metadata,
    notionMetadata: options.notionMetadata,
    works: options.works,
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
  const selectedStatus = context.visibleStatuses[selectedStage.id] || "waiting";
  const content = elements.flowsCurrentTitle?.closest(".flows-journey-content");
  content?.classList.toggle("flows-apply-mode", context.activeSubtab === "decisoes");
  content?.classList.toggle("flows-metadata-mode", selectedStage.id === "update_metadata");
  content?.closest(".flows-journey-panel")?.classList.toggle("flows-journey-panel--metadata", selectedStage.id === "update_metadata");
  if (elements.flowsCurrentTitle) {
    elements.flowsCurrentTitle.textContent = journeyTitle(context.activeSubtab, selectedStage);
  }
  if (elements.flowsCurrentDescription) {
    elements.flowsCurrentDescription.textContent = "Jornada operacional";
  }
  renderMeta(elements, run, selectedStatus);
  renderTopAction(elements, selectedStage, selectedStatus, visibleRunning);
  if (!elements.flowsCurrentCards) return;
  elements.flowsCurrentCards.classList.toggle("flow-detail-card--metadata", selectedStage.id === "update_metadata");
  if (selectedStage.id === "resolve_ids") {
    elements.flowsCurrentCards.innerHTML = renderResolveIdsPanel(context);
    return;
  }
  if (selectedStage.id === "update_metadata") {
    elements.flowsCurrentCards.innerHTML = renderUpdateMetadataPanel(context.metadata);
    return;
  }
  if (selectedStage.id === "sync_notion") {
    elements.flowsCurrentCards.innerHTML = renderSyncNotionPanel({
      stageResult: run.results?.sync_notion,
      stageStatus: selectedStatus,
      legacyMetadata: context.notionMetadata,
      journeyWorkIds: run.results?.update_metadata?.metrics?.processed_work_ids || [],
    });
    return;
  }
  elements.flowsCurrentCards.innerHTML = defaultCards(selectedStage, data);
}

function journeyTitle(activeSubtab, selectedStage) {
  return RESOLVE_ID_STEPS.find(step => step.id === activeSubtab)?.title
    || selectedStage.title;
}

function renderMeta(elements, run, activeStatus) {
  if (!elements.flowsCurrentMeta) return;
  const finishedDate = shortDate(run.finished_at || run.started_at);
  const startedTime = shortTime(run.started_at);
  const finishedTime = shortTime(run.finished_at);
  elements.flowsCurrentMeta.innerHTML = `
    <div class="status-minimalist">
      <div class="main-status">
        <span class="pulse-icon"></span>
        <span>${escapeHtml(FLOW_STATUS_LABELS[activeStatus] || activeStatus)}</span>
        <b>${escapeHtml(finishedDate)}</b>
      </div>
      <div class="dates-row">
        INÍCIO: <b>${escapeHtml(startedTime)}</b>
        <span>•</span>
        FIM: <b>${escapeHtml(finishedTime)}</b>
      </div>
    </div>
  `;
}

function shortDate(value) {
  if (!value) return "--/--";
  return new Date(value).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
  });
}

function shortTime(value) {
  if (!value) return "--:--:--";
  return new Date(value).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function primaryLabel(activeStage, activeStatus) {
  if (activeStage.id === "resolve_ids" && activeStatus === "completed_with_warnings") {
    return "Revisar pendências";
  }
  return `Executar ${activeStage.title}`;
}

function renderTopAction(elements, activeStage, activeStatus, visibleRunning) {
  if (elements.flowsStartWorkflow) {
    elements.flowsStartWorkflow.hidden = activeStage.id === "sync_notion";
    elements.flowsStartWorkflow.disabled = visibleRunning;
    elements.flowsStartWorkflow.textContent = visibleRunning
      ? "Etapa em execução"
      : primaryLabel(activeStage, activeStatus);
  }
}

function defaultCards(activeStage, data) {
  const dataCopy = {
    title: activeStage.title,
    lead: activeStage.description,
    cards: [["Status", "Aguardando"], ["Integração", "Disponível"], ["Histórico", "Sem execução"]],
    action: `Executar ${activeStage.title}`,
  };
  return `
    <p class="lead">${escapeHtml(dataCopy.lead)}</p>
    <div class="flow-subgrid">
      ${dataCopy.cards.map(([label, value]) => `
        <article class="flow-metric-card">
          <strong>${escapeHtml(value)}</strong>
          <span>${escapeHtml(label)}</span>
        </article>
      `).join("")}
    </div>
    <table class="flow-table">
      <thead><tr><th>Processo</th><th>Status</th><th>Ação</th></tr></thead>
      <tbody>
        <tr>
          <td>${escapeHtml(dataCopy.title)}</td>
          <td><span class="flow-badge info">Aguardando</span></td>
          <td>${escapeHtml(dataCopy.action)}</td>
        </tr>
      </tbody>
    </table>
    <div class="flow-panel-note">
      Esta etapa será executada pelo backend oficial de Fluxos. Use-a depois
      que as pendências anteriores estiverem resolvidas.
    </div>
    <div class="actions">
      <button class="primary-action" type="button" data-flow-run-stage>
        ${escapeHtml(dataCopy.action)}
      </button>
      <button class="secondary-action" type="button" data-flow-refresh>Atualizar estado</button>
    </div>
  `;
}

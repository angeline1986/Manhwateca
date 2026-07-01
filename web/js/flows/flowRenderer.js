import {
  FLOW_STAGE_GROUPS,
  FLOW_STATUS_LABELS,
  RESOLVE_ID_STEPS,
} from "./flowConstants.js";
import { currentFlowStage, visibleFlowStatuses } from "./flowModel.js";
import { renderResolveIdsPanel } from "./resolveIdsPanel.js";
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
    visibleStatuses,
    review: options.review,
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
  if (elements.flowsCurrentTitle) {
    elements.flowsCurrentTitle.textContent = journeyTitle(context.activeSubtab, selectedStage);
  }
  if (elements.flowsCurrentDescription) {
    elements.flowsCurrentDescription.textContent = "Jornada operacional";
  }
  renderJourneyNav(elements, context.activeSubtab);
  renderMeta(elements, run, selectedStatus);
  renderTopAction(elements, selectedStage, selectedStatus, visibleRunning);
  if (!elements.flowsCurrentCards) return;
  elements.flowsCurrentCards.innerHTML = selectedStage.id === "resolve_ids"
    ? renderResolveIdsPanel(context)
    : defaultCards(selectedStage, data);
}

function journeyTitle(activeSubtab, selectedStage) {
  return RESOLVE_ID_STEPS.find(step => step.id === activeSubtab)?.title
    || selectedStage.title;
}

function renderJourneyNav(elements, activeSubtab) {
  if (!elements.flowsCurrentActions) return;
  elements.flowsCurrentActions.innerHTML = [
    ...RESOLVE_ID_STEPS.map(step => `
      <button type="button" class="${activeSubtab === step.id ? "active" : ""}"
        data-flow-subtab="${step.id}">
        ${escapeHtml(step.title)}
      </button>
    `),
    `<button type="button" class="${activeSubtab === "update_metadata" ? "active" : ""}"
      data-flow-subtab="update_metadata">Atualizar metadados</button>`,
    `<button type="button" class="${activeSubtab === "sync_notion" ? "active" : ""}"
      data-flow-subtab="sync_notion">Sincronizar Notion</button>`,
  ].join("");
}

function renderMeta(elements, run, activeStatus) {
  if (!elements.flowsCurrentMeta) return;
  const startedAt = run.started_at ? new Date(run.started_at).toLocaleString("pt-BR") : "Ainda não executado";
  const finishedAt = run.finished_at ? new Date(run.finished_at).toLocaleString("pt-BR") : "Sem finalização registrada";
  elements.flowsCurrentMeta.innerHTML = `
    <article class="flow-meta-card">
      <div><strong>Status desta etapa</strong><span class="flow-meta-status">${escapeHtml(FLOW_STATUS_LABELS[activeStatus] || activeStatus)}</span></div>
      <div><strong>Início</strong><span class="flow-meta-date">${escapeHtml(startedAt)}</span></div>
      <div><strong>Última finalização</strong><span class="flow-meta-date">${escapeHtml(finishedAt)}</span></div>
    </article>
  `;
}

export function primaryLabel(activeStage, activeStatus) {
  if (activeStage.id === "resolve_ids" && activeStatus === "completed_with_warnings") {
    return "Revisar pendências";
  }
  return `Executar ${activeStage.title}`;
}

function renderTopAction(elements, activeStage, activeStatus, visibleRunning) {
  if (elements.flowsStartWorkflow) {
    elements.flowsStartWorkflow.disabled = visibleRunning;
    elements.flowsStartWorkflow.textContent = visibleRunning
      ? "Etapa em execução"
      : primaryLabel(activeStage, activeStatus);
  }
}

function defaultCards(activeStage, data) {
  const copy = {
    update_metadata: {
      title: "Consultar detalhes dos IDs",
      lead: "Sincronize gêneros, autores, status e dados oficiais dos IDs confirmados.",
      cards: [
        ["IDs confirmados", "Disponíveis após revisão"],
        ["Pendentes", "Aguardam decisão"],
        ["Metadados", "Prontos para consulta"],
      ],
      action: "Consultar detalhes",
    },
    sync_notion: {
      title: "Sincronizar Notion",
      lead: "Atualize as páginas no Notion depois que os metadados estiverem consistentes.",
      cards: [
        ["Páginas", "A preparar"],
        ["Alterações", "A revisar"],
        ["Sincronização", "Aguardando"],
      ],
      action: "Sincronizar Notion",
    },
  }[activeStage.id];
  const dataCopy = copy || {
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

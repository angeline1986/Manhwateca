import { FLOW_STATUS_LABELS } from "./flowConstants.js";
import { escapeHtml } from "../utils/html.js";

export function renderMeta(elements, run, activeStatus) {
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
    return "Abrir Central de decisões";
  }
  return `Executar ${activeStage.title}`;
}

export function renderTopAction(elements, activeStage, activeStatus, visibleRunning) {
  if (elements.flowsStartWorkflow) {
    elements.flowsStartWorkflow.hidden = activeStage.id === "sync_notion";
    elements.flowsStartWorkflow.disabled = visibleRunning;
    elements.flowsStartWorkflow.textContent = visibleRunning
      ? "Etapa em execução"
      : primaryLabel(activeStage, activeStatus);
  }
}

export function defaultCards(activeStage) {
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

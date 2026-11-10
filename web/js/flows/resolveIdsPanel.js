import { escapeHtml } from "../utils/html.js";
import { decisionsTab } from "./applyDecisionsPanel.js";
import { pendingTab } from "./pendingReviewPanel.js";

export function renderResolveIdsPanel({
  activeSubtab,
  activeReviewKey,
  showResolvedReview,
  review,
  reviewSearchQuery,
  confirmedIdCorrection,
  selectedDecisions,
  savedReviewKeys,
  flowSectionOpenState,
  works,
  worksFilter = "WITHOUT_ID",
  selectedWorkIds = [],
  releaseMonitor = {},
}) {
  return `
    ${activeSubtab === "buscar" ? searchTab(review, works, worksFilter, selectedWorkIds, releaseMonitor) : ""}
    ${activeSubtab === "pendencias" ? pendingTab(review, selectedDecisions, activeReviewKey, {
      savedKeys: savedReviewKeys,
      searchQuery: reviewSearchQuery,
      showResolved: showResolvedReview,
      idCorrection: confirmedIdCorrection,
      openSections: flowSectionOpenState,
    }) : ""}
    ${activeSubtab === "decisoes" ? decisionsTab(review, selectedDecisions) : ""}
  `;
}

function searchTab(review, works, worksFilter, selectedWorkIds, releaseMonitor) {
  const rows = searchRows(works);
  const kpis = works?.kpis || {};
  const pageSize = Number(works?.pagination?.pageSize || 10);
  const selected = new Set(selectedWorkIds.map(Number));
  return `
    <div class="flow-search-page-header">
      <div class="flow-search-page-heading">
        <div class="flow-search-breadcrumb">MANHWATECA <span>/</span> FLUXOS OPERACIONAIS</div>
        <h1>Buscar Candidatos</h1>
      </div>
      ${monitoringChip(releaseMonitor)}
    </div>
    <section class="flow-search-main-card">
          <div class="flow-search-toolbar">
            <div class="flow-search-filters" role="group" aria-label="Filtrar obras por situação">
              ${searchFilter("WITHOUT_ID", "Todos", kpis.withoutId ?? 0, worksFilter)}
              ${searchFilter("REVIEW", "Revisão", kpis.candidatesFound ?? 0, worksFilter)}
              ${searchFilter("READY_TO_SEARCH", "Não pesquisada", kpis.readyToSearch ?? 0, worksFilter)}
              ${searchFilter("MANUAL_ID_REQUIRED", "Sem correspondência", kpis.noResult ?? 0, worksFilter)}
              ${searchFilter("ERROR", "Falha", kpis.apiErrors ?? 0, worksFilter)}
            </div>
            <div class="flow-search-actions">
              <button class="secondary-action" type="button" data-flow-subtab="pendencias">Ver pendências</button>
              <button class="primary-action" type="button" data-flow-run-stage>Buscar candidatos</button>
            </div>
          </div>
          <div class="flow-search-table-scroll">
          <table class="flow-table flow-search-results-table">
            <colgroup>
              <col class="flow-search-col-select">
              <col class="flow-search-col-title">
              <col class="flow-search-col-status">
              <col class="flow-search-col-result">
              <col class="flow-search-col-action">
              <col class="flow-search-col-details">
            </colgroup>
            <thead>
              <tr>
                <th class="flow-search-select-cell"><input type="checkbox" data-flow-works-select-all aria-label="Selecionar obras desta página"></th>
                <th>Obra local</th><th>Situação</th><th>Resultado</th><th>Ação sugerida</th>
                <th class="flow-search-details-cell">Ações</th>
              </tr>
            </thead>
            <tbody>
              ${rows.length ? rows.map(item => {
                const id = Number(item.mangaId);
                const status = statusLabel(item.decisionStatus);
                const result = resultLabel(item);
                return `
                  <tr>
                    <td class="flow-search-select-cell"><input type="checkbox" data-flow-works-select="${id}" aria-label="Selecionar ${escapeHtml(item.localTitle || "obra")}" ${selected.has(id) ? "checked" : ""}></td>
                    <td class="flow-search-work-title" title="${escapeHtml(item.localTitle || "Obra sem título")}">${escapeHtml(item.localTitle || "Obra sem título")}</td>
                    <td><span class="flow-badge ${statusTone(item.decisionStatus)}">${escapeHtml(status)}</span></td>
                    <td>${escapeHtml(result)}</td>
                    <td>${escapeHtml(actionLabel(item.nextAction))}</td>
                    <td class="flow-search-details-cell">
                      <button class="flow-search-detail-button" type="button" data-flow-work-view="${id}" aria-label="Visualizar detalhes de ${escapeHtml(item.localTitle || "obra")}" title="Visualizar detalhes">
                        <span class="flow-search-eye-icon" aria-hidden="true"></span>
                      </button>
                    </td>
                  </tr>`;
              }).join("") : `<tr><td class="flow-search-empty" colspan="6">Nenhuma obra encontrada nesta situação.</td></tr>`}
            </tbody>
          </table>
          </div>
          <div class="flow-search-footer">
            <label class="flow-search-page-size">
              <span>Exibir:</span>
              <select data-flow-works-page-size aria-label="Obras por página">
                ${[10, 25, 50].map(size => `<option value="${size}" ${size === pageSize ? "selected" : ""}>${size}</option>`).join("")}
              </select>
            </label>
            ${searchPagination(works)}
          </div>
    </section>
  `;
}

function monitoringChip(summary = {}) {
  const monitored = summary?.monitoring?.monitored_count;
  const run = summary?.last_monitor_run;
  const checkedAt = run?.finished_at || run?.started_at;
  const checkedDate = checkedAt ? new Date(checkedAt) : null;
  const checkedTime = checkedDate && Number.isFinite(checkedDate.getTime())
    ? checkedDate.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
    : "—";
  const hasCount = monitored !== undefined && monitored !== null && Number.isFinite(Number(monitored));
  const numericCount = hasCount ? Number(monitored) : null;
  const countLabel = numericCount === null ? "—" : numericCount === 0 ? "" : numericCount.toLocaleString("pt-BR");
  const monitoredLabel = countLabel ? `${countLabel} obras` : "";
  return `<div class="flow-search-monitor-chip ${hasCount ? "" : "is-unavailable"}" aria-label="Resumo do monitoramento">
    <span class="flow-search-monitor-label">Monitorando:</span>
    ${monitoredLabel ? `<strong>${monitoredLabel}</strong>` : ""}
    <span class="flow-search-monitor-divider" aria-hidden="true"></span>
    <span class="flow-search-monitor-label">Última verificação às <strong>${checkedTime}</strong></span>
  </div>`;
}

function searchFilter(value, label, count, active) {
  const numericCount = Number(count) || 0;
  return `<button class="flow-search-filter ${value === active ? "is-active" : ""} ${numericCount === 0 ? "is-empty" : ""}" type="button" data-flow-works-status="${value}" aria-pressed="${value === active}">
    <span>${label}${numericCount > 0 ? ` (${numericCount})` : ""}</span>
  </button>`;
}

function searchPagination(works) {
  const pagination = works?.pagination || {};
  const page = Number(pagination.page || 1);
  const pages = Math.max(1, Number(pagination.pages || 1));
  return `<div class="flow-search-pagination">
    <button class="flow-search-page-button" type="button" ${page <= 1 ? "disabled" : ""} data-flow-works-page="${page - 1}" aria-label="Página anterior">&lt;&lt;</button>
    <span aria-label="Página ${page} de ${pages}">${page} / ${pages}</span>
    <button class="flow-search-page-button" type="button" ${page >= pages ? "disabled" : ""} data-flow-works-page="${page + 1}" aria-label="Próxima página">&gt;&gt;</button>
  </div>`;
}

function searchRows(works) {
  return works?.items || [];
}

function statusLabel(status) {
  return {
    WITHOUT_ID: "Sem ID confirmado",
    READY_TO_SEARCH: "Não pesquisada",
    CANDIDATES_FOUND: "Revisão",
    PENDING_REVIEW: "Revisão",
    MANUAL_ID_REQUIRED: "Sem correspondência",
    ERROR: "Falha",
  }[status] || status || "Revisão";
}

function statusTone(status) {
  if (status === "ERROR" || status === "MANUAL_ID_REQUIRED") return "bad";
  if (status === "CANDIDATES_FOUND" || status === "PENDING_REVIEW") return "amb";
  return "info";
}

function resultLabel(item) {
  if (item?.decisionStatus === "READY_TO_SEARCH") return "—";
  if (item?.decisionStatus === "ERROR") return "Falha na consulta";
  const arrayCount = Array.isArray(item?.candidates) ? item.candidates.length : null;
  const explicitCount = Number.isFinite(Number(item?.candidateCount))
    ? Number(item.candidateCount)
    : Number.isFinite(Number(item?.candidatesCount))
      ? Number(item.candidatesCount)
      : arrayCount;
  if (explicitCount !== null && Number.isFinite(explicitCount)) {
    return `${explicitCount} encontrado${explicitCount === 1 ? "" : "s"}`;
  }
  return {
    WITHOUT_ID: "—",
    CANDIDATES_FOUND: "Disponíveis para revisão",
    PENDING_REVIEW: "Disponíveis para revisão",
    MANUAL_ID_REQUIRED: "0 encontrados",
  }[item?.decisionStatus] || "Aguardando";
}

function actionLabel(action) {
  return {
    SEARCH_API: "Executar busca",
    NORMALIZE_TITLE: "Ajustar título",
    REVIEW_CANDIDATES: "Revisar candidatos",
    MANUAL_SEARCH: "Ajustar busca",
    RETRY_FAILED: "Repetir tentativa",
  }[action] || action || "Executar busca";
}

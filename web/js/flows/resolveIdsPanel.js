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
  run,
  selectedDecisions,
  savedReviewKeys,
  flowSectionOpenState,
  works,
}) {
  const summary = review?.summary || {};
  const metrics = run.results?.resolve_ids?.metrics || {};
  return `
    ${activeSubtab === "buscar" ? searchTab(metrics, summary, review, works) : ""}
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

function searchTab(metrics, summary, review, works) {
  const rows = searchRows(metrics, summary, review, works);
  const kpis = works?.kpis || {};
  const description = "Localize candidatos no MangaUpdates para obras sem identificação.";
  return `
    <section class="flow-search-main-card">
      <details class="flow-section-details" open>
        <summary class="flow-section-summary">
          <span class="eyebrow">Jornada operacional</span>
          <h2>${headingTooltip("Buscar candidatos", description)}</h2>
        </summary>
        <div class="flow-section-body">
          <div class="flow-subgrid">
            ${metricCard("Sem ID", kpis.withoutId ?? unresolvedCount(metrics))}
            ${metricCard("Sugestões", kpis.candidatesFound ?? suggestionCount(metrics, summary))}
            ${metricCard("Sem resultado", kpis.noResult ?? criticalCount(metrics))}
            ${metricCard("Erros de API", kpis.apiErrors ?? 0)}
          </div>
          <table class="flow-table flow-search-results-table">
            <colgroup>
              <col class="flow-search-col-title">
              <col class="flow-search-col-status">
              <col class="flow-search-col-result">
              <col class="flow-search-col-action">
            </colgroup>
            <thead>
              <tr><th>Obra local</th><th>Situação</th><th>Resultado</th><th>Ação sugerida</th></tr>
            </thead>
            <tbody>
              ${rows.map(row => `
                <tr>
                  <td title="${escapeHtml(row.title)}">${escapeHtml(row.title)}</td>
                  <td><span class="flow-badge ${row.tone}">${escapeHtml(row.status)}</span></td>
                  <td>${escapeHtml(row.result)}</td>
                  <td>${escapeHtml(row.action)}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
          <div class="flow-table-footer">
            <div class="actions">
              <button class="primary-action" type="button" data-flow-run-stage>Buscar candidatos</button>
              <button class="secondary-action" type="button" data-flow-subtab="pendencias">Ver pendências</button>
            </div>
            ${searchPagination(works)}
          </div>
        </div>
      </details>
    </section>
  `;
}

function headingTooltip(label, text) {
  return `<span class="flow-heading-tooltip" tabindex="0" aria-label="${escapeHtml(text)}">${escapeHtml(label)}</span>`;
}

function searchPagination(works) {
  const pagination = works?.pagination || {};
  const page = Number(pagination.page || 1);
  const pages = Number(pagination.pages || 1);
  if (pages <= 1) return "";
  return `<div class="flow-pager">
    <button class="flow-page-link" type="button" ${page <= 1 ? "disabled" : ""} data-flow-works-page="${page - 1}" aria-label="Página anterior">‹</button>
    ${pageButtons(page, pages)}
    <button class="flow-page-link" type="button" ${page >= pages ? "disabled" : ""} data-flow-works-page="${page + 1}" aria-label="Próxima página">›</button>
  </div>`;
}

function pageButtons(page, pages) {
  const start = Math.max(1, Math.min(page - 1, pages - 2));
  const end = Math.min(pages, start + 2);
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
    .map(number => `<button type="button" class="flow-page-link ${number === page ? "active" : ""}" data-flow-works-page="${number}">${number}</button>`)
    .join("");
}

function searchRows(metrics, summary, review, works) {
  const workItems = works?.items || [];
  if (workItems.length) return workItems.map(item => ({
    title: item.localTitle || "Obra sem título",
    status: statusLabel(item.decisionStatus),
    tone: statusTone(item.decisionStatus),
    result: resultLabel(item),
    action: actionLabel(item.nextAction),
  }));
  const items = review?.items || [];
  if (items.length) return items.map(item => ({
    title: item.nome || "Obra sem título",
    status: item.candidates?.length ? "Pendente" : "Crítico",
    tone: item.candidates?.length ? "amb" : "bad",
    result: item.candidates?.length ? `${item.candidates.length} encontrado${item.candidates.length === 1 ? "" : "s"}` : "0 candidatos",
    action: item.candidates?.length ? "Revisar candidatos" : "Informar ID manual",
  }));
  return [
    {
      title: "Obras sem ID",
      status: `${unresolvedCount(metrics)} aguardam`,
      tone: "info",
      result: "Ainda não consultada",
      action: "Pesquisar na API",
    },
    {
      title: "Correspondências pendentes",
      status: `${suggestionCount(metrics, summary)} sugestões`,
      tone: "amb",
      result: "Sugestões disponíveis",
      action: "Revisar candidatos",
    },
    {
      title: "Sem resultado seguro",
      status: `${criticalCount(metrics)} críticas`,
      tone: "bad",
      result: "0 candidatos",
      action: "Normalizar título ou informar ID",
    },
  ];
}

function statusLabel(status) {
  return {
    WITHOUT_ID: "Sem ID",
    READY_TO_SEARCH: "Pronta",
    CANDIDATES_FOUND: "Candidatos",
    PENDING_REVIEW: "Pendente",
    MANUAL_ID_REQUIRED: "Sem resultado",
    ERROR: "Erro",
  }[status] || status || "Pendente";
}

function statusTone(status) {
  if (status === "ERROR" || status === "MANUAL_ID_REQUIRED") return "bad";
  if (status === "CANDIDATES_FOUND" || status === "PENDING_REVIEW") return "amb";
  return "info";
}

function resultLabel(item) {
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
    WITHOUT_ID: "Ainda não consultada",
    READY_TO_SEARCH: "Ainda não consultada",
    CANDIDATES_FOUND: "Disponíveis para revisão",
    PENDING_REVIEW: "Disponíveis para revisão",
    MANUAL_ID_REQUIRED: "0 candidatos",
    ERROR: "Falha na consulta",
  }[item?.decisionStatus] || "Aguardando";
}

function actionLabel(action) {
  return {
    SEARCH_API: "Pesquisar na API",
    NORMALIZE_TITLE: "Normalizar título",
    REVIEW_CANDIDATES: "Revisar candidatos",
    MANUAL_SEARCH: "Informar ID manual",
    RETRY_FAILED: "Tentar novamente",
  }[action] || action || "Pesquisar na API";
}

function metricCard(label, value) {
  return `<article class="flow-metric-card">
    <strong>${escapeHtml(String(value))}</strong>
    <span>${escapeHtml(label)}</span>
  </article>`;
}

function suggestionCount(metrics, summary) {
  return Number(metrics.pending || summary.review || 0);
}

function criticalCount(metrics) {
  return Number(metrics.notFound || metrics.errors || 0);
}

function unresolvedCount(metrics) {
  return Math.max(
    0,
    Number(metrics.catalogWorks || 0) - Number(metrics.alreadyResolved || 0),
  );
}

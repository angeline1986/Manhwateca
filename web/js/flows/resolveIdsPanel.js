import { escapeHtml } from "../utils/html.js";
import { decisionsTab } from "./applyDecisionsPanel.js";
import { pendingTab } from "./pendingReviewPanel.js";

export function renderResolveIdsPanel({
  activeSubtab,
  activeReviewKey,
  showResolvedReview,
  review,
  reviewSearchQuery,
  run,
  selectedDecisions,
  savedReviewKeys,
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
    }) : ""}
    ${activeSubtab === "decisoes" ? decisionsTab(review, selectedDecisions) : ""}
  `;
}

function searchTab(metrics, summary, review, works) {
  const rows = searchRows(metrics, summary, review, works);
  const kpis = works?.kpis || {};
  return `
    <p class="lead">Localize candidatos no MangaUpdates para obras sem identificação.</p>
    <div class="flow-subgrid">
      ${metricCard("Sem ID", kpis.withoutId ?? unresolvedCount(metrics))}
      ${metricCard("Sugestões", kpis.candidatesFound ?? suggestionCount(metrics, summary))}
      ${metricCard("Sem resultado", kpis.noResult ?? criticalCount(metrics))}
      ${metricCard("Erros de API", kpis.apiErrors ?? 0)}
    </div>
    <table class="flow-table">
      <thead>
        <tr><th>Obra local</th><th>Situação</th><th>Ação sugerida</th></tr>
      </thead>
      <tbody>
        ${rows.map(row => `
          <tr>
            <td>${escapeHtml(row.title)}</td>
            <td><span class="flow-badge ${row.tone}">${escapeHtml(row.status)}</span></td>
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
  `;
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
    action: actionLabel(item.nextAction),
  }));
  const items = review?.items || [];
  if (items.length) return items.map(item => ({
    title: item.nome || "Obra sem título",
    status: item.candidates?.length ? "Pendente" : "Crítico",
    tone: item.candidates?.length ? "amb" : "bad",
    action: item.candidates?.length ? "Revisar candidatos" : "Informar ID manual",
  }));
  return [
    {
      title: "Obras sem ID",
      status: `${unresolvedCount(metrics)} aguardam`,
      tone: "info",
      action: "Pesquisar na API",
    },
    {
      title: "Correspondências pendentes",
      status: `${suggestionCount(metrics, summary)} sugestões`,
      tone: "amb",
      action: "Revisar candidatos",
    },
    {
      title: "Sem resultado seguro",
      status: `${criticalCount(metrics)} críticas`,
      tone: "bad",
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

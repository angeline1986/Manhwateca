import { escapeHtml } from "../utils/html.js";

export function renderResolveIdsPanel({ activeSubtab, review, run, works }) {
  const summary = review?.summary || {};
  const metrics = run.results?.resolve_ids?.metrics || {};
  return `
    ${activeSubtab === "buscar" ? searchTab(metrics, summary, review, works) : ""}
    ${activeSubtab === "pendencias" ? pendingTab(review) : ""}
    ${activeSubtab === "decisoes" ? decisionsTab(review) : ""}
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
    <div class="actions">
      <button class="primary-action" type="button" data-flow-run-stage>Buscar candidatos</button>
      <button class="secondary-action" type="button" data-flow-subtab="pendencias">Ver pendências</button>
    </div>
  `;
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

function pendingTab(review) {
  const items = review?.items || [];
  if (!items.length) {
    return '<p class="empty">Nenhuma correspondência pendente para revisar.</p>';
  }
  const first = items[0];
  return `
    <p class="lead">Valide os candidatos encontrados ou informe IDs manualmente.</p>
    <div class="flow-choice-panel">
      <div>
        ${items.slice(0, 5).map(item => `
          <article class="flow-choice">
            <strong>${escapeHtml(item.nome || "")}</strong>
            <span class="flow-badge amb">${item.candidates?.length || 0} candidato(s)</span>
            <p>${escapeHtml(item.candidates?.length ? "Requer validação." : "Sem match automático seguro.")}</p>
          </article>
        `).join("")}
      </div>
      <div class="flow-detail-card">
        <h3>Detalhe da seleção</h3>
        <table class="flow-table compact">
          <thead><tr><th>Candidato</th><th>Score</th><th>ID</th></tr></thead>
          <tbody>
            ${(first.candidates || []).slice(0, 3).map(candidate => `
              <tr>
                <td>${escapeHtml(candidate.titulo || "")}</td>
                <td>${Number(candidate.pontuacao || 0).toFixed(2)}</td>
                <td>${escapeHtml(String(candidate.id || ""))}</td>
              </tr>
            `).join("") || '<tr><td colspan="3">Nenhum candidato disponível.</td></tr>'}
          </tbody>
        </table>
        <input class="flow-manual-input" placeholder="ID manual" type="number" min="1">
      </div>
    </div>
    <div class="actions">
      <button class="primary-action" type="button" data-page="mangaupdates">Abrir revisão completa</button>
      <button class="secondary-action" type="button" data-flow-subtab="decisoes">Aplicar decisões</button>
    </div>
  `;
}

function decisionsTab(review) {
  const count = review?.items?.length || 0;
  return `
    <p class="lead">Grave no banco os IDs revisados e deixe a etapa pronta para metadados.</p>
    <table class="flow-table">
      <thead>
        <tr><th>Fila</th><th>Decisão</th><th>Impacto</th></tr>
      </thead>
      <tbody>
        <tr>
          <td>Correspondências pendentes</td>
          <td><span class="flow-badge amb">${count} pendente(s)</span></td>
          <td>Salva IDs confirmados no banco</td>
        </tr>
      </tbody>
    </table>
    <div class="flow-panel-note">
      ${count
        ? `${count} obra(s) ainda precisam de decisão antes da aplicação final.`
        : "Não há decisões pendentes para aplicar."}
    </div>
    <button class="primary-action" type="button" data-page="mangaupdates">
      Abrir revisão de decisões
    </button>
  `;
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

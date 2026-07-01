import { escapeHtml } from "../utils/html.js";

export function pendingTab(review, selectedDecisions = {}) {
  const items = review?.items || [];
  if (!items.length) return '<p class="empty">Não há correspondências pendentes.</p>';
  return `
    <p class="lead">Escolha o ID correto, informe um ID manual ou deixe para revisar depois.</p>
    <div class="flow-review-list">
      ${items.slice(0, 5).map(item => reviewItem(item, selectedDecisions)).join("")}
    </div>
    <div class="actions">
      <button class="secondary-action" type="button" data-flow-subtab="decisoes">Aplicar decisões</button>
    </div>
  `;
}

export function decisionsTab(review, selectedDecisions = {}) {
  const count = Object.keys(selectedDecisions).length;
  const pending = review?.items?.length || 0;
  return `
    <p class="lead">Aplique no PostgreSQL apenas as decisões já conferidas.</p>
    <table class="flow-table">
      <thead><tr><th>Fila</th><th>Decisão</th><th>Impacto</th></tr></thead>
      <tbody>
        <tr>
          <td>Decisões selecionadas</td>
          <td><span class="flow-badge ${count ? "amb" : "info"}">${count} pronta(s)</span></td>
          <td>Grava IDs confirmados e remove da fila de revisão</td>
        </tr>
        <tr>
          <td>Correspondências pendentes</td>
          <td><span class="flow-badge amb">${pending} pendente(s)</span></td>
          <td>Continuam disponíveis para revisão</td>
        </tr>
      </tbody>
    </table>
    <button class="primary-action" type="button" data-flow-apply-decisions ${count ? "" : "disabled"}>
      Aplicar decisões
    </button>
  `;
}

function reviewItem(item, selectedDecisions) {
  const title = item.localTitle || item.nome || "Obra sem título";
  const key = item.nome_decisao || title;
  const selected = selectedDecisions[key];
  return `
    <article class="flow-review-card">
      <header>
        <div>
          <strong>${escapeHtml(title)}</strong>
          <span>${escapeHtml(reasonLabel(item.reason || item.decisionStatus))}</span>
        </div>
        ${selected ? '<span class="flow-badge info">Selecionada</span>' : ""}
      </header>
      <div class="flow-candidate-grid">
        ${(item.candidates || []).map(candidate => candidateButton(key, candidate, selected)).join("")
          || '<p class="empty">Sem candidato seguro. Informe um ID manual.</p>'}
      </div>
      <div class="flow-manual-row">
        <input type="number" min="1" placeholder="ID manual" data-flow-manual-id="${escapeHtml(key)}">
        <button class="secondary-action" type="button" data-flow-manual-work="${escapeHtml(key)}">Usar ID</button>
      </div>
    </article>
  `;
}

function candidateButton(key, candidate, selected) {
  const id = String(candidate.id || "");
  const active = selected?.ID === Number(id);
  return `
    <button class="flow-candidate ${active ? "selected" : ""}" type="button"
      data-flow-select-id="${escapeHtml(id)}"
      data-flow-work="${escapeHtml(key)}"
      data-flow-title="${escapeHtml(candidate.title || candidate.titulo || "")}">
      <strong>${escapeHtml(candidate.title || candidate.titulo || "Sem título")}</strong>
      <span>${confidenceLabel(candidate.confidence ?? candidate.pontuacao)}</span>
    </button>
  `;
}

function confidenceLabel(value) {
  const number = Number(value || 0);
  return number ? `${Math.round(number * 100)}% de confiança` : "Sem confiança";
}

function reasonLabel(reason) {
  return {
    AMBIGUOUS: "Correspondência ambígua",
    LOW_CONFIDENCE: "Baixa confiança",
    NO_RESULT: "Sem resultado",
    PENDING_REVIEW: "Requer revisão",
    MANUAL_ID_REQUIRED: "ID manual necessário",
  }[reason] || "Requer revisão";
}

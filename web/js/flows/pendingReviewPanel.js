import { escapeHtml } from "../utils/html.js";

export function pendingTab(review, selectedDecisions = {}, activeKey = "") {
  const items = review?.items || [];
  if (!items.length) return '<p class="empty">Não há correspondências pendentes.</p>';
  const selectedItem = items.find(item => itemKey(item) === activeKey) || items[0];
  const activeItemKey = itemKey(selectedItem);
  return `
    <div class="flow-review-workbench">
      <aside class="flow-review-queue" aria-label="Obras pendentes">
        <p>${reviewSummary(items, selectedDecisions)}</p>
        ${items.map(item => queueItem(item, selectedDecisions, itemKey(item) === activeItemKey)).join("")}
      </aside>
      ${decisionPanel(selectedItem, selectedDecisions)}
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

function decisionPanel(item, selectedDecisions) {
  const title = item.localTitle || item.nome || "Obra sem título";
  const key = itemKey(item);
  const selected = selectedDecisions[key];
  const candidates = rankedCandidates(item.candidates || []);
  return `
    <section class="flow-decision-panel">
      <header>
        <span class="eyebrow">Revisão manual</span>
        <h3>${escapeHtml(title)}</h3>
        ${selected ? '<span class="flow-badge info">Decisão marcada</span>' : ""}
      </header>
      <div class="flow-review-alert">${escapeHtml(reasonText(candidates))}</div>
      <h4>Candidatos do MangaUpdates</h4>
      <div class="flow-candidate-grid">
        ${candidates.map((candidate, index) => candidateButton(key, candidate, selected, index)).join("")
          || '<p class="empty">Sem candidato seguro. Informe um ID manual.</p>'}
      </div>
      <div class="flow-manual-row">
        <label>
          <span>ID manual</span>
          <input type="number" min="1" placeholder="Ex.: 98765" data-flow-manual-id="${escapeHtml(key)}">
        </label>
        <button class="secondary-action" type="button" data-flow-manual-work="${escapeHtml(key)}">Usar ID</button>
      </div>
      <footer class="flow-decision-actions">
        <button class="secondary-action" type="button">Ignorar por enquanto</button>
        <button class="secondary-action" type="button">Marcar sem correspondência</button>
        <span>${selected ? `Selecionado: ID ${escapeHtml(String(selected.ID))}` : "Nenhuma decisão selecionada"}</span>
        <button class="primary-action" type="button" data-flow-subtab="decisoes" ${selected ? "" : "disabled"}>
          Salvar decisão
        </button>
      </footer>
    </section>
  `;
}

function queueItem(item, selectedDecisions, active) {
  const title = item.localTitle || item.nome || "Obra sem título";
  const key = itemKey(item);
  const candidates = rankedCandidates(item.candidates || []);
  const marked = Boolean(selectedDecisions[key]);
  return `
    <button class="flow-queue-item ${active ? "active" : ""} ${marked ? "marked" : ""}" type="button" data-flow-review-work="${escapeHtml(key)}">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(reasonLabel(item.reason || item.decisionStatus, candidates.length))} · ${candidates.length}</span>
      ${marked ? "<em>Marcada</em>" : ""}
    </button>
  `;
}

function candidateButton(key, candidate, selected, index) {
  const id = String(candidate.id || "");
  const active = selected?.ID === Number(id);
  const recommended = index === 0;
  const score = confidenceLabel(candidate.confidence ?? candidate.pontuacao);
  return `
    <button class="flow-candidate ${recommended ? "recommended" : ""} ${active ? "selected" : ""}" type="button"
      data-flow-select-id="${escapeHtml(id)}"
      data-flow-work="${escapeHtml(key)}"
      data-flow-title="${escapeHtml(candidate.title || candidate.titulo || "")}">
      <span class="candidate-icon">${recommended ? "☆" : "ID"}</span>
      <span class="candidate-copy">
        ${recommended ? '<em class="candidate-seal">Recomendado</em>' : ""}
        <strong>${escapeHtml(candidate.title || candidate.titulo || "Sem título")}</strong>
        <small>ID: ${escapeHtml(id || "--")} · ${escapeHtml(candidate.tipo || candidate.type || "MangaUpdates")}</small>
      </span>
      <span class="candidate-score">
        <strong>${score}</strong>
        <small>match</small>
        ${active ? '<em class="candidate-selected">Selecionado</em>' : ""}
      </span>
    </button>
  `;
}

function confidenceLabel(value) {
  const number = Number(value || 0);
  return number ? `${Math.round(number * 100)}%` : "--";
}

function rankedCandidates(candidates) {
  const unique = new Map();
  for (const candidate of candidates) {
    const score = Number(candidate.confidence ?? candidate.pontuacao ?? 0);
    if (score <= 0.64) continue;
    const key = String(candidate.id || candidate.title || candidate.titulo || "");
    if (!key) continue;
    if (!unique.has(key) || score > Number(unique.get(key).confidence ?? unique.get(key).pontuacao ?? 0)) {
      unique.set(key, candidate);
    }
  }
  return [...unique.values()]
    .sort((left, right) => Number(right.confidence ?? right.pontuacao ?? 0) - Number(left.confidence ?? left.pontuacao ?? 0))
    .slice(0, 5);
}

function reasonLabel(reason, candidateCount = null) {
  if (candidateCount === 0) return "Sem resultado";
  if (candidateCount === 1) return "Candidato encontrado";
  return {
    AMBIGUOUS: "Correspondência ambígua",
    LOW_CONFIDENCE: "Baixa confiança",
    NO_RESULT: "Sem resultado",
    PENDING_REVIEW: "Requer revisão",
    MANUAL_ID_REQUIRED: "ID manual necessário",
  }[reason] || "Requer revisão";
}

function itemKey(item) {
  return item.queueId || item.nome_decisao || item.localTitle || item.nome || "obra";
}

function reasonText(candidates) {
  if (candidates.length > 1) return `A busca encontrou ${candidates.length} candidatos acima de 64% para comparação.`;
  if (!candidates.length) return "A API não retornou candidato útil acima de 64% para esta obra.";
  return "Revise o candidato encontrado antes de marcar a decisão.";
}

function reviewSummary(items, selectedDecisions) {
  const ready = Object.keys(selectedDecisions).length;
  const noResult = items.filter(item => !rankedCandidates(item.candidates || []).length).length;
  return `${items.length} pendentes · ${noResult} sem resultado · ${ready} prontas para aplicar`;
}

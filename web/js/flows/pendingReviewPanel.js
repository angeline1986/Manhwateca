import { escapeHtml } from "../utils/html.js";

export function pendingTab(review, selectedDecisions = {}, activeKey = "", options = {}) {
  const items = review?.items || [];
  const correction = options.idCorrection || {};
  if (!items.length) return `
    <section class="flow-review-main-card">
      <details class="flow-section-details" open>
        ${reviewMainSummary()}
        <div class="flow-section-body">
          <p class="empty">Não há correspondências pendentes.</p>
        </div>
      </details>
    </section>
    ${confirmedIdCorrectionPanel(correction)}
  `;
  const savedKeys = new Set(options.savedKeys || []);
  const showResolved = Boolean(options.showResolved);
  const searchQuery = options.searchQuery || "";
  const sortedItems = [...items].sort(compareItemsByTitle);
  const filteredItems = sortedItems.filter(item => matchesSearch(item, searchQuery));
  const pendingItems = filteredItems.filter(item => !savedKeys.has(itemKey(item)));
  if (!pendingItems.length && !showResolved && !searchQuery.trim()) {
    return `
      <section class="flow-review-main-card">
        <details class="flow-section-details" open>
          ${reviewMainSummary()}
          <div class="flow-section-body">
            ${reviewCompleted(savedKeys.size)}
          </div>
        </details>
      </section>
      ${confirmedIdCorrectionPanel(correction)}
    `;
  }
  const visibleItems = showResolved ? filteredItems : pendingItems;
  const selectedItem = visibleItems.find(item => itemKey(item) === activeKey) || visibleItems[0];
  const activeItemKey = selectedItem ? itemKey(selectedItem) : "";
  return `
    <section class="flow-review-main-card">
      <details class="flow-section-details" open>
        ${reviewMainSummary()}
        <div class="flow-section-body">
          <div class="flow-review-workbench">
            <aside class="flow-review-queue" aria-label="Obras pendentes">
              <div class="flow-queue-heading">
                <strong>Fila de revisão</strong>
                <span>${pendingItems.length} itens aguardando revisão</span>
              </div>
              <label class="flow-queue-search">
                <span>Filtrar por nome</span>
                <input type="search" placeholder="Filtrar por nome..." data-flow-review-search value="${escapeHtml(searchQuery)}">
              </label>
              <p>${reviewSummary(items, savedKeys)}</p>
              ${visibleItems.length
                ? visibleItems.map(item => queueItem(item, selectedDecisions, itemKey(item) === activeItemKey)).join("")
                : '<p class="empty">Nenhuma pendência encontrada para esse filtro.</p>'}
            </aside>
            ${decisionPanel(selectedItem, selectedDecisions)}
          </div>
        </div>
      </details>
    </section>
    ${confirmedIdCorrectionPanel(correction)}
  `;
}

function reviewMainSummary() {
  return `
    <summary class="flow-section-summary">
      <span class="eyebrow">Jornada operacional</span>
      <h2>Revisar pendências</h2>
      <p>Revise correspondências encontradas, resolva conflitos e prepare decisões para gravação.</p>
    </summary>
  `;
}

function reviewCompleted(count) {
  return `
    <section class="flow-review-completed">
      <span class="eyebrow">Revisão concluída</span>
      <h3>Todas as pendências foram resolvidas.</h3>
      <p>As ${count} decisões estão prontas para aplicação.</p>
      <div>
        <button class="secondary-action" type="button" data-flow-review-again>Revisar novamente</button>
        <button class="primary-action" type="button" data-flow-subtab="decisoes">Aplicar decisões</button>
      </div>
    </section>
  `;
}

function decisionPanel(item, selectedDecisions) {
  if (!item) {
    return `
      <section class="flow-decision-panel">
        <p class="empty">Selecione uma pendência para revisar.</p>
      </section>
    `;
  }
  const title = item.localTitle || item.nome || "Obra sem título";
  const key = itemKey(item);
  const selected = selectedDecisions[key];
  const candidates = rankedCandidates(item.candidates || []);
  const normalizedTitle = item.normalizedTitle || item.searchedTitle || "Não informado";
  const aliases = aliasesText(item);
  return `
    <section class="flow-decision-panel">
      <header>
        <span class="eyebrow">Revisão manual</span>
        <h3>${escapeHtml(title)}</h3>
        ${selected ? '<span class="flow-badge info">Decisão marcada</span>' : ""}
      </header>
      <div class="flow-info-grid">
        <div class="flow-info-card">
          <span>Título normalizado</span>
          <p>${escapeHtml(normalizedTitle)}</p>
        </div>
        <div class="flow-info-card">
          <span>Aliases locais</span>
          <p>${escapeHtml(aliases)}</p>
        </div>
      </div>
      ${conflictNotice(item)}
      <div class="flow-candidate-grid">
        ${candidates.map((candidate, index) => candidateButton(key, title, candidate, selected, index)).join("")
          || '<p class="empty">Sem candidato seguro. Informe um ID manual.</p>'}
      </div>
      <div class="flow-manual-row">
        <label>
          <span>Não é nenhum desses? Informe o ID manual</span>
          <input type="number" min="1" placeholder="Ex.: 98765" data-flow-manual-id="${escapeHtml(key)}">
        </label>
        <button class="secondary-action" type="button"
          data-flow-manual-work="${escapeHtml(key)}"
          data-flow-local-title="${escapeHtml(title)}">Validar ID</button>
      </div>
      <footer class="flow-decision-actions">
        <div>
          <button class="secondary-action" type="button">Ignorar</button>
          <button class="secondary-action" type="button">Sem correspondência</button>
        </div>
        <span>${selected ? `Selecionado: ID ${escapeHtml(String(selected.ID))}` : "Nenhuma decisão selecionada"}</span>
        <button class="primary-action btn" type="button" data-flow-save-review ${selected ? "" : "disabled"}>
          ${boxIcon()}
          Preparar lote
        </button>
      </footer>
    </section>
  `;
}

function confirmedIdCorrectionPanel(state = {}) {
  const preview = state.preview || null;
  const loading = Boolean(state.loading);
  const selectedWork = state.selectedWork || null;
  const candidates = state.candidates || [];
  const pageSize = 5;
  const page = Math.max(1, Number(state.page || 1));
  const pages = Math.max(1, Math.ceil(candidates.length / pageSize));
  const safePage = Math.min(page, pages);
  const visibleCandidates = candidates.slice((safePage - 1) * pageSize, safePage * pageSize);
  return `
    <section class="confirmed-id-correction">
      <details class="flow-section-details" open>
        <summary class="flow-section-summary">
          <span class="eyebrow">Manutenção controlada</span>
          <h2>Corrigir ID confirmado</h2>
          <p>Use quando uma obra já foi vinculada ao ID MangaUpdates errado.</p>
        </summary>
        <div class="flow-section-body">
          <div class="confirmed-id-workbench">
            <aside class="confirmed-id-sidebar" aria-label="Obras confirmadas">
              <div class="flow-queue-heading">
                <strong>Obras confirmadas</strong>
                <span>${candidates.length} obras encontradas</span>
              </div>
              <label class="flow-queue-search confirmed-id-search">
                <span>Buscar obra confirmada</span>
                <input type="search" placeholder="Filtrar por nome..." data-confirmed-id-search value="${escapeHtml(state.search || "")}">
              </label>
              ${state.candidatesError ? `<p class="flow-review-warning">${escapeHtml(state.candidatesError)}</p>` : ""}
              <div class="confirmed-id-candidates">
                ${state.candidatesLoading ? '<p class="empty">Carregando obras...</p>' : confirmedIdCandidates(visibleCandidates, selectedWork)}
              </div>
              ${confirmedIdPager(safePage, pages)}
            </aside>
            <main class="confirmed-id-content">
              <div class="section-label">Obra selecionada</div>
              <h3>${selectedWork ? escapeHtml(selectedWork.title) : "Nenhuma obra selecionada"}</h3>
              <div class="confirmed-id-info-grid">
                <article>
                  <span>ID local</span>
                  <strong>${selectedWork ? `ID ${escapeHtml(String(selectedWork.id))}` : "Não selecionado"}</strong>
                </article>
                <article>
                  <span>ID MangaUpdates atual</span>
                  <strong>${selectedWork ? escapeHtml(String(selectedWork.current_work_code || "--")) : "Não informado"}</strong>
                </article>
              </div>
              <div class="flow-review-warning confirmed-id-warning">
                <strong>Atenção ao alterar o ID</strong>
                <p>A correção troca apenas o vínculo e invalida metadados derivados do ID antigo. A reconstrução deve ser feita depois em Atualizar metadados.</p>
              </div>
              <div class="confirmed-id-manual-row">
                <label>
                  <span>Deseja alterar para um novo ID?</span>
                  <input type="number" min="1" placeholder="Ex.: 56302347523" data-confirmed-id-new value="${escapeHtml(state.newWorkCode || "")}">
                </label>
                <button class="secondary-action" type="button" data-confirmed-id-preview ${loading || !selectedWork ? "disabled" : ""}>
                  ${loading ? "Validando..." : "Validar ID"}
                </button>
              </div>
              ${state.error ? `<p class="flow-review-warning">${escapeHtml(state.error)}</p>` : ""}
              ${preview ? confirmedIdPreview(preview, loading) : ""}
            </main>
          </div>
        </div>
      </details>
    </section>
  `;
}

function confirmedIdPager(page, pages) {
  const nextPage = Math.min(page + 1, pages);
  return `
    <nav class="confirmed-id-pager" aria-label="Paginação de obras confirmadas">
      <button class="flow-page-link" type="button" data-confirmed-id-page-action="prev" ${page <= 1 ? "disabled" : ""} aria-label="Página anterior">‹</button>
      <button class="flow-page-link active" type="button" data-confirmed-id-page-number="${page}">${page}</button>
      <button class="flow-page-link" type="button" data-confirmed-id-page-number="${nextPage}" ${page >= pages ? "hidden" : ""}>${nextPage}</button>
      <button class="flow-page-link" type="button" data-confirmed-id-page-action="next" ${page >= pages ? "disabled" : ""} aria-label="Próxima página">›</button>
    </nav>
  `;
}

function confirmedIdCandidates(candidates, selectedWork) {
  if (!candidates.length) {
    return '<p class="empty">Nenhuma obra com ID confirmado encontrada para esse filtro.</p>';
  }
  return candidates.map(item => {
    const selected = selectedWork && Number(selectedWork.id) === Number(item.id);
    return `
      <button class="confirmed-id-candidate ${selected ? "selected" : ""}" type="button"
        data-confirmed-id-select-work="${escapeHtml(String(item.id))}">
        <strong>${escapeHtml(item.title || "Obra sem título")}</strong>
        <span><i></i>ID vinculado · ${escapeHtml(String(item.id))}</span>
      </button>
    `;
  }).join("");
}

function confirmedIdPreview(preview, loading) {
  const current = preview.current || {};
  const proposed = preview.proposed || {};
  const blockers = preview.blockers || [];
  return `
    <div class="confirmed-id-preview ${preview.can_apply ? "ready" : "blocked"}">
      <div class="confirmed-id-preview-grid">
        <article>
          <span>Vínculo atual</span>
          <strong>${escapeHtml(current.title || "Não validado")}</strong>
          <small>ID ${escapeHtml(preview.work?.current_work_code || current.work_code || "--")}</small>
        </article>
        <article>
          <span>Novo vínculo</span>
          <strong>${escapeHtml(proposed.title || "Não informado")}</strong>
          <small>ID ${escapeHtml(proposed.work_code || "--")}</small>
        </article>
      </div>
      ${blockers.length ? blockers.map(blocker => `
        <p class="flow-review-warning">${escapeHtml(blocker.message || "Correção bloqueada.")}</p>
      `).join("") : `
        <p>Ao aplicar, o sistema trocará apenas o ID e limpará metadados derivados do ID antigo. A reconstrução ficará para Atualizar metadados.</p>
      `}
      <button class="primary-action" type="button" data-confirmed-id-apply ${preview.can_apply && !loading ? "" : "disabled"}>
        Aplicar correção
      </button>
    </div>
  `;
}

function aliasesText(item) {
  const aliases = item.alternativeTitles || item.aliases || item.alias || [];
  if (Array.isArray(aliases) && aliases.length) return aliases.join(", ");
  if (typeof aliases === "string" && aliases.trim()) return aliases;
  return "Não informado";
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
      <small class="flow-queue-tip">${escapeHtml(reasonText(item, candidates))}</small>
    </button>
  `;
}

function candidateButton(key, localTitle, candidate, selected, index) {
  const id = String(candidate.id || "");
  const active = selected?.ID === Number(id);
  const recommended = index === 0;
  const score = confidenceLabel(candidate.confidence ?? candidate.pontuacao);
  return `
    <button class="flow-candidate ${recommended ? "recommended" : ""} ${active ? "selected" : ""}" type="button"
      data-flow-select-id="${escapeHtml(id)}"
      data-flow-work="${escapeHtml(key)}"
      data-flow-local-title="${escapeHtml(localTitle)}"
      data-flow-title="${escapeHtml(candidate.title || candidate.titulo || "")}">
      <span class="candidate-icon">${recommended ? "☆" : "ID"}</span>
      <span class="candidate-copy">
        <strong>${escapeHtml(candidate.title || candidate.titulo || "Sem título")}</strong>
        <small>ID: ${escapeHtml(id || "--")} · ${escapeHtml(candidate.tipo || candidate.type || "MangaUpdates")}</small>
      </span>
      <span class="candidate-score">
        <strong>${score}</strong>
        <small>match</small>
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
  if (reason === "EXTERNAL_ID_ALREADY_ASSIGNED") return "ID já associado";
  if (candidateCount === 0) return "Sem resultado";
  if (candidateCount === 1) return "Candidato encontrado";
  return {
    AMBIGUOUS: "Correspondência ambígua",
    LOW_CONFIDENCE: "Baixa confiança",
    NO_RESULT: "Sem resultado",
    PENDING_REVIEW: "Requer revisão",
    MANUAL_ID_REQUIRED: "ID manual necessário",
    EXTERNAL_ID_ALREADY_ASSIGNED: "ID já associado",
  }[reason] || "Requer revisão";
}

function itemKey(item) {
  return item.queueId || item.nome_decisao || item.localTitle || item.nome || "obra";
}

function reasonText(item, candidates) {
  if (item?.reason === "EXTERNAL_ID_ALREADY_ASSIGNED") {
    return "Este ID já está associado a outra obra.";
  }
  if (candidates.length > 1) return `A busca encontrou ${candidates.length} candidatos acima de 64% para comparação.`;
  if (!candidates.length) return "A API não retornou candidato útil acima de 64% para esta obra.";
  return "Revise o candidato encontrado antes de marcar a decisão.";
}

function reviewSummary(items, savedKeys) {
  const ready = savedKeys.size;
  const noResult = items.filter(item => !rankedCandidates(item.candidates || []).length).length;
  return `${items.length} pendentes · ${noResult} sem resultado · ${ready} prontas para aplicar`;
}

function conflictNotice(item) {
  if (item?.reason !== "EXTERNAL_ID_ALREADY_ASSIGNED") return "";
  const conflict = item.conflict || {};
  const existing = conflict.existingTitle || "outra obra";
  const externalId = conflict.candidateExternalId || "o ID sugerido";
  return `
    <div class="flow-review-warning">
      <strong>Este ID já está associado a outra obra.</strong>
      <p>ID ${escapeHtml(String(externalId))} pertence a ${escapeHtml(existing)}. Revise antes de aplicar qualquer decisão.</p>
    </div>
  `;
}

function compareItemsByTitle(left, right) {
  return itemTitle(left).localeCompare(itemTitle(right), "pt-BR", {
    sensitivity: "base",
  });
}

function itemTitle(item) {
  return item.localTitle || item.nome || item.searchedTitle || item.normalizedTitle || "";
}

function matchesSearch(item, query) {
  const normalizedQuery = normalizeSearch(query);
  if (!normalizedQuery) return true;
  return normalizeSearch(itemTitle(item)).includes(normalizedQuery);
}

function normalizeSearch(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .trim();
}

function boxIcon() {
  return `
    <svg class="btn-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <path d="M3.3 7L12 12l8.7-5" />
      <path d="M12 22V12" />
    </svg>
  `;
}

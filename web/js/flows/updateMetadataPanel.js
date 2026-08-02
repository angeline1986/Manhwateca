import { escapeHtml } from "../utils/html.js";

const FIELDS = [
  "Títulos alternativos",
  "Autores",
  "Gêneros",
  "Status",
  "País",
  "Sinopse",
  "Tags",
  "Capa",
];

export function renderUpdateMetadataPanel(metadata = {}) {
  const works = readyWorks(metadata);
  const selected = 0;
  const pageSize = 5;
  const page = 1;
  const pages = Math.max(1, Math.ceil(works.length / pageSize));
  const totalPendingFields = 0;
  const description = "Selecione as obras que terão dados oficiais atualizados via MangaUpdates.";

  return `
    <section class="metadata-main-card" data-metadata-page="${page}" data-metadata-page-size="${pageSize}">
      <details class="flow-section-details" open>
        <summary class="flow-section-summary">
          <span class="eyebrow">Confirmação</span>
          <h2>${headingTooltip("Atualizar metadados", description)}</h2>
        </summary>
        <div class="flow-section-body metadata-stage-body">
        <header class="metadata-header">
          <div class="metadata-summary-chips">
            <span><b data-metadata-total>${works.length}</b> ${works.length === 1 ? "obra pronta" : "obras prontas"}</span>
            <span data-metadata-selected>${selectedLabel(selected, "selecionada", "selecionadas")}</span>
            <span>IDs confirmados</span>
          </div>
        </header>

      <section class="metadata-selection">
        <div class="metadata-selection-head">
          <label class="metadata-select-all">
            <input type="checkbox" data-metadata-select-all>
            Selecionar todas
          </label>
          <label class="metadata-page-size">
            <span>Itens por página</span>
            <select data-metadata-page-size-select>
              ${[5, 10, 25].map(size => `<option value="${size}" ${size === pageSize ? "selected" : ""}>${size}</option>`).join("")}
            </select>
          </label>
        </div>

        <div class="metadata-list" data-metadata-list>
          ${works.length ? works.map((work, index) => metadataItem(work, index)).join("") : emptyState()}
        </div>
      </section>

        <footer class="metadata-bottom-row">
          <div class="metadata-actions">
            <button class="metadata-button-secondary" type="button" data-flow-subtab="decisoes">Voltar para decisões</button>
            <button class="metadata-button-primary" type="button" data-flow-run-stage data-metadata-run disabled>
              Selecione obras
            </button>
          </div>
          ${metadataPager(page, pages)}
        </footer>
        </div>
      </details>
    </section>
    <section class="metadata-info-card">
        <details class="metadata-info">
          <summary>
            <span>Informações da sincronização</span>
            <span class="metadata-info-arrow metadata-info-arrow-closed" aria-hidden="true">▸</span>
            <span class="metadata-info-arrow metadata-info-arrow-open" aria-hidden="true">▾</span>
          </summary>
          <div class="metadata-info-content">
            <div class="metadata-info-panel">
              <h3>Impacto da sincronização</h3>
              <div class="metadata-impact-grid">
                ${impactMetric("Fonte", "MangaUpdates")}
                ${impactMetric("Campos pendentes", String(totalPendingFields), "metadata-fields-count")}
                ${impactMetric("Não selecionadas", String(works.length), "metadata-not-selected")}
                ${impactMetric("Tempo estimado", estimateTime(selected), "metadata-estimated-time")}
              </div>
            </div>
            <div class="metadata-info-panel">
              <h3>Campos avaliados</h3>
              <div class="metadata-fields-grid">
                ${FIELDS.map(field => `<span class="metadata-field-chip">${escapeHtml(field)}</span>`).join("")}
              </div>
            </div>
          </div>
        </details>
    </section>
  `;
}

function headingTooltip(label, text) {
  return `<span class="flow-heading-tooltip" tabindex="0" aria-label="${escapeHtml(text)}">${escapeHtml(label)}</span>`;
}

function readyWorks(metadata) {
  // A regra agora é: tem que ter ID do MangaUpdates e ter pelo menos um metadado pendente
  return (metadata.items || [])
    .filter(item => item.mangaupdatesId && item.pendingMetadata && item.pendingMetadata.length > 0)
    .slice(0, 25);
}

function metadataItem(work, index) {
  const title = work.localTitle || "Obra sem título";
  const id = work.mangaupdatesId || "sem ID";
  const pending = work.pendingMetadata || [];
  const count = pending.length;
  const itemId = `metadata-item-${index}`;

  return `
    <article class="metadata-item" data-metadata-expandable data-metadata-index="${index}" aria-expanded="false" ${index >= 5 ? "hidden" : ""}>
      <div class="metadata-item-header" role="button" tabindex="0" aria-controls="${itemId}">
        <input class="metadata-item-checkbox" type="checkbox" data-metadata-choice data-metadata-work-id="${escapeHtml(String(work.mangaId || work.id || ""))}" data-metadata-fields="${count}" aria-label="Selecionar ${escapeHtml(title)}">
        <div class="metadata-item-content">
          <strong class="metadata-item-title">${escapeHtml(title)}</strong>
          <span class="metadata-item-meta">ID ${escapeHtml(String(id))} · ${selectedLabel(count, "campo pendente", "campos pendentes")}</span>
        </div>
        <span class="metadata-badge">Pronta</span>
        <span class="metadata-item-arrow" aria-hidden="true">▸</span>
      </div>
      <div class="metadata-item-details" id="${itemId}">
        ${pending.map(field => pendingBlock(field)).join("")}
      </div>
    </article>
  `;
}

function metadataPager(page, pages) {
  const nextPage = Math.min(page + 1, pages);
  return `
    <nav class="metadata-pager" data-metadata-pager aria-label="Paginação de obras">
      <button class="flow-page-link" type="button" data-metadata-page-action="prev" ${page <= 1 ? "disabled" : ""} aria-label="Página anterior">‹</button>
      <button class="flow-page-link active" type="button" data-metadata-page-number="${page}">${page}</button>
      <button class="flow-page-link" type="button" data-metadata-page-number="${nextPage}" ${page >= pages ? "hidden" : ""}>${nextPage}</button>
      <button class="flow-page-link" type="button" data-metadata-page-action="next" ${page >= pages ? "disabled" : ""} aria-label="Próxima página">›</button>
    </nav>
  `;
}

/**
 * Renderiza o bloco de informação de um campo pendente.
 */
function pendingBlock(fieldKey) {
  const mapping = {
    'cover': { label: 'Capa', detail: 'A imagem será buscada no MangaUpdates e salva localmente.' },
    'mangaupdatesUrl': { label: 'URL MangaUpdates', detail: 'O link oficial será gerado com base no ID confirmado.' }
  };

  const info = mapping[fieldKey] || { label: fieldKey, detail: 'Este campo será atualizado com os dados oficiais.' };

  return `
    <section class="metadata-change">
      <strong>${escapeHtml(info.label)}</strong>
      <p class="metadata-change-value metadata-change-next">${escapeHtml(info.detail)}</p>
    </section>
  `;
}

function impactMetric(label, value, attr) {
  const data = attr ? ` data-${attr}` : "";
  return `<div><span>${escapeHtml(label)}</span><b${data}>${escapeHtml(value)}</b></div>`;
}

function emptyState() {
  return `
    <div class="metadata-empty">
      <strong>Nenhuma obra com metadados pendentes encontrada.</strong>
      <span>Obras sem ID confirmado ou que já possuem capa e URL não aparecem aqui.</span>
    </div>
  `;
}

function selectedLabel(count, singular, plural) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function estimateTime(count) {
  if (!count) return "~0s";
  // Estimativa baseada em 1.5s por obra para buscar metadados
  return `~${Math.max(5, count * 2)}s`;
}
